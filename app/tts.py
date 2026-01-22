# app/tts.py

import os
from gtts import gTTS

def text_to_english_audio(text: str, out_path: str):
    """
    Convert English text to English MP3 audio.
    """
    text = (text or "").strip()
    if not text:
        # Create an empty placeholder file name logic (skip silently)
        return False

    tts = gTTS(text=text, lang="en")
    tts.save(out_path)
    return True


def tts_directory(translations_dir: str, english_audio_dir: str):
    """
    For each translated English .txt file:
    generate an English MP3 file with the same base name.
    """
    os.makedirs(english_audio_dir, exist_ok=True)

    for filename in os.listdir(translations_dir):
        if not filename.lower().endswith(".txt"):
            continue

        in_path = os.path.join(translations_dir, filename)
        stem = filename.rsplit(".", 1)[0]
        out_path = os.path.join(english_audio_dir, stem + ".mp3")

        with open(in_path, "r", encoding="utf-8") as f:
            text = f.read()

        # If translation failed and file contains markers, skip audio to avoid speaking errors
        if "TRANSLATION_FAILED" in text:
            print(f"Skipped TTS (translation failed markers found): {filename}")
            continue

        ok = text_to_english_audio(text, out_path)
        if ok:
            print(f"English audio saved: {out_path}")
        else:
            print(f"Skipped TTS (empty text): {filename}")