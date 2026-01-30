# app/twilio_handler.py
from dotenv import load_dotenv
load_dotenv()

import os
import yaml
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask, request, Response, redirect
from twilio.rest import Client

from app.dashboard import dashboard_bp
from app.scheduler import start_scheduler_in_background, run_once
from app.utils import schedule_participant
from app.state import (
    load_participants,
    save_participants,
    mark_engaged,
    mark_completed,
    mark_call_result,
    log_call_event,
    mask_phone,
    reset_state,
)

from app.transcribe import transcribe_audio
from app.translate import translate_to_english_chunked
from app.tts import text_to_english_audio

# --------------------------
# Time (NYC + UTC)
# --------------------------
NY_TZ = ZoneInfo("America/New_York")
UTC_TZ = ZoneInfo("UTC")


def log(msg: str) -> None:
    ny = datetime.now(NY_TZ).isoformat(timespec="seconds")
    utc = datetime.now(UTC_TZ).isoformat(timespec="seconds").replace("+00:00", "Z")
    print(f"[NYC {ny} | UTC {utc}] {msg}")


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
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "").strip()

if not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM, PUBLIC_BASE_URL]):
    raise RuntimeError("Missing Twilio env vars in .env")

GATHER_TIMEOUT = int(cfg.get("ivr", {}).get("gather_timeout_sec", 6))
SPEECH_TIMEOUT = cfg.get("ivr", {}).get("speech_timeout", "auto")
QUESTIONS_FILE = cfg.get("ivr", {}).get("questions_file", "data/questions.txt")

AUDIO_DIR = "data/audio"
TRANSCRIPTS_DIR = "data/transcripts"
TRANSLATIONS_DIR = "data/translations"
EN_AUDIO_DIR = "data/english_audio"
for d in [AUDIO_DIR, TRANSCRIPTS_DIR, TRANSLATIONS_DIR, EN_AUDIO_DIR]:
    os.makedirs(d, exist_ok=True)

# --------------------------
# Flask app
# --------------------------
app = Flask(__name__)
app.register_blueprint(dashboard_bp)


# --------------------------
# Helpers
# --------------------------
def load_questions():
    if not os.path.exists(QUESTIONS_FILE):
        return []
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        return [q.strip() for q in f if q.strip()]


def twiml(xml: str) -> Response:
    return Response(xml, mimetype="text/xml")


def xml_escape(s: str) -> str:
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def safe_base(call_sid: str) -> str:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"{call_sid}_{ts}"


def looks_like_real_speech(s: str) -> bool:
    if not s:
        return False
    t = s.strip().lower()
    if t in {"no", "no.", "nah", "none"}:
        return False
    return len(t.split()) >= 2


def find_participant_by_callsid(state: dict, call_sid: str):
    for pid, p in state.items():
        if p.get("last_call_sid") == call_sid:
            return pid, p
    return None, None


def require_admin(req) -> bool:
    if not ADMIN_TOKEN:
        return True
    return (req.args.get("token") == ADMIN_TOKEN) or (req.form.get("token") == ADMIN_TOKEN)


# --------------------------
# Routes
# --------------------------
@app.route("/health", methods=["GET"])
def health():
    return "ok", 200


# ---- Admin extra: dial now (uses scheduler.run_once) ----
@app.route("/admin/dial_now", methods=["POST"])
def admin_dial_now():
    if not require_admin(request):
        return ("Unauthorized", 401)

    run_once(force=True)  # ✅ CALL ALL IMMEDIATELY

    qs = f"?token={ADMIN_TOKEN}&msg=Dial+Now+triggered" if ADMIN_TOKEN else "?msg=Dial+Now+triggered"
    return redirect("/admin" + qs)


# ---- Twilio IVR ----
@app.route("/voice", methods=["POST"])
def voice():
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather input="dtmf" numDigits="1" timeout="8" action="{PUBLIC_BASE_URL}/start" method="POST">
    <Say voice="alice">To begin the survey, please press any key.</Say>
  </Gather>
  <Redirect method="POST">{PUBLIC_BASE_URL}/start</Redirect>
</Response>"""
    return twiml(xml)


@app.route("/start", methods=["POST"])
def start():
    questions = load_questions()
    if not questions:
        return twiml("<Response><Say>No questions configured.</Say><Hangup/></Response>")

    q1 = xml_escape(questions[0])
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="alice">Hello. This is a research survey call.</Say>
  <Gather input="speech" timeout="{GATHER_TIMEOUT}" speechTimeout="{SPEECH_TIMEOUT}"
          action="{PUBLIC_BASE_URL}/next?q=1" method="POST">
    <Say voice="alice">{q1}</Say>
  </Gather>
  <Redirect method="POST">{PUBLIC_BASE_URL}/next?q=1</Redirect>
</Response>"""
    return twiml(xml)


