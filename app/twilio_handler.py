# app/twilio_handler.py

from dotenv import load_dotenv
load_dotenv()

import os
import csv
import yaml
import requests
from datetime import datetime
from flask import Flask, request, Response
from twilio.rest import Client

from app.state import reset_state

from app.state import (
    load_participants,
    save_participants,
    upsert_participant,
    can_call,
    mark_call_started,
    mark_completed,
    log_call_event,
    mark_call_result,
    mark_engaged,         
)

from app.transcribe import transcribe_audio
from app.translate import translate_to_english_chunked
from app.tts import text_to_english_audio


# --------------------------
# Config + env
# --------------------------
def load_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)

cfg = load_config()

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM_NUMBER")
PUBLIC_BASE_URL = (os.getenv("PUBLIC_BASE_URL") or "").rstrip("/")

if not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM, PUBLIC_BASE_URL]):
    raise RuntimeError(
        "Missing Twilio env vars in .env. Need: "
        "TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, PUBLIC_BASE_URL"
    )

GATHER_TIMEOUT = int(cfg.get("ivr", {}).get("gather_timeout_sec", 6))
SPEECH_TIMEOUT = cfg.get("ivr", {}).get("speech_timeout", "auto")
QUESTIONS_FILE = cfg.get("ivr", {}).get("questions_file", "data/questions.txt")

with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
    QUESTIONS = [q.strip() for q in f.readlines() if q.strip()]

if not QUESTIONS:
    raise RuntimeError("No questions found in questions file")

AUDIO_DIR = "data/audio"
TRANSCRIPTS_DIR = "data/transcripts"
TRANSLATIONS_DIR = "data/translations"
EN_AUDIO_DIR = "data/english_audio"

for d in [AUDIO_DIR, TRANSCRIPTS_DIR, TRANSLATIONS_DIR, EN_AUDIO_DIR]:
    os.makedirs(d, exist_ok=True)

app = Flask(__name__)


# --------------------------
# Helpers
# --------------------------
def twiml(xml: str) -> Response:
    return Response(xml, mimetype="text/xml")


def safe_base(call_sid: str) -> str:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"{call_sid}_{ts}"


def xml_escape(s: str) -> str:
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def is_inbound_call() -> bool:
    direction = (request.form.get("Direction") or "").lower()
    return direction.startswith("inbound")


def looks_like_real_speech(s: str) -> bool:
    """
    Twilio may send "No." or blank SpeechResult.
    Treat very short/empty or "no" as not engaged.
    """
    if not s:
        return False
    t = s.strip().lower()
    if t in {"no", "no.", "nah", "none"}:
        return False
    # A small threshold to avoid marking engaged on single filler word
    return len(t.split()) >= 2


def find_participant_by_callsid(state: dict, call_sid: str):
    for pid, p in state.items():
        if p.get("last_call_sid") == call_sid:
            return pid, p
    return None, None


# --------------------------
# Routes
# --------------------------
@app.route("/health", methods=["GET"])
def health():
    return "ok", 200


@app.route("/voice", methods=["POST"])
def voice():
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather input="dtmf" numDigits="1" timeout="8" action="{PUBLIC_BASE_URL}/start" method="POST">
    <Say voice="alice">To begin the survey, please press any key.</Say>
  </Gather>
  <Say voice="alice">Starting the survey.</Say>
  <Redirect method="POST">{PUBLIC_BASE_URL}/start</Redirect>
</Response>"""
    return twiml(xml)


@app.route("/start", methods=["POST"])
def start():
    q1 = xml_escape(QUESTIONS[0])

    start_record_block = ""
    if is_inbound_call():
        start_record_block = f"""
  <Start>
    <Record recordingStatusCallback="{PUBLIC_BASE_URL}/recording-done"
            recordingStatusCallbackMethod="POST"
            recordingStatusCallbackEvent="completed"
            trim="do-not-trim" />
  </Start>"""

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
{start_record_block}

  <Say voice="alice">Hello. This is a research survey call.</Say>
  <Say voice="alice">Please answer each question after it is spoken.</Say>

  <Gather input="speech" timeout="{GATHER_TIMEOUT}" speechTimeout="{SPEECH_TIMEOUT}"
          action="{PUBLIC_BASE_URL}/next?q=1" method="POST">
    <Say voice="alice">{q1}</Say>
  </Gather>

  <Redirect method="POST">{PUBLIC_BASE_URL}/next?q=1</Redirect>
</Response>"""
    return twiml(xml)


