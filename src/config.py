"""
config.py
----------
Central place for:
1. Loading secrets (API key) from the .env file.
2. Holding constant options used by the Streamlit form (dropdown lists etc.)

Beginner note: We use python-dotenv's load_dotenv() so that the OPENAI_API_KEY
never has to be hard-coded anywhere in the source code. This keeps the key
out of GitHub if the developer remembers to add .env to .gitignore.
"""

import os
from dotenv import load_dotenv

# Load variables from a local .env file into the environment (if it exists).
load_dotenv()

# ---------------------------------------------------------------------------
# Secrets / model settings
# ---------------------------------------------------------------------------
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("MODEL_NAME", "gpt-4o-mini")
MODEL_TEMPERATURE = float(os.getenv("MODEL_TEMPERATURE", "0.3"))

# ---------------------------------------------------------------------------
# Form options (used to populate Streamlit widgets in app.py)
# ---------------------------------------------------------------------------
GENDER_OPTIONS = ["Female", "Male", "Other", "Prefer not to say"]

SYMPTOM_OPTIONS = [
    "Fever", "Cough", "Sore throat", "Runny nose", "Headache",
    "Fatigue", "Nausea", "Vomiting", "Diarrhea", "Abdominal pain",
    "Chest pain", "Shortness of breath", "Dizziness", "Rash",
    "Joint pain", "Muscle ache", "Loss of appetite", "Chills",
]

DURATION_OPTIONS = [
    "Less than a day", "1-3 days", "4-7 days", "1-2 weeks", "More than 2 weeks",
]

LANGUAGE_OPTIONS = ["English", "Urdu", "Spanish", "French", "Arabic"]

# Urgency levels the model is allowed to return, and the color used to render them.
URGENCY_COLORS = {
    "LOW": "green",
    "MEDIUM": "orange",
    "HIGH": "red",
    "EMERGENCY": "red",
}

# The exact JSON schema keys we expect back from the LLM (used by utils.py
# to validate the parsed response before rendering the dashboard).
REQUIRED_JSON_KEYS = [
    "summary",
    "possible_conditions",
    "urgency_level",
    "recommended_next_steps",
    "questions_for_doctor",
    "warning_signs",
]

MEDICAL_DISCLAIMER = (
    "⚠️ **MediGuide AI is an educational prototype, not a licensed doctor.** "
    "It does not provide a medical diagnosis. Always consult a qualified "
    "healthcare professional for real medical concerns. If this is an "
    "emergency, contact your local emergency number immediately."
)
