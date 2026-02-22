import pandas as pd
from app.state import load_participants


def export_responses_to_excel():

    state = load_participants()

    rows = []
    all_keys = set()

    # collect all question keys first
    for pid, p in state.items():
        responses = p.get("responses", {})
        for k in responses.keys():
            all_keys.add(k)

    all_keys = sorted(list(all_keys))

    # now build uniform rows
    for pid, p in state.items():

        row = {
            "participant_id": pid
        }

        responses = p.get("responses", {})

        for k in all_keys:
            row[k] = responses.get(k, "")

        rows.append(row)

    df = pd.DataFrame(rows)

    df.to_excel("survey_output.xlsx", index=False)

    print("Excel created successfully!")