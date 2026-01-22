import whisper
import os

model = whisper.load_model("base")

def transcribe_audio(file_path):
    print(f"Transcribing: {file_path}")
    result = model.transcribe(
        file_path,
        language="sw",      # Kiswahili
        task="transcribe"   # ensure it transcribes (not translate)
    )
    return result["text"], result.get("language", "unknown")

def transcribe_directory(audio_dir, output_dir):
    for filename in os.listdir(audio_dir):
        if filename.lower().endswith((".wav", ".mp3", ".m4a")):
            file_path = os.path.join(audio_dir, filename)
            text, detected_lang = transcribe_audio(file_path)

            out_path = os.path.join(output_dir, filename.rsplit(".", 1)[0] + ".txt")
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(text)

            print(f"Saved: {out_path} | detected={detected_lang}")