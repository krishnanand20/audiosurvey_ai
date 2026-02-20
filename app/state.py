# app/state.py
import os
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from zoneinfo import ZoneInfo

STATE_DIR = "data/state"
PARTICIPANTS_PATH = os.path.join(STATE_DIR, "participants.json")
CALL_LOG_PATH = os.path.join(STATE_DIR, "call_log.csv")
SETTINGS_PATH = os.path.join(STATE_DIR, "settings.json")

os.makedirs(STATE_DIR, exist_ok=True)

DEFAULT = {
    "status": "pending",          # pending | in_progress | completed | failed
    "attempts": 0,
    "last_call_time": None,       # ISO UTC string
    "last_call_sid": None,
    "last_call_status": None,     # Twilio CallStatus
    "engaged": False,             # True only if we saw real SpeechResult
    "last_recording_url": None,
    "last_outputs": {},
    # Scheduling
    "scheduled_time_local": None, # human readable (NYC local)
    "scheduled_time_utc": None,   # ISO UTC for comparisons
    # Phone (PII) - stored locally only (gitignored)
    "phone_e164": None,
}

RETRY_GAP = timedelta(hours=1)    # production: 1 hour (test: minutes)
MAX_ATTEMPTS = 3

def _now_utc() -> datetime:
    return datetime.utcnow()

def _now_iso() -> str:
    return _now_utc().isoformat()

def mask_phone(phone: Optional[str]) -> str:
    """Return masked phone string; never return raw."""
    if not phone:
        return ""
    p = phone.strip()
    if len(p) <= 4:
        return "****"
    return p[:2] + "******" + p[-4:]

def migrate_add_fields(state: Dict[str, Any]) -> bool:
    changed = False
    for _, p in state.items():
        for k, v in DEFAULT.items():
            if k not in p:
                p[k] = v
                changed = True
    return changed

def load_participants() -> Dict[str, Any]:
    if not os.path.exists(PARTICIPANTS_PATH):
        return {}
    try:
        with open(PARTICIPANTS_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            state = json.loads(content)
        if migrate_add_fields(state):
            save_participants(state)
        return state
    except (json.JSONDecodeError, OSError):
        try:
            os.rename(PARTICIPANTS_PATH, PARTICIPANTS_PATH + ".corrupt")
        except OSError:
            pass
        return {}

def save_participants(state: dict) -> None:
    tmp_path = PARTICIPANTS_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, PARTICIPANTS_PATH)

def reset_for_retry(state: dict, participant_id: str, reset_attempts: bool = False) -> None:
    p = state.get(participant_id)
    if not p:
        return
    p["status"] = "pending"
    p["engaged"] = False
    p["last_call_sid"] = None
    p["last_call_status"] = None
    if reset_attempts:
        p["attempts"] = 0
        p["last_call_time"] = None

def upsert_participant(state: Dict[str, Any], participant_id: str, phone_e164: str) -> None:
    if participant_id not in state:
        state[participant_id] = {**DEFAULT, "phone_e164": phone_e164}
    else:
        state[participant_id]["phone_e164"] = phone_e164

def can_call(state: Dict[str, Any], participant_id: str, force: bool = False) -> bool:

    p = state.get(participant_id)
    if not p:
        return False

    if p.get("status") in {"completed", "failed"}:
        return False

    if int(p.get("attempts", 0)) >= MAX_ATTEMPTS:
        return False

    # 🚨 FORCE MODE (Dial Now)
    if force:
        return True

    # 🚨 NORMAL MODE MUST BE SCHEDULED
    sched_utc = p.get("scheduled_time_utc")
    if not sched_utc:
        return False

    try:
        sched_dt = datetime.fromisoformat(sched_utc.replace("Z", ""))
        if _now_utc() < sched_dt:
            return False
    except Exception:
        return False

    last_time = p.get("last_call_time")
    if not last_time:
        return True

    try:
        last_dt = datetime.fromisoformat(last_time)
    except Exception:
        return True

    return (_now_utc() - last_dt) >= RETRY_GAP


def mark_engaged(state: dict, participant_id: str) -> None:
    p = state.setdefault(participant_id, dict(DEFAULT))
    p["engaged"] = True

def mark_call_started(state: Dict[str, Any], participant_id: str, call_sid: str) -> None:
    p = state.setdefault(participant_id, dict(DEFAULT))
    p["status"] = "in_progress"
    p["attempts"] = int(p.get("attempts", 0)) + 1
    p["last_call_time"] = _now_iso()
    p["last_call_sid"] = call_sid
    p["engaged"] = False  # reset each attempt

def mark_completed(state: Dict[str, Any], participant_id: str, recording_url: str, outputs: Dict[str, str]) -> None:
    p = state.setdefault(participant_id, dict(DEFAULT))
    p["status"] = "completed"
    p["last_recording_url"] = recording_url
    p["last_outputs"] = outputs

def mark_call_result(state: dict, participant_id: str, call_status: str) -> None:
    p = state.setdefault(participant_id, dict(DEFAULT))
    cs = (call_status or "").lower().strip()
    p["last_call_status"] = cs

    if cs in {"no-answer", "busy", "failed", "canceled"}:
        p["status"] = "failed" if int(p.get("attempts", 0)) >= MAX_ATTEMPTS else "pending"
        return

    if cs == "completed":
        # Not equivalent to "survey complete"
        if p.get("status") != "completed":
            p["status"] = "in_progress"
        return

    if cs in {"initiated", "ringing", "answered", "in-progress"}:
        p["status"] = "in_progress"

def log_call_event(row: Dict[str, Any]) -> None:
    file_exists = os.path.exists(CALL_LOG_PATH)
    headers = [
  "timestamp_utc", "participant_id", "phone_masked", "direction",
  "call_sid", "recording_url",
  "audio_path", "transcript_path", "translation_path", "english_audio_path"
]
    with open(CALL_LOG_PATH, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in headers})

def load_settings() -> Dict[str, Any]:
    if not os.path.exists(SETTINGS_PATH):
        return {"paused": False}
    try:
        with open(SETTINGS_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"paused": False}

def save_settings(settings: Dict[str, Any]) -> None:
    tmp = SETTINGS_PATH + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=2)
    os.replace(tmp, SETTINGS_PATH)

def set_paused(paused: bool) -> None:
    s = load_settings()
    s["paused"] = bool(paused)
    save_settings(s)

def is_paused() -> bool:
    return bool(load_settings().get("paused", False))

def reset_state(reset_call_log: bool = False, backup: bool = True) -> None:
    os.makedirs(STATE_DIR, exist_ok=True)
    ts = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    if os.path.exists(PARTICIPANTS_PATH):
        if backup:
            os.rename(PARTICIPANTS_PATH, f"{PARTICIPANTS_PATH}.bak_{ts}")
        else:
            os.remove(PARTICIPANTS_PATH)

    if reset_call_log and os.path.exists(CALL_LOG_PATH):
        if backup:
            os.rename(CALL_LOG_PATH, f"{CALL_LOG_PATH}.bak_{ts}")
        else:
            os.remove(CALL_LOG_PATH)

    # Reset settings (paused=false)
    save_settings({"paused": False})