import pandas as pd
from app.state import load_participants
import os
import re
import yaml
from app.translate import translate_to_english_chunked

RESULTS_PATH = "data/results/ivr_responses.xlsx"
RESULTS_EN_PATH = "data/results/ivr_responses_english.xlsx"


def _questions_file_path(default_path="data/questions.txt"):
    path = default_path
    try:
        with open("config.yaml", "r", encoding="utf-8") as f:
            cfg = yaml.safe_load(f) or {}
        path = ((cfg.get("ivr") or {}).get("questions_file") or path).strip()
    except Exception:
        pass
    return path


def _load_structured_questions():
    path = _questions_file_path()
    questions = []
    if not os.path.exists(path):
        return questions

    with open(path, "r", encoding="utf-8") as f:
        for raw in f:
            line = raw.strip()
            if not line:
                continue
            parts = line.split("|")
            q_type = parts[0].strip()
            if q_type in {"MCQ", "MCQO"} and len(parts) >= 3:
                questions.append(
                    {
                        "type": q_type.lower(),
                        "question": parts[1],
                        "options": parts[2:],
                    }
                )
            elif q_type == "OPEN" and len(parts) >= 2:
                questions.append({"type": "open", "question": parts[1]})
            elif q_type == "INFO" and len(parts) >= 2:
                questions.append({"type": "info", "question": parts[1]})

    return questions


def _build_response_metadata():
    metadata = {}
    survey_q_counter = 0
    questions = _load_structured_questions()
    # Runtime starts collecting responses only after the first 2 intro prompts.
    response_flow_questions = questions[2:] if len(questions) > 2 else []

    for q in response_flow_questions:
        q_type = q.get("type")
        if q_type not in {"open", "mcq", "mcqo"}:
            continue

        survey_q_counter += 1
        q_key = f"q{survey_q_counter}"
        metadata[q_key] = {"type": q_type, "options": q.get("options", [])}

        if q_type == "mcqo":
            other_digit = None
            for i, opt in enumerate(q.get("options", []), start=1):
                opt_norm = (opt or "").strip().lower()
                if opt_norm in {"other", "nyingine"}:
                    other_digit = str(i)
                    break
            metadata[q_key]["other_digit"] = other_digit

    return metadata


def _decode_choice_value(value, options):
    """
    Convert stored DTMF digit (1/2/3...) to option text for Excel.
    If value is not a valid digit for these options, keep raw value.
    """
    opts = list(options or [])
    if not opts:
        return value

    raw = str(value).strip()
    if not raw:
        return value

    try:
        # Support values like "1", 1, or "1.0"
        digit = int(float(raw))
    except Exception:
        return value

    idx = digit - 1
    if 0 <= idx < len(opts):
        return opts[idx]
    return value


def _build_export_key_map(metadata):
    remap = {}
    export_idx = 0

    def qnum(k):
        m = re.findall(r"\d+", str(k))
        return int(m[0]) if m else 0

    for old_key in sorted(metadata.keys(), key=qnum):
        if metadata.get(old_key, {}).get("type") == "open":
            continue
        export_idx += 1
        remap[old_key] = f"q{export_idx}"

    return remap


def filter_responses_for_excel(responses, metadata=None):
    meta = metadata or _build_response_metadata()
    filtered = {}

    for key, value in (responses or {}).items():
        # Never export free-speech "other" fields (legacy/current safety)
        if str(key).endswith("_other"):
            continue

        rule = meta.get(key)

        if not rule:
            filtered[key] = value
            continue

        if rule.get("type") == "open":
            continue

        filtered[key] = value

    return filtered


def build_export_rows(state, participant_ids=None):
    metadata = _build_response_metadata()
    export_key_map = _build_export_key_map(metadata)
    rows = []
    allowed_ids = None
    if participant_ids is not None:
        allowed_ids = {str(x) for x in participant_ids}

    for pid, pdata in (state or {}).items():
        if allowed_ids is not None and str(pid) not in allowed_ids:
            continue

        responses = pdata.get("responses", {})
        if not responses:
            continue

        filtered = filter_responses_for_excel(responses, metadata=metadata)
        if not filtered:
            continue

        row = {"participant_id": pid}
        for key, value in filtered.items():
            rule = metadata.get(key, {})
            q_type = rule.get("type")
            if q_type in {"mcq", "mcqo"}:
                value = _decode_choice_value(value, rule.get("options", []))
            row[export_key_map.get(key, key)] = value
        rows.append(row)

    return rows


def _ordered_columns(columns):
    q_cols = sorted(
        [c for c in columns if str(c).startswith("q")],
        key=lambda x: int(re.findall(r"\d+", str(x))[0]),
    )
    other_cols = [c for c in columns if c not in q_cols and c != "participant_id"]
    return ["participant_id"] + q_cols + other_cols


def _rows_to_dataframe(rows):
    df = pd.DataFrame(rows)
    return df[_ordered_columns(df.columns)]


def export_responses_to_excel(append=True):

    state = load_participants()
    if not state:
        return

    rows = build_export_rows(state)

    if not rows:
        return

    os.makedirs("data/results", exist_ok=True)
    new_df = _rows_to_dataframe(rows)

    if append and os.path.exists(RESULTS_PATH):
        old_df = pd.read_excel(RESULTS_PATH)
        final_df = pd.concat([old_df, new_df], ignore_index=True)
        final_df = final_df[_ordered_columns(final_df.columns)]
    else:
        final_df = new_df

    final_df.to_excel(RESULTS_PATH, index=False)


def append_participant_response_to_excel(participant_id):
    state = load_participants()
    if not state:
        return False

    rows = build_export_rows(state, participant_ids={participant_id})
    if not rows:
        return False

    new_df = _rows_to_dataframe(rows)
    os.makedirs("data/results", exist_ok=True)

    if os.path.exists(RESULTS_PATH):
        old_df = pd.read_excel(RESULTS_PATH)
        final_df = pd.concat([old_df, new_df], ignore_index=True)
        final_df = final_df[_ordered_columns(final_df.columns)]
    else:
        final_df = new_df

    final_df.to_excel(RESULTS_PATH, index=False)
    return True


def _translate_cell_to_english(value, cache):
    if pd.isna(value):
        return value

    if isinstance(value, (int, float, bool)):
        return value

    text = str(value).strip()
    if not text:
        return value

    if text in cache:
        return cache[text]

    translated = (translate_to_english_chunked(text) or "").strip()
    cache[text] = translated or text
    return cache[text]


def export_excel_in_english(source_path=RESULTS_PATH, output_path=RESULTS_EN_PATH):
    """
    Build an English copy of ivr_responses.xlsx by translating response cells.
    """
    if not os.path.exists(source_path):
        return None

    df = pd.read_excel(source_path)
    if df.empty:
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_excel(output_path, index=False)
        return output_path

    cache = {}
    for col in df.columns:
        if str(col).strip().lower() == "participant_id":
            continue
        df[col] = df[col].apply(lambda v: _translate_cell_to_english(v, cache))

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df.to_excel(output_path, index=False)
    return output_path
