# app/twilio_handler.py

import os
import csv
import yaml
import requests
from datetime import datetime
from flask import Flask, request
from twilio.twiml.voice_response import VoiceResponse
from twilio.rest import Client

# Import your existing pipeline functions
from app.transcribe import transcribe_audio
from app.translate import translate_to_english_chunked  # adjust if your function name differs
from app.tts import text_to_english_audio               # adjust if your function name differs

# --------------------------
# Config loader
# --------------------------
def load_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

cfg = load_config()

TWILIO_SID = cfg["twilio"]["account_sid"]
TWILIO_TOKEN = cfg["twilio"]["auth_token"]
TWILIO_FROM = cfg["twilio"]["from_number"]
PUBLIC_BASE_URL = cfg["twilio"]["public_base_url"].rstrip("/")

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
# Flask routes for Twilio
# --------------------------
@app.route("/health", methods=["GET"])
def health():
    return "ok", 200


@app.route("/voice", methods=["POST"])
def voice():
    """
    Twilio hits this when call connects (inbound or outbound).
    1-question MVP: Ask one question (English TTS for US testing), record response.
    """
    vr = VoiceResponse()
    vr.say("Hello. This is a research survey test call.", voice="alice")
    vr.say(QUESTION_TEXT, voice="alice")

    vr.record(
        action="/handle-recording",
        method="POST",
        max_length=MAX_LEN,
        timeout=SILENCE_TIMEOUT,
        play_beep=True,
        trim="trim-silence"
    )

    vr.say("Thank you. Goodbye.", voice="alice")
    vr.hangup()
    return str(vr)


@app.route("/handle-recording", methods=["POST"])
def handle_recording():
    """
    Twilio posts RecordingUrl here after the recording is done.
    We download recording WAV, then run pipeline:
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

    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    base = f"{call_sid}_{ts}"

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

    # For US testing: if transcript is English, skip translation
    if detected == "en":
        english_text = text
    else:
        # For production Kiswahili calls: translate Kiswahili -> English
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
    """
    client = Client(TWILIO_SID, TWILIO_TOKEN)

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            pid = row["participant_id"].strip()
            to = row["phone_e164"].strip()

            call = client.calls.create(
                to=to,
                from_=TWILIO_FROM,
                url=f"{PUBLIC_BASE_URL}/voice",
                method="POST"
            )
            print(f"Calling {pid} -> {to} | CallSid={call.sid}")


if __name__ == "__main__":
    # Run Flask locally:
    # python3 app/twilio_handler.py serve
    #
    # Or outbound call:
    # python3 app/twilio_handler.py call
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "serve"

    if mode == "call":
        call_from_csv("data/contacts.csv")
    else:
        # serve mode
        app.run(host="0.0.0.0", port=5000, debug=True)