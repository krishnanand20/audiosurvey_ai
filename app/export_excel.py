import pandas as pd
from app.state import load_participants
from app.twilio_handler import load_structured_questions

def export_responses_to_excel():

    state = load_participants()
    questions = load_structured_questions()

    rows = []

    for pid, p in state.items():

        responses = p.get("responses", {})
        if not responses:
            continue

        row = {}
        row["participant_id"] = pid

        survey_q_counter = 1

        for q in range(len(questions)):

            question = questions[q]

            if question["type"] not in ["mcq","mcqo"]:
                continue

            digit = responses.get(f"q{q+1}")

            if digit:

                try:
                    option_text = question["options"][int(digit)-1]
                except:
                    option_text = digit

                row[f"Q{survey_q_counter}"] = option_text

            survey_q_counter += 1

        rows.append(row)

    if not rows:
        print("No responses found!")
        return

    df = pd.DataFrame(rows)

    df.to_excel("survey_output.xlsx", index=False)

    print("Excel created successfully!")