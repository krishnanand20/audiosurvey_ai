import logging
import os
import subprocess
import warnings
import wave
from pathlib import Path
from typing import Callable, Dict, Optional

import numpy as np
import torch
import yaml


PROGRESS_CB = Optional[Callable[[int, str], None]]
DEFAULT_CONFIG = {
    "enabled": True,
    "backend": "deepfilternet",
    "processed_dir": "data/audio_processed",
    "temp_dir": "data/audio_processed/tmp",
    "output_sample_rate": 16000,
    "model_sample_rate": 48000,
    "channel_mode": "mixdown",
    "caller_channel": 0,
    "keep_intermediate_files": False,
}

_DF_MODEL = None
_DF_STATE = None


def _load_config(path: str = "config.yaml") -> Dict[str, object]:
    cfg = {}
    try:
        with open(path, "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
    except FileNotFoundError:
        cfg = {}
    except Exception:
        cfg = {}
    user_cfg = (cfg.get("audio_processing") or {}) if isinstance(cfg, dict) else {}
    merged = dict(DEFAULT_CONFIG)
    if isinstance(user_cfg, dict):
        merged.update({k: v for k, v in user_cfg.items() if v is not None})
    return merged


def _run(cmd: list[str]) -> None:
    proc = subprocess.run(cmd, capture_output=True, text=True)
    if proc.returncode != 0:
        raise RuntimeError(proc.stderr.strip() or proc.stdout.strip() or "command failed")


def _prepare_for_model(
    src_path: str,
    prep_path: str,
    sample_rate: int,
    channel_mode: str,
    caller_channel: int,
) -> None:
    cmd = [
        "ffmpeg",
        "-y",
        "-i",
        src_path,
    ]

    if str(channel_mode).lower() == "channel":
        cmd.extend(
            [
                "-af",
                f"pan=mono|c0=c{max(0, int(caller_channel))}",
                "-ac",
                "1",
            ]
        )
    else:
        cmd.extend(["-ac", "1"])

    cmd.extend(
        [
            "-ar",
            str(sample_rate),
            "-c:a",
            "pcm_s16le",
            prep_path,
        ]
    )
    _run(cmd)


def _read_pcm16_wave(path: str) -> torch.Tensor:
    with wave.open(path, "rb") as wf:
        channels = wf.getnchannels()
        sample_width = wf.getsampwidth()
        if sample_width != 2:
            raise RuntimeError(f"Unsupported sample width for denoise input: {sample_width}")
        frames = wf.readframes(wf.getnframes())

    arr = np.frombuffer(frames, dtype=np.int16).astype(np.float32) / 32768.0
    if channels > 1:
        arr = arr.reshape(-1, channels).mean(axis=1)
    return torch.from_numpy(arr).unsqueeze(0)


def _write_pcm16_wave(path: str, audio: torch.Tensor, sample_rate: int) -> None:
    pcm = audio.detach().cpu().squeeze(0).clamp(-1.0, 1.0).numpy()
    pcm = (pcm * 32767.0).astype(np.int16)
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with wave.open(path, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(pcm.tobytes())


def _load_df_model():
    global _DF_MODEL
    global _DF_STATE

    if _DF_MODEL is not None and _DF_STATE is not None:
        return _DF_MODEL, _DF_STATE

    for name in ("torio", "torio._extension", "torio._extension.utils", "torchaudio"):
        logging.getLogger(name).setLevel(logging.ERROR)

    warnings.filterwarnings("ignore", module="df.io")
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        from df import utils as df_utils  # type: ignore
        from df.enhance import enhance, init_df  # type: ignore

    df_utils.get_git_root = lambda: None
    model, df_state, _ = init_df(log_level="ERROR")
    _DF_MODEL = (enhance, model)
    _DF_STATE = df_state
    return _DF_MODEL, _DF_STATE


def _enhance_with_deepfilternet(input_path: str, output_path: str) -> None:
    (enhance_fn, model), df_state = _load_df_model()
    audio = _read_pcm16_wave(input_path)
    enhanced = enhance_fn(model, df_state, audio)
    _write_pcm16_wave(output_path, enhanced, df_state.sr())


def preprocess_recording(
    src_path: str,
    progress_cb: PROGRESS_CB = None,
) -> str:
    cfg = _load_config()
    if not bool(cfg.get("enabled", True)):
        return src_path

    backend = str(cfg.get("backend", "deepfilternet")).strip().lower()
    if backend != "deepfilternet":
        raise RuntimeError(f"Unsupported audio_processing.backend: {backend}")

    processed_dir = str(cfg.get("processed_dir", DEFAULT_CONFIG["processed_dir"]))
    temp_dir = str(cfg.get("temp_dir", DEFAULT_CONFIG["temp_dir"]))
    model_sr = int(cfg.get("model_sample_rate", DEFAULT_CONFIG["model_sample_rate"]))
    output_sr = int(cfg.get("output_sample_rate", DEFAULT_CONFIG["output_sample_rate"]))
    channel_mode = str(cfg.get("channel_mode", DEFAULT_CONFIG["channel_mode"])).strip().lower()
    caller_channel = int(cfg.get("caller_channel", DEFAULT_CONFIG["caller_channel"]))
    keep_intermediate = bool(
        cfg.get("keep_intermediate_files", DEFAULT_CONFIG["keep_intermediate_files"])
    )

    os.makedirs(processed_dir, exist_ok=True)
    os.makedirs(temp_dir, exist_ok=True)

    stem = Path(src_path).stem
    prepared_path = os.path.join(temp_dir, f"{stem}_df_input.wav")
    enhanced_path = os.path.join(temp_dir, f"{stem}_df_enhanced.wav")
    final_path = os.path.join(processed_dir, f"{stem}.wav")

    if progress_cb:
        progress_cb(25, "Preparing audio for denoise")
    _prepare_for_model(src_path, prepared_path, model_sr, channel_mode, caller_channel)

    if progress_cb:
        progress_cb(60, "Removing background noise")
    _enhance_with_deepfilternet(prepared_path, enhanced_path)

    if progress_cb:
        progress_cb(75, "Resampling cleaned audio for Whisper")
    _run(
        [
            "ffmpeg",
            "-y",
            "-i",
            enhanced_path,
            "-ac",
            "1",
            "-ar",
            str(output_sr),
            "-c:a",
            "pcm_s16le",
            final_path,
        ]
    )

    if not keep_intermediate:
        for path in (prepared_path, enhanced_path):
            try:
                os.remove(path)
            except FileNotFoundError:
                pass

    return final_path
