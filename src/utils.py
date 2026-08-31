"""
utils.py
--------
Small stateless helpers:

- strip_json_fences()   : removes accidental ```json ... ``` wrappers.
- safe_parse_json()     : never lets a bad LLM response crash the app.
- build_patient_summary_text(): a plain-text recap of what the user typed,
                                 shown in the "Patient Summary" tab.
"""

import json
import re

from src.config import REQUIRED_JSON_KEYS


def strip_json_fences(text: str) -> str:
    """Remove ```json / ``` fences and any leading/trailing junk around the
    JSON object, in case the model didn't follow instructions perfectly."""
    text = text.strip()
    text = re.sub(r"^```(?:json)?", "", text, flags=re.IGNORECASE).strip()
    text = re.sub(r"```$", "", text).strip()

    # If there's stray text before/after the JSON object, grab just the
    # outermost {...} block.
    match = re.search(r"\{.*\}", text, flags=re.DOTALL)
    if match:
        text = match.group(0)
    return text


def safe_parse_json(raw_text: str):
    """Try to parse the model's raw output into a dict.

    Returns (parsed_dict_or_None, error_message_or_None).
    Never raises — callers should check which of the two is not None.
    """
    cleaned = strip_json_fences(raw_text)

    try:
        data = json.loads(cleaned)
    except json.JSONDecodeError as exc:
        return None, f"Could not parse the AI's response as JSON ({exc})."

    missing = [key for key in REQUIRED_JSON_KEYS if key not in data]
    if missing:
        return None, f"AI response is missing expected fields: {', '.join(missing)}."

    return data, None


def build_patient_summary_text(inputs: dict) -> str:
    """Plain-text recap of the form inputs, for the Patient Summary tab."""
    return (
        f"**Age:** {inputs['age']}  \n"
        f"**Gender:** {inputs['gender']}  \n"
        f"**Symptoms:** {inputs['symptoms']}  \n"
        f"**Duration:** {inputs['duration']}  \n"
        f"**Severity:** {inputs['severity']}/10  \n"
        f"**Existing conditions:** {inputs['conditions'] or 'None reported'}  \n"
        f"**Current medications:** {inputs['medications'] or 'None reported'}  \n"
        f"**Additional notes:** {inputs['notes'] or 'None'}"
    )


def urgency_icon(level: str) -> str:
    icons = {"LOW": "🟢", "MEDIUM": "🟠", "HIGH": "🔴", "EMERGENCY": "🚨"}
    return icons.get(level.upper(), "⚪")
