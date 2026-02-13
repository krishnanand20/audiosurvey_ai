# app/twilio_handler.py
from dotenv import load_dotenv
load_dotenv()

import os
import time
import json
import yaml
import requests
from datetime import datetime, timezone, timedelta
from zoneinfo import ZoneInfo

from flask import Flask, request, Response, redirect, session

from werkzeug.security import check_password_hash

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
        return yaml.safe_load(f) or {}


cfg = load_config()

TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_FROM = os.getenv("TWILIO_FROM_NUMBER")
PUBLIC_BASE_URL = (os.getenv("PUBLIC_BASE_URL") or "").rstrip("/")

# NOTE: To remove token-based auth from dashboard.py, set ADMIN_TOKEN blank in .env
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "").strip()

if not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM, PUBLIC_BASE_URL]):
    raise RuntimeError("Missing Twilio env vars in .env")

ivr_cfg = cfg.get("ivr", {}) or {}
GATHER_TIMEOUT = int(ivr_cfg.get("gather_timeout_sec", 6))
SPEECH_TIMEOUT = ivr_cfg.get("speech_timeout", "auto")
QUESTIONS_FILE = ivr_cfg.get("questions_file", "data/questions.txt")

# Twilio-native TTS voice
SAY_VOICE = ivr_cfg.get("say_voice", "alice")

# Kenya Kiswahili recognition
SPEECH_LANGUAGE = (ivr_cfg.get("speech_language") or "sw-KE").strip()

AUDIO_DIR = "data/audio"
TRANSCRIPTS_DIR = "data/transcripts"
TRANSLATIONS_DIR = "data/translations"
EN_AUDIO_DIR = "data/english_audio"
for d in [AUDIO_DIR, TRANSCRIPTS_DIR, TRANSLATIONS_DIR, EN_AUDIO_DIR]:
    os.makedirs(d, exist_ok=True)

# --------------------------
# Auth settings (hard)
# --------------------------
AUTH_STATE_PATH = os.getenv("AUTH_STATE_PATH", "data/auth_state.json")
AUTH_LOG_PATH = os.getenv("AUTH_LOG_PATH", "data/auth_log.jsonl")

AUTH_MAX_FAILS = int(os.getenv("AUTH_MAX_FAILS", "7"))
AUTH_LOCK_SECONDS = int(os.getenv("AUTH_LOCK_SECONDS", "900"))     # 15 min
AUTH_WINDOW_SECONDS = int(os.getenv("AUTH_WINDOW_SECONDS", "600")) # 10 min


def _ensure_parent(path: str) -> None:
    parent = os.path.dirname(path)
    if parent:
        os.makedirs(parent, exist_ok=True)


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def _ny_now_str() -> str:
    return datetime.now(NY_TZ).strftime("%Y-%m-%d %H:%M:%S %Z")


def _client_ip() -> str:
    xff = (request.headers.get("X-Forwarded-For") or "").split(",")[0].strip()
    return xff or (request.remote_addr or "unknown")


def _auth_key(username: str) -> str:
    return f"{(username or '').lower()}|{_client_ip()}"


def _load_auth_state() -> dict:
    if not os.path.exists(AUTH_STATE_PATH):
        return {"fails": {}, "locks": {}}
    try:
        with open(AUTH_STATE_PATH, "r", encoding="utf-8") as f:
            return json.load(f) or {"fails": {}, "locks": {}}
    except Exception:
        return {"fails": {}, "locks": {}}


def _save_auth_state(st: dict) -> None:
    _ensure_parent(AUTH_STATE_PATH)
    with open(AUTH_STATE_PATH, "w", encoding="utf-8") as f:
        json.dump(st, f, indent=2)


def _log_auth_event(event: dict) -> None:
    _ensure_parent(AUTH_LOG_PATH)
    with open(AUTH_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(event, ensure_ascii=False) + "\n")


def _is_locked(username: str) -> tuple[bool, int]:
    st = _load_auth_state()
    k = _auth_key(username)
    until = int(st.get("locks", {}).get(k, 0))
    now = int(time.time())
    if until > now:
        return True, until - now
    return False, 0