@app.route("/next", methods=["POST"])
def next_question():
    """
    Moves through questions.
    ✅ Engagement tracking: if SpeechResult contains real speech, mark engaged=True.
    """
    q = int(request.args.get("q", "0"))

    # ---- Engagement tracking ----
    call_sid = request.form.get("CallSid", "")
    speech = (request.form.get("SpeechResult") or "").strip()

    if call_sid and looks_like_real_speech(speech):
        state = load_participants()
        pid, _ = find_participant_by_callsid(state, call_sid)
        if pid:
            mark_engaged(state, pid)
            save_participants(state)
            print(f"ENGAGED=True for participant {pid} | CallSid={call_sid}")

    # ---- End survey ----
    if q >= len(QUESTIONS):
        stop_block = ""
        if is_inbound_call():
            stop_block = "  <Stop><Record/></Stop>\n"

        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
{stop_block}  <Say voice="alice">Thank you. The survey is complete. Goodbye.</Say>
  <Hangup/>
</Response>"""
        return twiml(xml)

    # ---- Ask next question ----
    question = xml_escape(QUESTIONS[q])
    next_q = q + 1

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather input="speech" timeout="{GATHER_TIMEOUT}" speechTimeout="{SPEECH_TIMEOUT}"
          action="{PUBLIC_BASE_URL}/next?q={next_q}" method="POST">
    <Say voice="alice">{question}</Say>
  </Gather>

  <Redirect method="POST">{PUBLIC_BASE_URL}/next?q={next_q}</Redirect>
</Response>"""
    return twiml(xml)


@app.route("/call-status", methods=["POST"])
def call_status():
    """
    Twilio status callback for outbound calls.
    ✅ We do NOT trust "completed" alone as survey completion.
    We use 'engaged' to decide final completion.
    """
    call_sid = request.form.get("CallSid", "")
    call_status = (request.form.get("CallStatus") or "").lower().strip()

    print("CALL STATUS HIT")
    print("CallSid:", call_sid)
    print("CallStatus:", call_status)

    state = load_participants()
    pid, p = find_participant_by_callsid(state, call_sid)

    if not pid:
        return ("ok", 200)

    # Store last_call_status + adjust retry state
    mark_call_result(state, pid, call_status)

    # ✅ If Twilio says completed but participant never spoke, keep them pending for retry
    engaged = bool(p.get("engaged", False)) if p else False
    if call_status == "completed" and not engaged:
        state[pid]["status"] = "pending"

    save_participants(state)
    return ("ok", 200)


