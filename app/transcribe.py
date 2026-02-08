# app/transcribe.py

import whisper
import os
import json

model = whisper.load_model("large-v3")

def transcribe_audio(file_path):
    result = model.transcribe(
        file_path,
        language="sw",
        task="transcribe",
        fp16=False,                      # CPU safe
        verbose=False,
        condition_on_previous_text=False, # reduces drift / early cut issues
        temperature=0.0                  # more stable decoding
    )
    text = result["text"]
    detected_lang = result.get("language", "unknown")
    return text, detected_lang

def transcribe_directory(audio_dir, output_dir):
    os.makedirs(output_dir, exist_ok=True)

    lang_map = {}  # filename_without_ext -> detected_lang

    for filename in os.listdir(audio_dir):
        if filename.lower().endswith((".wav", ".mp3", ".m4a")):
            file_path = os.path.join(audio_dir, filename)
            text, detected_lang = transcribe_audio(file_path)

            stem = filename.rsplit(".", 1)[0]
            out_path = os.path.join(output_dir, stem + ".txt")

            with open(out_path, "w", encoding="utf-8") as f:
                f.write(text)

            lang_map[stem] = detected_lang
            print(f"Saved: {out_path} | detected={detected_lang}")

    # Save language metadata for translation step
    meta_path = os.path.join(output_dir, "_lang_map.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(lang_map, f, ensure_ascii=False, indent=2)

    print(f"Saved language map: {meta_path}")