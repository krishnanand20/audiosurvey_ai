from __future__ import annotations

import os
from datetime import datetime
from zoneinfo import ZoneInfo
from typing import Optional

from twilio.rest import Client

from app.state import (
    load_participants,
    save_participants,
    upsert_participant,
    can_call,
    mark_call_started,
)

NY_TZ = ZoneInfo("America/New_York")
UTC_TZ = ZoneInfo("UTC")


def _require_env(name: str) -> str:
    v = (os.getenv(name) or "").strip()
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return v


def schedule_participant(participant_id: str, local_time_str: str) -> None:
    """
    Schedule a participant for a specific NYC local time.
    local_time_str format: YYYY-MM-DD HH:MM (NYC time)
    """
    state = load_participants()

    if participant_id not in state:
        raise ValueError(
            f"Participant '{participant_id}' not found. "
            f"Upload contacts first so participant exists."
        )

    # Parse local time as NYC
    local_dt = datetime.strptime(local_time_str, "%Y-%m-%d %H:%M").replace(tzinfo=NY_TZ)
    utc_dt = local_dt.astimezone(UTC_TZ)

    state[participant_id]["scheduled_time_local"] = local_dt.isoformat()
    state[participant_id]["scheduled_time_utc"] = utc_dt.isoformat().replace("+00:00", "Z")

    # Optional: reset status so scheduling works as expected
    state[participant_id]["status"] = "pending"

    save_participants(state)


def dial_eligible_participants() -> int:
    """
    Reads participants.json and calls ONLY eligible participants according to can_call().
    Returns number of calls placed.
    """
    TWILIO_SID = _require_env("TWILIO_ACCOUNT_SID")
    TWILIO_TOKEN = _require_env("TWILIO_AUTH_TOKEN")
    TWILIO_FROM = _require_env("TWILIO_FROM_NUMBER")
    PUBLIC_BASE_URL = _require_env("PUBLIC_BASE_URL").rstrip("/")

    client = Client(TWILIO_SID, TWILIO_TOKEN)
    state = load_participants()

    calls_placed = 0

    for pid, p in state.items():
        phone = (p.get("phone_e164") or "").strip()
        if not phone:
            continue

        if not can_call(state, pid):
            continue

        call = client.calls.create(
            to=phone,
            from_=TWILIO_FROM,
            url=f"{PUBLIC_BASE_URL}/voice",
            method="POST",

            # ✅ full call recording
            record=True,

            # ✅ recording callback so /recording-done runs pipeline
            recording_status_callback=f"{PUBLIC_BASE_URL}/recording-done",
            recording_status_callback_method="POST",

            # ✅ status callback so retry engine works
            status_callback=f"{PUBLIC_BASE_URL}/call-status",
            status_callback_event=["completed", "no-answer", "busy", "failed", "canceled"],
            status_callback_method="POST",
        )

        mark_call_started(state, pid, call.sid)
        calls_placed += 1

    if calls_placed:
        save_participants(state)

    return calls_placed