def _record_fail(username: str) -> None:
    st = _load_auth_state()
    k = _auth_key(username)
    now = int(time.time())

    fails = st.setdefault("fails", {}).setdefault(k, [])
    fails = [t for t in fails if now - int(t) <= AUTH_WINDOW_SECONDS]
    fails.append(now)
    st["fails"][k] = fails

    if len(fails) >= AUTH_MAX_FAILS:
        st.setdefault("locks", {})[k] = now + AUTH_LOCK_SECONDS

    _save_auth_state(st)


def _clear_fails(username: str) -> None:
    st = _load_auth_state()
    k = _auth_key(username)
    st.get("fails", {}).pop(k, None)
    st.get("locks", {}).pop(k, None)
    _save_auth_state(st)


def _load_users_from_config() -> dict:
    auth_cfg = cfg.get("auth", {}) or {}
    users = auth_cfg.get("users", {}) or {}
    out = {}
    for name, meta in users.items():
        out[str(name).lower()] = {
            "password_hash": (meta or {}).get("password_hash", "")
        }
    return out


def _verify_user(users: dict, username: str, password: str) -> bool:
    u = users.get((username or "").lower())
    if not u:
        return False
    return check_password_hash(u.get("password_hash", ""), password or "")


def _is_logged_in() -> bool:
    return bool(session.get("user"))


def _start_session(username: str) -> None:
    session["user"] = username
    session["login_utc"] = _utc_now_iso()
    session["login_ts"] = int(time.time())
    session["ip"] = _client_ip()

    _log_auth_event({
        "event": "login",
        "user": username,
        "ip": session["ip"],
        "login_utc": session["login_utc"],
        "login_local": _ny_now_str(),
        "user_agent": request.headers.get("User-Agent", ""),
    })


def _end_session() -> None:
    user = session.get("user")
    if not user:
        session.clear()
        return

    login_ts = int(session.get("login_ts") or 0)
    duration = max(0, int(time.time()) - login_ts)

    _log_auth_event({
        "event": "logout",
        "user": user,
        "ip": session.get("ip", ""),
        "logout_utc": _utc_now_iso(),
        "logout_local": _ny_now_str(),
        "session_duration_sec": duration,
    })

    session.clear()


def _render_login_page(err: str = "") -> str:
    return f"""
<!doctype html>
<html>
<head>
  <meta charset="utf-8" />
  <meta name="viewport" content="width=device-width,initial-scale=1" />
  <title>AudioSurvey AI — Login</title>
  <style>
    :root {{
      --bg: #0b1020;
      --card: rgba(18,26,51,.78);
      --muted: #9aa4c3;
      --text: #e8ecff;
      --line: rgba(255,255,255,.08);
      --accent: #7c5cff;
      --bad: #ff6b6b;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      font-family: -apple-system, BlinkMacSystemFont, "SF Pro Text", Segoe UI, Roboto, Helvetica, Arial, sans-serif;
      background: radial-gradient(1200px 800px at 20% 10%, rgba(124,92,255,.22), transparent 60%),
                  radial-gradient(900px 600px at 80% 20%, rgba(32,201,151,.12), transparent 55%),
                  var(--bg);
      color: var(--text);
      min-height: 100vh;
      display: grid;
      place-items: center;
      padding: 18px;
    }}
    .card {{
      width: 100%;
      max-width: 420px;
      background: var(--card);
      border: 1px solid var(--line);
      border-radius: 16px;
      padding: 18px;
      box-shadow: 0 10px 30px rgba(0,0,0,.25);
      backdrop-filter: blur(8px);
    }}
    h1 {{ margin: 0 0 6px 0; font-size: 20px; }}
    p {{ margin: 0 0 14px 0; color: var(--muted); font-size: 13px; }}
    .banner {{
      border-radius: 14px; padding: 10px 12px;
      border: 1px solid rgba(255,107,107,.35);
      background: rgba(255,107,107,.10);
      margin-bottom: 12px;
      font-size: 13px;
      color: var(--text);
    }}
    label {{ display:block; margin: 10px 0 6px; color: var(--muted); font-size: 12px; }}
    input {{
      width: 100%;
      border: 1px solid var(--line);
      background: rgba(0,0,0,.18);
      color: var(--text);
      padding: 10px 10px;
      border-radius: 12px;
      outline: none;
      font-size: 14px;
    }}
    button {{
      margin-top: 14px;
      width: 100%;
      border: 1px solid rgba(124,92,255,.35);
      background: rgba(124,92,255,.22);
      color: var(--text);
      padding: 10px 12px;
      border-radius: 12px;
      cursor: pointer;
      font-weight: 700;
    }}
    button:hover {{ background: rgba(124,92,255,.28); }}
  </style>
</head>
<body>
  <div class="card">
    <h1>AudioSurvey AI</h1>
    <p>Sign in to continue.</p>
    {f'<div class="banner">{err}</div>' if err else ''}
    <form method="POST" action="/login">
      <label>Username</label>
      <input name="username" autocomplete="username" />
      <label>Password</label>
      <input name="password" type="password" autocomplete="current-password" />
      <button type="submit">Sign in</button>
    </form>
  </div>
</body>
</html>
"""


