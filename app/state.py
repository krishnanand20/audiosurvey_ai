# app/state.py
import os
import json
import csv
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

STATE_DIR = "data/state"
PARTICIPANTS_PATH = os.path.join(STATE_DIR, "participants.json")
CALL_LOG_PATH = os.path.join(STATE_DIR, "call_log.csv")

os.makedirs(STATE_DIR, exist_ok=True)

DEFAULT = {
    "status": "pending",          # pending | in_progress | completed | failed
    "attempts": 0,
    "last_call_time": None,       # ISO UTC string (no Z, just isoformat)
    "last_call_sid": None,
    "last_call_status": None,     # Twilio CallStatus
    "engaged": False,             # True only if we saw real SpeechResult
    "last_recording_url": None,
    "last_outputs": {},
    # Scheduling
    "scheduled_time_local": None, # human readable (NYC local)
    "scheduled_time_utc": None,   # ISO UTC for comparisons (may end with Z)
}

RETRY_GAP = timedelta(hours=1)    # production: 1 hour
MAX_ATTEMPTS = 3


def _now_utc() -> datetime:
    # timezone-aware UTC now
    return datetime.now(timezone.utc)


def _now_iso() -> str:
    # store as ISO string (UTC) without Z, consistent
    return _now_utc().replace(tzinfo=None).isoformat()


def migrate_add_schedule_fields(state: Dict[str, Any]) -> bool:
    """
    Ensures every participant has required keys.
    Returns True if any changes were made.
    """
    changed = False
    for _, p in state.items():
        for k, v in DEFAULT.items():
            if k not in p:
                p[k] = v
                changed = True
    return changed


def load_participants() -> Dict[str, Any]:
    """
    Safe loader:
    - Returns {} if file missing/empty
    - Backs up corrupted JSON and returns {}
    - Auto-migrates schema fields when new keys are added
    """
    if not os.path.exists(PARTICIPANTS_PATH):
        return {}

    try:
        with open(PARTICIPANTS_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            state = json.loads(content)

        if migrate_add_schedule_fields(state):
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


def upsert_participant(state: Dict[str, Any], participant_id: str, phone_e164: str) -> None:
    if participant_id not in state:
        state[participant_id] = {**DEFAULT, "phone_e164": phone_e164}
    else:
        state[participant_id]["phone_e164"] = phone_e164


def _parse_utc_iso(s: str) -> datetime:
    """
    Accepts:
    - "2026-01-28T19:15:00Z"
    - "2026-01-28T19:15:00+00:00"
    - "2026-01-28T19:15:00"  (treated as UTC naive)
    Returns timezone-aware UTC datetime.
    """
    s = (s or "").strip()
    if not s:
        raise ValueError("empty datetime")

    if s.endswith("Z"):
        s = s[:-1] + "+00:00"

    dt = datetime.fromisoformat(s)

    if dt.tzinfo is None:
        # treat naive as UTC
        dt = dt.replace(tzinfo=timezone.utc)

    return dt.astimezone(timezone.utc)


def can_call(state: Dict[str, Any], participant_id: str, require_schedule: bool = False) -> bool:
    """
    True only if:
    - not completed/failed
    - attempts < MAX_ATTEMPTS
    - if require_schedule=True: scheduled_time_utc must exist AND now >= scheduled_time_utc
    - retry gap passed since last_call_time (if any)
    """
    p = state.get(participant_id)
    if not p:
        # no record => if schedule is required, we cannot call yet
        return not require_schedule

    if p.get("status") in {"completed", "failed"}:
        return False

    if int(p.get("attempts", 0)) >= MAX_ATTEMPTS:
        return False

    # --- Scheduling gate ---
    sched_utc = p.get("scheduled_time_utc")

    if require_schedule and not sched_utc:
        return False

    if sched_utc:
        try:
            sched_dt = _parse_utc_iso(sched_utc)
            if _now_utc() < sched_dt:
                return False
        except Exception:
            # if schedule is required and schedule is broken => block call
            if require_schedule:
                return False
            # otherwise ignore broken schedule
            pass

    # --- Retry gap gate ---
    last_time = p.get("last_call_time")
    if not last_time:
        return True

    try:
        # last_call_time stored as naive UTC string
        last_dt = datetime.fromisoformat(last_time)
        last_dt = last_dt.replace(tzinfo=timezone.utc)
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


def log_call_event(row: Dict[str, Any]) -> None:
    file_exists = os.path.exists(CALL_LOG_PATH)
    headers = [
        "timestamp_utc", "participant_id", "phone_e164", "direction",
        "call_sid", "recording_url",
        "audio_path", "transcript_path", "translation_path", "english_audio_path"
    ]

    with open(CALL_LOG_PATH, "a", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=headers)
        if not file_exists:
            w.writeheader()
        w.writerow(row)


def mark_call_result(state: dict, participant_id: str, call_status: str) -> None:
    """
    Update participant status based on Twilio CallStatus callback.
    - We DO NOT mark completed here.
      Completion is decided in /recording-done using engaged + transcript guard.
    """
    p = state.setdefault(participant_id, dict(DEFAULT))
    cs = (call_status or "").lower().strip()

    p["last_call_status"] = cs

    if cs in {"no-answer", "busy", "failed", "canceled"}:
        if int(p.get("attempts", 0)) >= MAX_ATTEMPTS:
            p["status"] = "failed"
        else:
            p["status"] = "pending"
        return

    if cs == "completed":
        if p.get("status") != "completed":
            p["status"] = "in_progress"
        return

    if cs in {"initiated", "ringing", "answered", "in-progress"}:
        p["status"] = "in_progress"
        return


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