# app/translate.py

import os
import json
import time
import re
from googletrans import Translator

translator = Translator()
MAX_CHARS = 3000  # safe chunk size for googletrans scraping


def _split_text(text: str, max_chars: int = MAX_CHARS):
    """
    Split text into chunks <= max_chars, trying to split on sentence boundaries.
    """
    text = (text or "").strip()
    if len(text) <= max_chars:
        return [text] if text else [""]

    sentences = re.split(r'(?<=[.!?])\s+', text)
    chunks, current = [], ""

    for s in sentences:
        if not s:
            continue

        # Hard split if a single sentence is too long
        if len(s) > max_chars:
            if current:
                chunks.append(current.strip())
                current = ""
            for i in range(0, len(s), max_chars):
                part = s[i:i + max_chars].strip()
                if part:
                    chunks.append(part)
            continue

        if len(current) + len(s) + 1 <= max_chars:
            current += (" " if current else "") + s
        else:
            chunks.append(current.strip())
            current = s

    if current.strip():
        chunks.append(current.strip())

    return chunks


def translate_to_english_chunked(text: str, retries: int = 3, sleep_sec: float = 1.5) -> str:
    """
    Translate long text by chunking + retries.
    Returns full translated text or a marked fallback if chunks fail.
    """
    if not text or not text.strip():
        return ""

    chunks = _split_text(text)
    out_chunks = []

    for idx, chunk in enumerate(chunks, start=1):
        last_err = None

        for attempt in range(1, retries + 1):
            try:
                res = translator.translate(chunk, src="sw", dest="en")
                if res is None or res.text is None:
                    raise RuntimeError("googletrans returned None")
                out_chunks.append(res.text)
                break
            except Exception as e:
                last_err = e
                time.sleep(sleep_sec)

        # If all retries fail for this chunk
        if len(out_chunks) < idx:
            out_chunks.append(
                f"[TRANSLATION_FAILED_CHUNK {idx}/{len(chunks)}]\n{chunk}\n\n[ERROR]\n{repr(last_err)}\n"
            )

    return "\n".join(out_chunks)


def translate_directory(transcripts_dir: str, translations_dir: str):
    """
    For each transcript .txt:
    - If Whisper detected English -> copy as-is
    - Else translate (chunked) Kiswahili -> English
    """
    os.makedirs(translations_dir, exist_ok=True)

    meta_path = os.path.join(transcripts_dir, "_lang_map.json")
    lang_map = {}
    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as f:
            lang_map = json.load(f)

    for filename in os.listdir(transcripts_dir):
        if not filename.lower().endswith(".txt"):
            continue

        stem = filename.rsplit(".", 1)[0]
        detected_lang = lang_map.get(stem, "unknown")

        in_path = os.path.join(transcripts_dir, filename)
        out_path = os.path.join(translations_dir, filename)

        with open(in_path, "r", encoding="utf-8") as f:
            text = f.read()

        # Skip translation if Whisper says it's English
        if detected_lang == "en":
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Translation skipped (Whisper detected English): {out_path}")
            continue

        translated = translate_to_english_chunked(text)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(translated)

        if "TRANSLATION_FAILED_CHUNK" in translated:
            print(f"Translation partially failed (saved with markers): {out_path} | detected={detected_lang}")
        else:
            print(f"Translated to English: {out_path} | detected={detected_lang}")