# app/scheduler.py
import os
import time
import threading
from datetime import datetime
from zoneinfo import ZoneInfo

from twilio.rest import Client
from app.state import (
    load_participants,
    save_participants,
    can_call,
    mark_call_started,
    is_paused,
)

NY_TZ = ZoneInfo("America/New_York")


def log(msg: str) -> None:
    now_ny = datetime.now(NY_TZ).strftime("%Y-%m-%d %H:%M:%S %Z")
    print(f"[{now_ny}] {msg}")


def run_once(force: bool = False) -> None:
    """
    One tick.
    - force=False: normal behavior (schedule + retry gap enforced)
    - force=True : Dial Now behavior (ignore schedule + ignore retry gap)
    """
    if is_paused() and not force:
        log("Paused: no calls placed.")
        return

    TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_FROM = os.getenv("TWILIO_FROM_NUMBER")
    PUBLIC_BASE_URL = (os.getenv("PUBLIC_BASE_URL") or "").rstrip("/")

    if not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM, PUBLIC_BASE_URL]):
        log("Scheduler skipped: missing Twilio env vars.")
        return

    state = load_participants()
    if not state:
        log("No participants loaded (participants.json empty).")
        return

    client = Client(TWILIO_SID, TWILIO_TOKEN)

    any_called = False
    for participant_id, p in state.items():
        phone = (p.get("phone_e164") or "").strip()
        if not phone:
            continue

        # ✅ Normal scheduler respects schedule + retry
        # ✅ Dial Now forces call ignoring schedule + retry
        if not can_call(state, participant_id, force=force):
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
        log(f"Calling {participant_id} -> {phone} | CallSid={call.sid}")
        any_called = True

    if any_called:
        save_participants(state)
        log("Saved participants.json updates.")
    else:
        log("No eligible participants to call right now.")


def start_scheduler_in_background(interval_sec: int = 15) -> None:
    """
    Background loop for normal scheduled calling.
    """
    def _loop():
        log(f"[Scheduler] started (interval={interval_sec}s)")
        while True:
            try:
                run_once(force=False)
            except Exception as e:
                log(f"[Scheduler ERROR] {repr(e)}")
            time.sleep(interval_sec)

    t = threading.Thread(target=_loop, daemon=True)
    t.start()