from app.state import load_participants, save_participants
from app.twilio_handler import find_participant_by_callsid


def save_answer(call_sid, q, answer):

    state = load_participants()
    pid, _ = find_participant_by_callsid(state, call_sid)

    if not pid:
        return

    if "responses" not in state[pid]:
        state[pid]["responses"] = {}

    state[pid]["responses"][f"Q{q}_response"] = answer
    save_participants(state)