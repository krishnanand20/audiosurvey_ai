# app/utils.py
from datetime import datetime
from zoneinfo import ZoneInfo
from app.state import load_participants, save_participants

NY_TZ = ZoneInfo("America/New_York")
UTC_TZ = ZoneInfo("UTC")

def schedule_participant(participant_id: str, local_time_str: str) -> None:
    state = load_participants()
    if participant_id not in state:
        raise ValueError(f"Participant {participant_id} not found")

    local_dt = datetime.strptime(local_time_str, "%Y-%m-%d %H:%M").replace(tzinfo=NY_TZ)
    utc_dt = local_dt.astimezone(UTC_TZ)

    state[participant_id]["scheduled_time_local"] = local_dt.isoformat()
    state[participant_id]["scheduled_time_utc"] = utc_dt.isoformat().replace("+00:00", "Z")

    # Once scheduled, it's eligible in normal mode
    if state[participant_id].get("status") not in {"completed", "failed"}:
        state[participant_id]["status"] = "pending"

    save_participants(state)