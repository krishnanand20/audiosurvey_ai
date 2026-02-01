# app/twilio_handler.py
from dotenv import load_dotenv
load_dotenv()

import os
import yaml
import requests
from datetime import datetime
from zoneinfo import ZoneInfo

from flask import Flask, request, Response, redirect

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

NY_TZ = ZoneInfo("America/New_York")
UTC_TZ = ZoneInfo("UTC")


def log(msg: str) -> None:
    ny = datetime.now(NY_TZ).isoformat(timespec="seconds")
    utc = datetime.now(UTC_TZ).isoformat(timespec="seconds").replace("+00:00", "Z")
    print(f"[NYC {ny} | UTC {utc}] {msg}")


def load_config(path="config.yaml"):
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


cfg = load_config()

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM_NUMBER")
PUBLIC_BASE_URL = (os.getenv("PUBLIC_BASE_URL") or "").rstrip("/")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "").strip()

if not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM, PUBLIC_BASE_URL]):
    raise RuntimeError("Missing Twilio env vars in .env")

ivr_cfg = cfg.get("ivr", {}) or {}
GATHER_TIMEOUT = int(ivr_cfg.get("gather_timeout_sec", 6))
SPEECH_TIMEOUT = ivr_cfg.get("speech_timeout", "auto")
QUESTIONS_FILE = ivr_cfg.get("questions_file", "data/questions.txt")

# ✅ Keep Twilio-native voice "alice"
SAY_VOICE = ivr_cfg.get("say_voice", "alice")

# ✅ IMPORTANT: default to Kenya Kiswahili
SPEECH_LANGUAGE = (ivr_cfg.get("speech_language") or "sw-KE").strip()

AUDIO_DIR = "data/audio"
TRANSCRIPTS_DIR = "data/transcripts"
TRANSLATIONS_DIR = "data/translations"
EN_AUDIO_DIR = "data/english_audio"
for d in [AUDIO_DIR, TRANSCRIPTS_DIR, TRANSLATIONS_DIR, EN_AUDIO_DIR]:
    os.makedirs(d, exist_ok=True)

app = Flask(__name__)
app.register_blueprint(dashboard_bp)


def load_questions():
    if not os.path.exists(QUESTIONS_FILE):
        return []
    with open(QUESTIONS_FILE, "r", encoding="utf-8") as f:
        return [q.strip() for q in f if q.strip()]


def twiml(xml: str) -> Response:
    return Response(xml, mimetype="text/xml; charset=utf-8")


def xml_escape(s: str) -> str:
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def safe_base(call_sid: str) -> str:
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    return f"{call_sid}_{ts}"


# ✅ FIX: Accept 1-word answers (Ndiyo/Hapana/Mmoja/etc.)
def looks_like_real_speech(s: str) -> bool:
    if not s:
        return False

    t = s.strip()
    if not t:
        return False

    # Reject obvious empty garbage only
    tl = t.lower()
    if tl in {"...", "…", "silence", "no speech"}:
        return False

    # ✅ accept ANY non-empty response (including 1 word)
    return True


def find_participant_by_callsid(state: dict, call_sid: str):
    for pid, p in state.items():
        if p.get("last_call_sid") == call_sid:
            return pid, p
    return None, None


def require_admin(req) -> bool:
    if not ADMIN_TOKEN:
        return True
    return (req.args.get("token") == ADMIN_TOKEN) or (req.form.get("token") == ADMIN_TOKEN)


@app.route("/health", methods=["GET"])
def health():
    return "ok", 200


@app.route("/admin/dial_now", methods=["POST"])
def admin_dial_now():
    if not require_admin(request):
        return ("Unauthorized", 401)

    run_once(force=True)

    qs = f"?token={ADMIN_TOKEN}&msg=Dial+Now+triggered" if ADMIN_TOKEN else "?msg=Dial+Now+triggered"
    return redirect("/admin" + qs)


@app.route("/voice", methods=["POST"])
def voice():
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather input="dtmf" numDigits="1" timeout="8" action="{PUBLIC_BASE_URL}/start" method="POST">
    <Say voice="{SAY_VOICE}">Bonyeza kitufe chochote kuanza utafiti.</Say>
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

    lang_attr = f'language="{SPEECH_LANGUAGE}"' if SPEECH_LANGUAGE else ""

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Say voice="{SAY_VOICE}">Habari. Huu ni utafiti wa maswali.</Say>
  <Say voice="{SAY_VOICE}">Tafadhali jibu kila swali baada ya kusikiliza.</Say>

  <Gather input="speech" timeout="{GATHER_TIMEOUT}" speechTimeout="{SPEECH_TIMEOUT}"
          {lang_attr}
          action="{PUBLIC_BASE_URL}/next?q=1" method="POST">
    <Say voice="{SAY_VOICE}">{q1}</Say>
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
            log(f"ENGAGED=True for participant {pid} | CallSid={call_sid} | Speech='{speech[:60]}'")

    if q >= len(questions):
        return twiml(f"<Response><Say voice=\"{SAY_VOICE}\">Asante. Kwaheri.</Say><Hangup/></Response>")

    question = xml_escape(questions[q])
    next_q = q + 1

    lang_attr = f'language="{SPEECH_LANGUAGE}"' if SPEECH_LANGUAGE else ""

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Gather input="speech" timeout="{GATHER_TIMEOUT}" speechTimeout="{SPEECH_TIMEOUT}"
          {lang_attr}
          action="{PUBLIC_BASE_URL}/next?q={next_q}" method="POST">
    <Say voice="{SAY_VOICE}">{question}</Say>
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

    if len(text.strip().split()) < 5:
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


if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "serve"

    if mode == "serve":
        start_scheduler_in_background(interval_sec=15)
        app.run(host="0.0.0.0", port=5050, debug=False, use_reloader=False)

    elif mode == "schedule":
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