# app/state.py
import os
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, Any

STATE_DIR = "data/state"
PARTICIPANTS_PATH = os.path.join(STATE_DIR, "participants.json")
CALL_LOG_PATH = os.path.join(STATE_DIR, "call_log.csv")

os.makedirs(STATE_DIR, exist_ok=True)

DEFAULT = {
    "status": "pending",          # pending | in_progress | completed | failed
    "attempts": 0,
    "last_call_time": None,       # ISO string
    "last_call_sid": None,
    "last_call_status": None,
    "engaged": False,     # ✅ store last Twilio CallStatus (completed/no-answer/busy/failed/...)
    "last_recording_url": None,
    "last_outputs": {},
}

RETRY_GAP = timedelta(hours=1)    # ✅ 1 hour
MAX_ATTEMPTS = 3                  # ✅ 3


def _now_iso() -> str:
    return datetime.utcnow().isoformat()

def mark_engaged(state: dict, participant_id: str) -> None:
    p = state.setdefault(participant_id, dict(DEFAULT))
    p["engaged"] = True


def load_participants() -> Dict[str, Any]:
    """
    Safe loader:
    - Returns {} if file missing/empty
    - Backs up corrupted JSON and returns {}
    """
    if not os.path.exists(PARTICIPANTS_PATH):
        return {}

    try:
        with open(PARTICIPANTS_PATH, "r", encoding="utf-8") as f:
            content = f.read().strip()
            if not content:
                return {}
            return json.loads(content)
    except (json.JSONDecodeError, OSError):
        # Backup corrupted file and start fresh
        try:
            os.rename(PARTICIPANTS_PATH, PARTICIPANTS_PATH + ".corrupt")
        except OSError:
            pass
        return {}


def save_participants(state: dict) -> None:
    """
    Atomic write to avoid partial JSON (prevents JSONDecodeError).
    """
    tmp_path = PARTICIPANTS_PATH + ".tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)
    os.replace(tmp_path, PARTICIPANTS_PATH)


def upsert_participant(state: Dict[str, Any], participant_id: str, phone_e164: str) -> None:
    if participant_id not in state:
        state[participant_id] = {**DEFAULT, "phone_e164": phone_e164}
    else:
        state[participant_id]["phone_e164"] = phone_e164


def can_call(state: Dict[str, Any], participant_id: str) -> bool:
    p = state.get(participant_id)
    if not p:
        return True

    if p.get("status") == "completed":
        return False

    if int(p.get("attempts", 0)) >= MAX_ATTEMPTS:
        return False

    last_time = p.get("last_call_time")
    if not last_time:
        return True

    try:
        last_dt = datetime.fromisoformat(last_time)
    except Exception:
        return True

    return (datetime.utcnow() - last_dt) >= RETRY_GAP


def mark_call_started(state: Dict[str, Any], participant_id: str, call_sid: str) -> None:
    p = state.setdefault(participant_id, dict(DEFAULT))
    p["status"] = "in_progress"
    p["attempts"] = int(p.get("attempts", 0)) + 1
    p["last_call_time"] = _now_iso()
    p["last_call_sid"] = call_sid
    # don't overwrite last_call_status here; it'll be set by call-status callback


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
    Also stores last_call_status for gating /recording-done completion.
    """
    p = state.setdefault(participant_id, dict(DEFAULT))
    cs = (call_status or "").lower().strip()

    # ✅ Always store last call status
    p["last_call_status"] = cs  

    # Terminal success
    if cs == "completed":
        p["status"] = "completed"
        return

    # Retryable failures
    if cs in {"no-answer", "busy", "failed", "canceled"}:
        if int(p.get("attempts", 0)) >= MAX_ATTEMPTS:
            p["status"] = "failed"
        else:
            p["status"] = "pending"
        return

    # Non-terminal statuses (informational)
    if cs in {"initiated", "ringing", "answered", "in-progress"}:
        p["status"] = "in_progress"
        return


def reset_state(reset_call_log: bool = False, backup: bool = True) -> None:
    """
    Resets participant state for a fresh run.
    - backup=True renames participants.json -> participants.json.bak_<timestamp>
    - reset_call_log=True also backs up / clears call_log.csv
    """
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