# --------------------------
# Flask app
# --------------------------
app = Flask(__name__)
app.register_blueprint(dashboard_bp)

# Session secret (must set in .env)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "CHANGE_ME_NOW")

# hardened cookies
app.config.update(
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=True,   # ngrok is HTTPS (recommended)
    PERMANENT_SESSION_LIFETIME=timedelta(hours=8),
)

# Protect admin routes without touching dashboard.py
@app.before_request
def _guard_admin_routes():
    path = request.path or ""
    # allow login + health + Twilio webhooks
    allowed_prefixes = ("/login", "/health", "/voice", "/start", "/next", "/call-status", "/recording-done")
    if path.startswith(allowed_prefixes):
        return None

    if path.startswith("/admin"):
        # If old token auth is still set in env, allow token too (backward compatible)
        if ADMIN_TOKEN:
            tok = (request.args.get("token") or request.form.get("token") or "").strip()
            if tok == ADMIN_TOKEN:
                return None

        if not _is_logged_in():
            return redirect("/login")

    return None


@app.route("/", methods=["GET"])
def root():
    return redirect("/admin" if _is_logged_in() else "/login")


@app.route("/login", methods=["GET", "POST"])
def login_route():
    if request.method == "GET":
        return _render_login_page()

    users = _load_users_from_config()
    username = (request.form.get("username") or "").strip().lower()
    password = request.form.get("password") or ""

    if not username or not password:
        return _render_login_page("Please enter username and password.")

    locked, wait = _is_locked(username)
    if locked:
        return _render_login_page(f"Too many attempts. Try again in {wait} seconds.")

    if not _verify_user(users, username, password):
        _record_fail(username)
        return _render_login_page("Invalid credentials.")

    _clear_fails(username)
    _start_session(username)
    session.permanent = True
    return redirect("/admin")


@app.route("/logout", methods=["POST"])
def logout_route():
    _end_session()
    return redirect("/login")

# ================================
# CONFERENCE CALL (FIXED)
# ================================
@app.route("/admin/conference_call", methods=["POST"])
def admin_conference_call():
    n1 = (request.form.get("number_1") or "").strip()
    n2 = (request.form.get("number_2") or "").strip()

    if not n1 or not n2:
        return redirect("/admin?msg=Please+enter+both+phone+numbers")

    room = "CONF_" + datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    try:
        from twilio.rest import Client
        client = Client(TWILIO_SID, TWILIO_TOKEN)

        # call host (starts conf)
        client.calls.create(
            to=n1,
            from_=TWILIO_FROM,
            url=f"{PUBLIC_BASE_URL}/conference_host?room={room}",
            method="POST"
        )

        # call joiner (waits silently until host starts)
        client.calls.create(
            to=n2,
            from_=TWILIO_FROM,
            url=f"{PUBLIC_BASE_URL}/conference_join?room={room}",
            method="POST"
        )

        # ✅ poll until conference exists, then inject IVR
        conf = None
        for _ in range(20):  # ~10 seconds
            lst = client.conferences.list(friendly_name=room, status="in-progress", limit=1)
            if lst:
                conf = lst[0]
                break
            time.sleep(0.5)

        if conf:
            client.conferences(conf.sid).update(
                announce_url=f"{PUBLIC_BASE_URL}/conference_ivr",
                announce_method="POST"
            )
        else:
            log(f"Conference not found in time for room={room} (IVR not injected)")

        return redirect("/admin?msg=Conference+call+started")

    except Exception as e:
        log(f"Conference ERROR: {type(e).__name__}: {e}")
        return redirect("/admin?msg=Failed+to+start+conference")
    
