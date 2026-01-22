# main.py

import os
from app.transcribe import transcribe_directory
from app.translate import translate_directory
from app.tts import tts_directory

def main():
    audio_dir = "data/audio"
    transcript_dir = "data/transcripts"
    translations_dir = "data/translations"
    english_audio_dir = "data/english_audio"

    os.makedirs(transcript_dir, exist_ok=True)
    os.makedirs(translations_dir, exist_ok=True)
    os.makedirs(english_audio_dir, exist_ok=True)

    # Phase 1: Transcription
    transcribe_directory(audio_dir, transcript_dir)

    # Phase 2: Translation (skip if already English)
    translate_directory(transcript_dir, translations_dir)

    # Phase 3: English Text -> English Audio (TTS)
    tts_directory(translations_dir, english_audio_dir)

if __name__ == "__main__":
    main()