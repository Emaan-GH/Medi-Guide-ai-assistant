"""
prompts.py
----------
All prompt engineering lives here so app.py and chains.py stay clean.

Contains:
- SYSTEM_PROMPT              : safety rules baked into every request.
- JSON_SCHEMA_INSTRUCTIONS   : tells the model the EXACT JSON shape to return.
- ASSESSMENT_PROMPT_TEMPLATE : a classic single-string PromptTemplate (legacy style).
- ASSESSMENT_CHAT_TEMPLATE   : a ChatPromptTemplate (System + Human) used by the JSON chain.
- NARRATIVE_CHAT_TEMPLATE    : a ChatPromptTemplate used for the streamed, human-readable narrative.
"""

from langchain.prompts import PromptTemplate
from langchain_core.prompts import ChatPromptTemplate

# ---------------------------------------------------------------------------
# 1) SYSTEM PROMPT — encodes the non-negotiable safety rules (section 17)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = """You are MediGuide AI, an educational medical-information assistant.

STRICT SAFETY RULES (never break these):
1. You are NOT a doctor and must NEVER present a confirmed diagnosis.
2. Always frame possible conditions as "possibilities for education only",
   never as certainties.
3. If symptoms suggest anything severe (e.g. chest pain, difficulty breathing,
   signs of stroke, severe bleeding, suicidal thoughts), the urgency_level
   MUST be "HIGH" or "EMERGENCY" and warning_signs must clearly say to seek
   immediate emergency care.
4. Keep the tone calm, clear, and reassuring — never alarmist, never dismissive.
5. Always recommend consulting a licensed healthcare professional.
6. You must reply in the language the user requested.
"""

# ---------------------------------------------------------------------------
# 2) JSON SCHEMA INSTRUCTIONS — forces structured output (section 10 & 16)
# ---------------------------------------------------------------------------
JSON_SCHEMA_INSTRUCTIONS = """Return ONLY valid JSON — no markdown fences, no commentary before or after —
matching EXACTLY this structure:

{{
  "summary": "one short paragraph summarizing the patient's situation",
  "possible_conditions": [
    {{"name": "condition name", "reason": "why this fits the symptoms, education only"}}
  ],
  "urgency_level": "LOW" | "MEDIUM" | "HIGH" | "EMERGENCY",
  "recommended_next_steps": ["step 1", "step 2"],
  "questions_for_doctor": ["question 1", "question 2"],
  "warning_signs": ["sign that means seek immediate care"]
}}
"""

# ---------------------------------------------------------------------------
# 3) PromptTemplate — a reusable single-string template (legacy / classic API)
#    Required by the assignment as a standalone demonstration of PromptTemplate.
# ---------------------------------------------------------------------------
ASSESSMENT_PROMPT_TEMPLATE = PromptTemplate(
    input_variables=[
        "age", "gender", "symptoms", "duration", "severity",
        "conditions", "medications", "notes", "language",
    ],
    template=(
        "Patient profile:\n"
        "- Age: {age}\n"
        "- Gender: {gender}\n"
        "- Symptoms: {symptoms}\n"
        "- Duration: {duration}\n"
        "- Severity (1-10): {severity}\n"
        "- Existing conditions: {conditions}\n"
        "- Current medications: {medications}\n"
        "- Additional notes: {notes}\n\n"
        "Please respond in {language}.\n\n"
        + JSON_SCHEMA_INSTRUCTIONS
    ),
)

# ---------------------------------------------------------------------------
# 4) ChatPromptTemplate — System + Human conversation used for the JSON call
# ---------------------------------------------------------------------------
ASSESSMENT_CHAT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        (
            "human",
            "Patient profile:\n"
            "- Age: {age}\n"
            "- Gender: {gender}\n"
            "- Symptoms: {symptoms}\n"
            "- Duration: {duration}\n"
            "- Severity (1-10): {severity}\n"
            "- Existing conditions: {conditions}\n"
            "- Current medications: {medications}\n"
            "- Additional notes: {notes}\n\n"
            "Please respond in {language}.\n\n" + JSON_SCHEMA_INSTRUCTIONS,
        ),
    ]
)

# ---------------------------------------------------------------------------
# 5) ChatPromptTemplate — used for the streamed, human-readable narrative
#    (plain text, not JSON, so it can be shown with a typing effect).
# ---------------------------------------------------------------------------
NARRATIVE_CHAT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        (
            "human",
            "Based on this patient profile, write a short, warm, plain-language "
            "narrative (4-6 sentences, no JSON, no markdown headers) explaining "
            "what the symptoms might generally indicate and reassuring the "
            "patient about next steps. Respond in {language}.\n\n"
            "- Age: {age}\n"
            "- Gender: {gender}\n"
            "- Symptoms: {symptoms}\n"
            "- Duration: {duration}\n"
            "- Severity (1-10): {severity}\n"
            "- Existing conditions: {conditions}\n"
            "- Current medications: {medications}\n"
            "- Additional notes: {notes}\n",
        ),
    ]
)
