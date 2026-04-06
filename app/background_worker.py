import os
import sys
import time
from datetime import datetime

from app.audio_preprocess import preprocess_recording
from app.state import load_participants, save_participants, mark_completed
from app.transcribe import transcribe_audio
from app.translate import translate_to_english_chunked
from app.tts import text_to_english_audio
from app.logger import logger
from app.runtime_status import mark_worker_started, mark_worker_heartbeat


TRANSCRIPTS_DIR = "data/transcripts"
TRANSLATIONS_DIR = "data/translations"
EN_AUDIO_DIR = "data/english_audio"

os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
os.makedirs(TRANSLATIONS_DIR, exist_ok=True)
os.makedirs(EN_AUDIO_DIR, exist_ok=True)


def log(msg):
    mark_worker_heartbeat()
    if getattr(log, "_progress_active", False):
        sys.stdout.write("\n")
        sys.stdout.flush()
        log._progress_active = False
    print(f"[BackgroundWorker] {msg}")


def log_progress(participant_id: str, percent: int, stage: str) -> None:
    mark_worker_heartbeat()
    pct = max(0, min(100, int(percent)))
    filled = max(0, min(20, round(pct / 5)))
    bar = "#" * filled + "-" * (20 - filled)
    line = f"[BackgroundWorker] participant={participant_id} | [{bar}] {pct:>3}% | {stage}"

    sys.stdout.write("\r" + line.ljust(140))
    sys.stdout.flush()

    if pct >= 100:
        sys.stdout.write("\n")
        sys.stdout.flush()
        log._progress_active = False
    else:
        log._progress_active = True


def log_success(participant_id: str) -> None:
    log(f"SUCCESS participant={participant_id} | cleaned audio, transcript, translation, and English audio saved")


def process_pending_recordings():
    """
    This runs continuously and processes recordings
    that webhook marked as 'pending'
    """

    mark_worker_started()
    while True:
        mark_worker_heartbeat()
        state = load_participants()

        for pid, p in state.items():
            if p.get("processing_status") != "pending":
                continue

            audio_path = p.get("audio_path")
            if not audio_path or not os.path.exists(audio_path):
                continue

            try:
                mark_worker_heartbeat()
                # Mark as processing
                state[pid]["processing_status"] = "processing"
                save_participants(state)

                base = os.path.splitext(os.path.basename(audio_path))[0]

                transcript_path = os.path.join(
                    TRANSCRIPTS_DIR, base + ".txt"
                )
                translation_path = os.path.join(
                    TRANSLATIONS_DIR, base + ".txt"
                )
                english_audio_path = os.path.join(
                    EN_AUDIO_DIR, base + ".mp3"
                )
                processed_audio_path = audio_path

                log_progress(pid, 10, "Starting background processing")
                try:
                    processed_audio_path = preprocess_recording(
                        audio_path,
                        progress_cb=lambda pct, stage: log_progress(pid, pct, stage),
                    )
                except Exception as e:
                    log(f"Preprocess skipped for participant {pid}: {e}")
                    processed_audio_path = audio_path

                # -------------------------
                # 1️⃣ Whisper
                # -------------------------
                log_progress(pid, 85, "Transcribing cleaned audio")
                text, detected = transcribe_audio(processed_audio_path)

                with open(transcript_path, "w", encoding="utf-8") as f:
                    f.write(text)

                # -------------------------
                # 2️⃣ Translation
                # -------------------------
                log_progress(pid, 93, "Translating transcript")
                if (detected or "").lower() == "en":
                    english_text = text
                else:
                    english_text = translate_to_english_chunked(text)

                with open(translation_path, "w", encoding="utf-8") as f:
                    f.write(english_text)

                # -------------------------
                # 3️⃣ English TTS
                # -------------------------
                log_progress(pid, 97, "Generating English audio")
                text_to_english_audio(english_text, english_audio_path)

                # -------------------------
                # Mark Completed
                # -------------------------
                outputs = {
                    "audio_path": audio_path,
                    "processed_audio_path": processed_audio_path,
                    "transcript_path": transcript_path,
                    "translation_path": translation_path,
                    "english_audio_path": english_audio_path,
                }

                mark_completed(state, pid, p.get("recording_url"), outputs)
                state[pid]["processing_status"] = "completed"
                save_participants(state)
                mark_worker_heartbeat()

                log_progress(pid, 100, "Processing complete")
                log_success(pid)

            except Exception as e:
                log(f"ERROR processing {pid}: {e}")
                state[pid]["processing_status"] = "failed"
                save_participants(state)

        mark_worker_heartbeat()
        time.sleep(5)
