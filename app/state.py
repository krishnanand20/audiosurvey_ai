# app/state.py
import os
import json
import csv
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

STATE_DIR = "data/state"
PARTICIPANTS_PATH = os.path.join(STATE_DIR, "participants.json")
CALL_LOG_PATH = os.path.join(STATE_DIR, "call_log.csv")

os.makedirs(STATE_DIR, exist_ok=True)

DEFAULT = {
    "status": "pending",          # pending | in_progress | completed | failed
    "attempts": 0,
    "last_call_time": None,       # ISO string
    "last_call_sid": None,
    "last_recording_url": None,
    "last_outputs": {}
}

RETRY_GAP = timedelta(hours=1)     # ✅ 1 hour
MAX_ATTEMPTS = 3                  # ✅ 3


def _now_iso() -> str:
    return datetime.utcnow().isoformat()


def load_participants() -> Dict[str, Any]:
    if not os.path.exists(PARTICIPANTS_PATH):
        return {}
    with open(PARTICIPANTS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def save_participants(state: Dict[str, Any]) -> None:
    with open(PARTICIPANTS_PATH, "w", encoding="utf-8") as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


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


def mark_completed(state: Dict[str, Any], participant_id: str, recording_url: str, outputs: Dict[str, str]) -> None:
    p = state.setdefault(participant_id, dict(DEFAULT))
    p["status"] = "completed"
    p["last_recording_url"] = recording_url
    p["last_outputs"] = outputs


def log_call_event(row: Dict[str, Any]) -> None:
    # Create log file with headers if missing
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