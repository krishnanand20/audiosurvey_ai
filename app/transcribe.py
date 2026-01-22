# app/transcribe.py

import whisper
import os

model = whisper.load_model("base")  # or 'small' or 'medium' depending on performance needs

def transcribe_audio(file_path):
    print(f"Transcribing: {file_path}")
    result = model.transcribe(file_path, language="sw")
    return result["text"]

def transcribe_directory(audio_dir, output_dir):
    for filename in os.listdir(audio_dir):
        if filename.endswith(".wav") or filename.endswith(".mp3"):
            file_path = os.path.join(audio_dir, filename)
            text = transcribe_audio(file_path)

            output_path = os.path.join(output_dir, filename.rsplit(".", 1)[0] + ".txt")
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(text)
            print(f"Saved: {output_path}")