@app.route("/next", methods=["POST"])
def next_question():
    questions = load_questions()
    q = int(request.args.get("q", "0"))

    call_sid = request.form.get("CallSid", "")
    speech = (request.form.get("SpeechResult") or "").strip()

    if call_sid and looks_like_real_speech(speech):
        state = load_participants()
        pid, _ = find_participant_by_callsid(state, call_sid)
        if pid:
            mark_engaged(state, pid)
            save_participants(state)
            log(f"ENGAGED=True for participant {pid} | CallSid={call_sid}")

    if q >= len(questions):
        return twiml("<Response><Say>Thank you. Goodbye.</Say><Hangup/></Response>")

    question = xml_escape(questions[q])
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
    call_sid = request.form.get("CallSid", "")
    call_status_val = (request.form.get("CallStatus") or "").lower().strip()
    log(f"CALL STATUS HIT | CallSid={call_sid} | CallStatus={call_status_val}")

    state = load_participants()
    pid, p = find_participant_by_callsid(state, call_sid)
    if not pid:
        return ("ok", 200)

    mark_call_result(state, pid, call_status_val)

    # If completed but no speech, keep pending for retry
    engaged = bool(p.get("engaged", False)) if p else False
    if call_status_val == "completed" and not engaged:
        state[pid]["status"] = "pending"

    save_participants(state)
    return ("ok", 200)


@app.route("/recording-done", methods=["POST"])
def recording_done():
    call_sid = request.form.get("CallSid", "unknown_call")
    recording_url = request.form.get("RecordingUrl")
    rec_status = (request.form.get("RecordingStatus") or "").lower()
    direction = request.form.get("Direction") or ""

    log(f"RECORDING DONE HIT | CallSid={call_sid} | Status={rec_status}")

    if rec_status and rec_status != "completed":
        return ("ok", 200)
    if not recording_url:
        return ("no recording", 400)

    state = load_participants()
    participant_id, p = find_participant_by_callsid(state, call_sid)
    phone = (p.get("phone_e164") or "") if p else ""
    phone_masked = mask_phone(phone)
    engaged = bool(p.get("engaged", False)) if p else False
    last_call_status = (p.get("last_call_status") or "").lower() if p else ""

    if participant_id and last_call_status in {"no-answer", "busy", "failed", "canceled"}:
        log("Skip pipeline: retryable failure.")
        return ("ok", 200)
    if participant_id and not engaged:
        log("Skip pipeline: engaged=False.")
        return ("ok", 200)

    wav_url = recording_url + ".wav"
    base = safe_base(call_sid)

    audio_path = os.path.join(AUDIO_DIR, base + "_FULLCALL.wav")
    transcript_path = os.path.join(TRANSCRIPTS_DIR, base + "_FULLCALL.txt")
    translation_path = os.path.join(TRANSLATIONS_DIR, base + "_FULLCALL.txt")
    english_audio_path = os.path.join(EN_AUDIO_DIR, base + "_FULLCALL.mp3")

    r = requests.get(wav_url, auth=(TWILIO_SID, TWILIO_TOKEN), timeout=60)
    r.raise_for_status()
    with open(audio_path, "wb") as f:
        f.write(r.content)

    text, detected = transcribe_audio(audio_path)
    with open(transcript_path, "w", encoding="utf-8") as f:
        f.write(text)

    if len(text.strip().split()) < 15:
        log("Transcript too short. Not completing.")
        return ("ok", 200)

    english_text = text if (detected or "").lower() == "en" else translate_to_english_chunked(text)
    with open(translation_path, "w", encoding="utf-8") as f:
        f.write(english_text)

    text_to_english_audio(english_text, english_audio_path)

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
        "phone_masked": phone_masked,
        "direction": direction,
        "call_sid": call_sid,
        "recording_url": recording_url,
        **outputs
    })

    return ("ok", 200)


# --------------------------
# CLI
# --------------------------
if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "serve"

    if mode == "serve":
        # keep 15s for testing
        start_scheduler_in_background(interval_sec=15)
        app.run(host="0.0.0.0", port=5050, debug=False, use_reloader=False)

    elif mode == "schedule":
        # python3 -m app.twilio_handler schedule 1 "2026-01-28 19:00"
        if len(sys.argv) != 4:
            print("Usage: python3 -m app.twilio_handler schedule <participant_id> 'YYYY-MM-DD HH:MM'")
            sys.exit(1)
        schedule_participant(sys.argv[2], sys.argv[3])
        print(f"✅ Scheduled participant {sys.argv[2]} at {sys.argv[3]} (NYC time)")
        sys.exit(0)

    elif mode == "reset":
        reset_call_log = "--log" in sys.argv
        reset_state(reset_call_log=reset_call_log, backup=True)
        print("State reset complete.")
        sys.exit(0)

    else:
        print("Unknown mode. Use: serve | schedule | reset")
        sys.exit(1)