@app.route("/recording-done", methods=["POST"])
def recording_done():
    """
    Called when recording is ready.
    ✅ Only mark 'completed' if participant was engaged AND transcript is non-trivial.
    """
    print("RECORDING DONE HIT")

    call_sid = request.form.get("CallSid", "unknown_call")
    recording_url = request.form.get("RecordingUrl")
    rec_status = request.form.get("RecordingStatus")
    direction = request.form.get("Direction") or ""

    print("CallSid:", call_sid)
    print("RecordingUrl:", recording_url)
    print("RecordingStatus:", rec_status)
    print("Direction:", direction)

    status = (rec_status or "").lower()
    if status and status != "completed":
        return ("ok", 200)

    if not recording_url:
        return ("no recording", 400)

    # ---- Map call -> participant ----
    state = load_participants()
    participant_id, p = find_participant_by_callsid(state, call_sid)
    phone_e164 = p.get("phone_e164") if p else None
    last_call_status = (p.get("last_call_status") or "").lower() if p else ""
    engaged = bool(p.get("engaged", False)) if p else False

    # If we know call outcome was failure, ignore recording for completion
    if participant_id and last_call_status in {"no-answer", "busy", "failed", "canceled"}:
        print(f"Not processing completion: call_status={last_call_status} for participant {participant_id}")
        return ("ok", 200)

    # If participant never spoke, do NOT process as completed
    if participant_id and not engaged:
        print(f"Not marking completed: engaged=False for participant {participant_id}")
        return ("ok", 200)

    # ---- Download recording and run pipeline ----
    wav_url = recording_url + ".wav"
    base = safe_base(call_sid)

    audio_path = os.path.join(AUDIO_DIR, base + "_FULLCALL.wav")
    transcript_path = os.path.join(TRANSCRIPTS_DIR, base + "_FULLCALL.txt")
    translation_path = os.path.join(TRANSLATIONS_DIR, base + "_FULLCALL.txt")
    english_audio_path = os.path.join(EN_AUDIO_DIR, base + "_FULLCALL.mp3")

    print("Downloading:", wav_url)
    r = requests.get(wav_url, auth=(TWILIO_SID, TWILIO_TOKEN), timeout=60)
    print("Download status:", r.status_code)
    r.raise_for_status()

    with open(audio_path, "wb") as f:
        f.write(r.content)

    text, detected = transcribe_audio(audio_path)

    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(text)

    # Guard: ignore extremely short transcripts
    if len(text.strip().split()) < 5:
        print("Transcript too short; not marking completed.")
        return ("ok", 200)

    if (detected or "").lower() == "en":
        english_text = text
    else:
        english_text = translate_to_english_chunked(text)

    with open(translation_path, "w", encoding="utf-8") as f:
        f.write(english_text)

    text_to_english_audio(english_text, english_audio_path)

    print("Saved:", audio_path)
    print("Saved:", transcript_path)
    print("Saved:", translation_path)
    print("Saved:", english_audio_path)

    outputs = {
        "audio_path": audio_path,
        "transcript_path": transcript_path,
        "translation_path": translation_path,
        "english_audio_path": english_audio_path,
    }

    if participant_id:
        mark_completed(state, participant_id, recording_url, outputs)
        save_participants(state)

    log_call_event({
        "timestamp_utc": datetime.utcnow().isoformat(),
        "participant_id": participant_id or "",
        "phone_e164": phone_e164 or "",
        "direction": direction,
        "call_sid": call_sid,
        "recording_url": recording_url,
        **outputs
    })

    return ("ok", 200)


def call_from_csv(csv_path="data/contacts.csv"):
    client = Client(TWILIO_SID, TWILIO_TOKEN)
    state = load_participants()

    with open(csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            participant_id = (row.get("participant_id") or "").strip()
            phone = (row.get("phone_e164") or "").strip()

            if not participant_id or not phone:
                continue

            upsert_participant(state, participant_id, phone)

            if not can_call(state, participant_id):
                continue

            call = client.calls.create(
                to=phone,
                from_=TWILIO_FROM,
                url=f"{PUBLIC_BASE_URL}/voice",
                method="POST",

                record=True,
                recording_status_callback=f"{PUBLIC_BASE_URL}/recording-done",
                recording_status_callback_method="POST",

                status_callback=f"{PUBLIC_BASE_URL}/call-status",
                status_callback_event=["completed", "no-answer", "busy", "failed", "canceled"],
                status_callback_method="POST",
            )

            mark_call_started(state, participant_id, call.sid)
            print(f"Calling {participant_id} -> {phone} | CallSid={call.sid}")

    save_participants(state)


if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "serve"

    if mode == "call":
        call_from_csv()
    elif mode == "reset":
        reset_call_log = "--log" in sys.argv
        reset_state(reset_call_log=reset_call_log, backup=True)
        print("State reset complete.")
        if reset_call_log:
            print("call_log.csv also reset (backed up).")
    else:
        app.run(host="0.0.0.0", port=5050, debug=False)