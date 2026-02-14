import os
import hashlib
import azure.cognitiveservices.speech as speechsdk

CACHE_DIR = "data/tts_cache"
os.makedirs(CACHE_DIR, exist_ok=True)

AZURE_SPEECH_KEY = os.getenv("AZURE_SPEECH_KEY", "")
AZURE_SPEECH_REGION = os.getenv("AZURE_SPEECH_REGION", "")
AZURE_TTS_VOICE = os.getenv("AZURE_TTS_VOICE", "sw-KE-ZuriNeural")
AZURE_TTS_FORMAT = os.getenv("AZURE_TTS_FORMAT", "audio-16khz-128kbitrate-mono-mp3")

if not AZURE_SPEECH_KEY or not AZURE_SPEECH_REGION:
    raise RuntimeError("Missing AZURE_SPEECH_KEY / AZURE_SPEECH_REGION in .env")

def _hash_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:24]

def synthesize_to_mp3(text: str) -> str:
    """
    Returns local filepath to an MP3.
    Caches by text hash so you don't regenerate every time.
    """
    text = (text or "").strip()
    if not text:
        raise ValueError("Empty text for TTS")

    key = _hash_text(f"{AZURE_TTS_VOICE}|{AZURE_TTS_FORMAT}|{text}")
    out_path = os.path.join(CACHE_DIR, f"{key}.mp3")
    if os.path.exists(out_path) and os.path.getsize(out_path) > 1000:
        return out_path

    speech_config = speechsdk.SpeechConfig(subscription=AZURE_SPEECH_KEY, region=AZURE_SPEECH_REGION)
    speech_config.speech_synthesis_voice_name = AZURE_TTS_VOICE
    speech_config.set_speech_synthesis_output_format(
        getattr(speechsdk.SpeechSynthesisOutputFormat, "Audio16Khz128KBitRateMonoMp3")
        if AZURE_TTS_FORMAT == "audio-16khz-128kbitrate-mono-mp3"
        else speechsdk.SpeechSynthesisOutputFormat.Riff16Khz16BitMonoPcm
    )

    audio_config = speechsdk.audio.AudioOutputConfig(filename=out_path)
    synthesizer = speechsdk.SpeechSynthesizer(speech_config=speech_config, audio_config=audio_config)

    result = synthesizer.speak_text_async(text).get()
    if result.reason != speechsdk.ResultReason.SynthesizingAudioCompleted:
        raise RuntimeError(f"Azure TTS failed: {result.reason}")

    return out_path