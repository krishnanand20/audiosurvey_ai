import os
import time
from datetime import datetime

from app.state import load_participants, save_participants, mark_completed
from app.transcribe import transcribe_audio
from app.translate import translate_to_english_chunked
from app.tts import text_to_english_audio


TRANSCRIPTS_DIR = "data/transcripts"
TRANSLATIONS_DIR = "data/translations"
EN_AUDIO_DIR = "data/english_audio"

os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
os.makedirs(TRANSLATIONS_DIR, exist_ok=True)
os.makedirs(EN_AUDIO_DIR, exist_ok=True)


def log(msg):
    print(f"[BackgroundWorker] {msg}")


def process_pending_recordings():
    """
    This runs continuously and processes recordings
    that webhook marked as 'pending'
    """

    while True:
        state = load_participants()

        for pid, p in state.items():
            if p.get("processing_status") != "pending":
                continue

            audio_path = p.get("audio_path")
            if not audio_path or not os.path.exists(audio_path):
                continue

            try:
                log(f"Processing participant {pid}")

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

                # -------------------------
                # 1️⃣ Whisper
                # -------------------------
                text, detected = transcribe_audio(audio_path)

                with open(transcript_path, "w", encoding="utf-8") as f:
                    f.write(text)

                # -------------------------
                # 2️⃣ Translation
                # -------------------------
                if (detected or "").lower() == "en":
                    english_text = text
                else:
                    english_text = translate_to_english_chunked(text)

                with open(translation_path, "w", encoding="utf-8") as f:
                    f.write(english_text)

                # -------------------------
                # 3️⃣ English TTS
                # -------------------------
                text_to_english_audio(english_text, english_audio_path)

                # -------------------------
                # Mark Completed
                # -------------------------
                outputs = {
                    "audio_path": audio_path,
                    "transcript_path": transcript_path,
                    "translation_path": translation_path,
                    "english_audio_path": english_audio_path,
                }

                mark_completed(state, pid, p.get("recording_url"), outputs)
                state[pid]["processing_status"] = "completed"
                save_participants(state)

                log(f"Finished participant {pid}")

            except Exception as e:
                log(f"ERROR processing {pid}: {e}")
                state[pid]["processing_status"] = "failed"
                save_participants(state)

        time.sleep(5)