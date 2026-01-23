# app/twilio_handler.py
"""
Flask + Twilio IVR (1-question MVP) + CSV outbound dialer
- Keeps your existing folder structure.
- Runs on port 5050 (avoids macOS port 5000 conflicts).
- Supports Twilio trial "Press any key" by adding a short Gather gate.
- Saves: data/audio, data/transcripts, data/translations, data/english_audio
- Uses your existing pipeline functions:
  - transcribe_audio(audio_path) -> (text, detected_lang)
  - translate_to_english_chunked(text) -> english_text
  - text_to_english_audio(english_text, out_mp3_path) -> saves mp3
"""
from dotenv import load_dotenv
load_dotenv()

import os
import csv
import yaml
import requests
from datetime import datetime
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse, Gather
from twilio.rest import Client


# ---- Import your pipeline functions (must exist in your project) ----
from app.transcribe import transcribe_audio
from app.translate import translate_to_english_chunked
from app.tts import text_to_english_audio


# --------------------------
# Config loader
# --------------------------
def load_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

cfg = load_config()  # keep for IVR params like question_text, max_len, etc.

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM_NUMBER")
PUBLIC_BASE_URL = (os.getenv("PUBLIC_BASE_URL") or "").rstrip("/")

if not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM, PUBLIC_BASE_URL]):
    raise RuntimeError(
        "Missing Twilio env vars. Ensure .env contains: "
        "TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, PUBLIC_BASE_URL"
    )

QUESTION_TEXT = cfg.get("ivr", {}).get("question_text", "Please answer after the beep.")
MAX_LEN = int(cfg.get("ivr", {}).get("max_len_sec", 60))
SILENCE_TIMEOUT = int(cfg.get("ivr", {}).get("silence_timeout_sec", 4))

# Output dirs (your existing structure)
AUDIO_DIR = "data/audio"
TRANSCRIPTS_DIR = "data/transcripts"
TRANSLATIONS_DIR = "data/translations"
EN_AUDIO_DIR = "data/english_audio"

os.makedirs(AUDIO_DIR, exist_ok=True)
os.makedirs(TRANSCRIPTS_DIR, exist_ok=True)
os.makedirs(TRANSLATIONS_DIR, exist_ok=True)
os.makedirs(EN_AUDIO_DIR, exist_ok=True)

# Flask app
app = Flask(__name__)


# --------------------------
# Helpers
# --------------------------
def safe_filename(prefix: str) -> str:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"{prefix}_{ts}"


# --------------------------
# Flask routes for Twilio
# --------------------------
@app.route("/health", methods=["GET"])
def health():
    return "ok", 200


@app.route("/voice", methods=["POST"])
def voice():
    """
    Entry point for Twilio when call connects.
    On trial accounts, Twilio plays a disclaimer and may require "press any key".
    We explicitly do a short Gather to capture a digit and then continue.
    """
    vr = VoiceResponse()

    # Trial-safe gate: ask to press any key to continue (works even if Twilio already asked)
    gather = Gather(
        input="dtmf",
        num_digits=1,
        timeout=8,
        action="/start",
        method="POST"
    )
    gather.say("To begin the survey, please press any key.", voice="alice")
    vr.append(gather)

    # If no key pressed, proceed anyway after a short message
    vr.say("Starting the survey now.", voice="alice")
    vr.redirect("/start", method="POST")
    return str(vr)


@app.route("/start", methods=["POST"])
def start():
    """
    1-question MVP:
    Ask the question and record a voice response.
    """
    vr = VoiceResponse()
    vr.say("Hello. This is a research survey test call.", voice="alice")
    vr.say(QUESTION_TEXT, voice="alice")

    vr.record(
        action="/handle-recording",
        method="POST",
        max_length=MAX_LEN,
        timeout=SILENCE_TIMEOUT,     # stop after silence
        play_beep=True,
        trim="trim-silence"
    )

    vr.say("Thank you. Goodbye.", voice="alice")
    vr.hangup()
    return str(vr)


@app.route("/handle-recording", methods=["POST"])
def handle_recording():
    """
    Twilio posts RecordingUrl here after recording is done.
    We download WAV, then run pipeline:
      audio -> transcript -> translation -> English audio
    """
    vr = VoiceResponse()

    call_sid = request.form.get("CallSid", "unknown_call")
    recording_url = request.form.get("RecordingUrl")  # no extension

    if not recording_url:
        vr.say("No recording received. Goodbye.", voice="alice")
        vr.hangup()
        return str(vr)

    wav_url = recording_url + ".wav"

    base = safe_filename(call_sid)

    audio_path = os.path.join(AUDIO_DIR, base + ".wav")
    transcript_path = os.path.join(TRANSCRIPTS_DIR, base + ".txt")
    translation_path = os.path.join(TRANSLATIONS_DIR, base + ".txt")
    english_audio_path = os.path.join(EN_AUDIO_DIR, base + ".mp3")

    # Download Twilio recording (requires Twilio basic auth)
    r = requests.get(wav_url, auth=(TWILIO_SID, TWILIO_TOKEN), timeout=60)
    r.raise_for_status()

    with open(audio_path, "wb") as f:
        f.write(r.content)

    # ---- Pipeline ----
    text, detected = transcribe_audio(audio_path)

    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(text)

    # Skip translation if Whisper detected English (US testing)
    if (detected or "").lower() == "en":
        english_text = text
    else:
        english_text = translate_to_english_chunked(text)

    with open(translation_path, "w", encoding="utf-8") as f:
        f.write(english_text)

    # Generate English audio from English text
    text_to_english_audio(english_text, english_audio_path)

    vr.say("Your response has been recorded. Goodbye.", voice="alice")
    vr.hangup()
    return str(vr)


# --------------------------
# Outbound calling from CSV
# --------------------------
def call_from_csv(csv_path="data/contacts.csv"):
    """
    Reads contacts.csv and places outbound calls.
    Expected headers: participant_id,phone_e164
    """
    client = Client(TWILIO_SID, TWILIO_TOKEN)

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = (row.get("participant_id") or "").strip()
            to = (row.get("phone_e164") or "").strip()

            if not to:
                print(f"Skipping row (missing phone_e164): {row}")
                continue

            call = client.calls.create(
                to=to,
                from_=TWILIO_FROM,
                url=f"{PUBLIC_BASE_URL}/voice",
                method="POST"
            )
            print(f"Calling {pid or 'UNKNOWN'} -> {to} | CallSid={call.sid}")


if __name__ == "__main__":
    """
    Run server:
      python3 -m app.twilio_handler serve

    Trigger outbound calls:
      python3 -m app.twilio_handler call
    """
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "serve"

    if mode == "call":
        call_from_csv("data/contacts.csv")
    else:
        # serve mode
        app.run(host="0.0.0.0", port=5050, debug=True)