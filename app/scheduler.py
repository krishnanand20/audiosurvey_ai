# app/scheduler.py
import os
import time
from datetime import datetime
from zoneinfo import ZoneInfo

from twilio.rest import Client

from app.state import load_participants, save_participants, can_call, mark_call_started

NY_TZ = ZoneInfo("America/New_York")


def log(msg: str) -> None:
    now_ny = datetime.now(NY_TZ).strftime("%Y-%m-%d %H:%M:%S %Z")
    print(f"[{now_ny}] {msg}")


def run_once(require_schedule: bool = True) -> None:
    """
    One scheduler tick:
    - Reads participants.json (data/state/participants.json)
    - Calls ONLY participants eligible now via can_call()
    - Writes back participants.json if it placed any calls

    require_schedule=True:
      - only calls participants who have scheduled_time_utc set AND is due
    """
    TWILIO_SID = os.getenv("TWILIO_ACCOUNT_SID")
    TWILIO_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
    TWILIO_FROM = os.getenv("TWILIO_FROM_NUMBER")
    PUBLIC_BASE_URL = (os.getenv("PUBLIC_BASE_URL") or "").rstrip("/")

    if not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM, PUBLIC_BASE_URL]):
        log("Scheduler skipped: missing Twilio env vars.")
        return

    client = Client(TWILIO_SID, TWILIO_TOKEN)
    state = load_participants()

    any_called = False

    for participant_id, p in state.items():
        phone = (p.get("phone_e164") or "").strip()
        if not phone:
            continue

        # ✅ IMPORTANT: require_schedule=True enables scheduled_time_utc gating
        if not can_call(state, participant_id, require_schedule=require_schedule):
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


def run_loop(interval_sec: int = 15, require_schedule: bool = True) -> None:
    """
    Continuous scheduler loop.
    require_schedule=True -> schedule must be set to call.
    """
    log(f"Scheduler loop started (interval_sec={interval_sec}, require_schedule={require_schedule})")

    # Optional small delay so app/server has time to boot
    time.sleep(2)

    tick = 0
    while True:
        try:
            run_once(require_schedule=require_schedule)
        except Exception as e:
            log(f"Scheduler ERROR: {repr(e)}")

        # prevent log spam: print heartbeat every ~2 minutes if 15s interval
        tick += 1
        if tick % max(1, int(120 / interval_sec)) == 0:
            log("Scheduler heartbeat: running...")

        time.sleep(interval_sec)