# ================================
# HOST SIDE (IVR + RECORDING)
# ================================
@app.route("/conference_host", methods=["POST"])
def conference_host():
    room = request.args.get("room")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Dial>
    <Conference
      startConferenceOnEnter="true"
      endConferenceOnExit="false"
      beep="false"
      record="record-from-start"
      recordingStatusCallback="{PUBLIC_BASE_URL}/recording-done"
      recordingStatusCallbackMethod="POST"
      recordingStatusCallbackEvent="completed">
      {room}
    </Conference>
  </Dial>
</Response>"""
    return twiml(xml)

@app.route("/conference_join", methods=["POST"])
def conference_join():
    room = request.args.get("room")

    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Dial>
    <Conference
      startConferenceOnEnter="false"
      endConferenceOnExit="false"
      beep="false"
      waitUrl="{PUBLIC_BASE_URL}/silence"
      waitMethod="POST">
      {room}
    </Conference>
  </Dial>
</Response>"""
    return twiml(xml)

@app.route("/silence", methods=["POST", "GET"])
def silence():
    # Twilio will loop this while waiting (no music)
    return twiml("""<?xml version="1.0" encoding="UTF-8"?>
<Response>
  <Pause length="60"/>
</Response>""")

@app.route("/conference_ivr", methods=["POST"])
def conference_ivr():
    questions = load_questions()
    xml = '<?xml version="1.0" encoding="UTF-8"?><Response>'

    xml += f'<Say voice="{SAY_VOICE}">Habari. Huu ni utafiti wa maswali.</Say>'
    xml += '<Pause length="1"/>'

    for q in questions:
        xml += f'<Say voice="{SAY_VOICE}">{xml_escape(q)}</Say>'
        xml += '<Pause length="7"/>'

    xml += '</Response>'
    return twiml(xml)
# --------------------------
# Helpers
# --------------------------
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


def looks_like_real_speech(s: str) -> bool:
    if not s:
        return False
    t = s.strip()
    if not t:
        return False
    tl = t.lower()
    if tl in {"...", "…", "silence", "no speech"}:
        return False
    return True


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


@app.route("/admin/dial_now", methods=["POST"])
def admin_dial_now():
    # Protected by before_request session auth
    run_once(force=True)
    return redirect("/admin?msg=Dial+Now+triggered")


# --------------------------
# INBOUND CALL ENTRYPOINT
# --------------------------
@app.route("/voice", methods=["POST"])
def voice():
    """
    FIX: Start recording immediately using TwiML <Start><Recording>.
    (Avoids Twilio REST error 21220: resource not eligible for recording)
    """
    xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>

  <Start>
    <Recording
      recordingStatusCallback="{PUBLIC_BASE_URL}/recording-done"
      recordingStatusCallbackMethod="POST"
      recordingStatusCallbackEvent="completed" />
  </Start>

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
        return twiml(f"<Response><Say voice=\"{SAY_VOICE}\">Hakuna maswali yaliyoandaliwa.</Say><Hangup/></Response>")

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

    # Mark engaged for known participants
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
        # Inbound unknown calls won't be in participants.json
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

    known_participant = bool(participant_id)

    phone = (p.get("phone_e164") or "") if p else ""
    phone_masked = mask_phone(phone)
    engaged = bool(p.get("engaged", False)) if p else False
    last_call_status = (p.get("last_call_status") or "").lower() if p else ""

    if known_participant:
        if last_call_status in {"no-answer", "busy", "failed", "canceled"}:
            log("Skip pipeline: retryable failure.")
            return ("ok", 200)
        if not engaged:
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

    if known_participant:
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
        start_scheduler_in_background(interval_sec=15)
        app.run(host="0.0.0.0", port=5050, debug=False, use_reloader=False)

    elif mode == "schedule":
        if len(sys.argv) != 4:
            print("Usage: python3 -m app.twilio_handler schedule <participant_id> 'YYYY-MM-DD HH:MM'")
            sys.exit(1)
        schedule_participant(sys.argv[2], sys.argv[3])
        print(f"Scheduled participant {sys.argv[2]} at {sys.argv[3]} (NYC time)")
        sys.exit(0)

    elif mode == "reset":
        reset_call_log = "--log" in sys.argv
        reset_state(reset_call_log=reset_call_log, backup=True)
        print("State reset complete.")
        sys.exit(0)

    else:
        print("Unknown mode. Use: serve | schedule | reset")
        sys.exit(1)