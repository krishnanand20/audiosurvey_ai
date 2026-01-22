# app/translate.py

import os
from googletrans import Translator

translator = Translator()

def is_likely_english(text: str) -> bool:
    """
    Lightweight heuristic to avoid translating English test files.
    We use Google's language detection and treat 'en' as English.
    """
    if not text or not text.strip():
        return True  # empty -> treat as "no translation needed"
    try:
        detected = translator.detect(text[:500]).lang  # only sample first 500 chars
        return detected == "en"
    except Exception:
        # If detection fails, do NOT assume English.
        return False

def translate_to_english(text: str) -> str:
    """
    Translate input text to English (verbatim).
    """
    if not text or not text.strip():
        return ""
    # googletrans: dest='en' for English
    out = translator.translate(text, dest="en")
    return out.text

def translate_directory(transcripts_dir: str, translations_dir: str):
    """
    For each transcript .txt:
    - If it's already English -> copy as-is to translations folder
    - Else translate to English and save
    """
    os.makedirs(translations_dir, exist_ok=True)

    for filename in os.listdir(transcripts_dir):
        if not filename.lower().endswith(".txt"):
            continue

        in_path = os.path.join(transcripts_dir, filename)
        out_path = os.path.join(translations_dir, filename)

        with open(in_path, "r", encoding="utf-8") as f:
            text = f.read()

        if is_likely_english(text):
            # Copy as-is
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Translation skipped (already English): {out_path}")
        else:
            translated = translate_to_english(text)
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(translated)
            print(f"Translated to English: {out_path}")