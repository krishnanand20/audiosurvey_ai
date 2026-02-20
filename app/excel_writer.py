import os
import pandas as pd
from datetime import datetime

EXCEL_PATH = "data/survey_results.xlsx"

def filename_only(path):
    if not path:
        return ""
    return os.path.basename(path)


def write_participant_excel(participant_id, p):

    responses = p.get("responses", {})

    name = responses.get("Q0_response", "")
    address = responses.get("Q1_response", "")
    dob = responses.get("Q2_response", "")

    audio_file = filename_only(p.get("audio_path"))
    transcript_file = filename_only(p.get("transcript_path"))
    translation_file = filename_only(p.get("translation_path"))

    row = {
        "participant_id": participant_id,
        "name": name,
        "address": address,
        "dob": dob,
        "full_audio": audio_file,
        "transcript": transcript_file,
        "translation": translation_file,
        "timestamp": datetime.utcnow().isoformat()
    }

    # ADD ALL QUESTION RESPONSES
    for key, value in responses.items():
        if key.startswith("Q"):
            row[key] = value

    df_new = pd.DataFrame([row])

    if os.path.exists(EXCEL_PATH):
        df_old = pd.read_excel(EXCEL_PATH)
        df = pd.concat([df_old, df_new], ignore_index=True)
    else:
        df = df_new

    df.to_excel(EXCEL_PATH, index=False)

    print(f"[EXCEL] Participant {participant_id} added to Excel")