# main.py

from app.transcribe import transcribe_directory
import os

def main():
    audio_dir = "data/audio"
    transcript_dir = "data/transcripts"
    os.makedirs(transcript_dir, exist_ok=True)

    transcribe_directory(audio_dir, transcript_dir)

if __name__ == "__main__":
    main()
