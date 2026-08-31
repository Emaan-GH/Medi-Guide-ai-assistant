"""
app.py
------
MediGuide AI — Streamlit entry point.

Run with:  streamlit run app.py
"""

import time
import streamlit as st
import openai

from src import config
from src.cache_manager import apply_cache_choice, get_cache_mode
from src.chains import build_assessment_chain, stream_narrative, demo_message_roles
from src.utils import safe_parse_json, build_patient_summary_text, urgency_icon

st.set_page_config(page_title="MediGuide AI", page_icon="🩺", layout="wide")

# ---------------------------------------------------------------------------
# SESSION STATE DEFAULTS
# ---------------------------------------------------------------------------
if "api_key_verified" not in st.session_state:
    st.session_state.api_key_verified = False
if "verified_api_key" not in st.session_state:
    st.session_state.verified_api_key = ""


def test_api_key(key: str) -> tuple[bool, str]:
    """
    Makes a minimal, cheap call to OpenAI to confirm the key actually works.
    Returns (is_valid, error_message).
    """
    if not key or not key.strip():
        return False, "Please enter an API key."

    try:
        client = openai.OpenAI(api_key=key.strip())
        # Cheapest possible way to confirm the key is real & has access:
        # listing models does NOT consume completion tokens.
        client.models.list()
        return True, ""
    except openai.AuthenticationError:
        return False, "Invalid API key. Please check and try again."
    except openai.APIConnectionError:
        return False, "Could not connect to OpenAI. Check your internet connection."
    except Exception as e:
        return False, f"Key test failed: {e}"


# ---------------------------------------------------------------------------
# GATE SCREEN — shown until the API key is verified
# ---------------------------------------------------------------------------
if not st.session_state.api_key_verified:
    st.title("🩺 MediGuide AI")
    st.caption("AI-Powered Medical Symptom Assessment & Patient Guidance (Educational Prototype)")
    st.warning(config.MEDICAL_DISCLAIMER)

    st.subheader("🔑 Enter your OpenAI API key to continue")
    st.write(
        "Your key is used only for this session and is never saved to disk. "
        "We'll do a quick test to make sure it works before loading the app."
    )

    with st.form("api_key_gate_form"):
        entered_key = st.text_input(
            "OpenAI API key",
            type="password",
            placeholder="sk-...",
        )
        # Fall back to a key configured in .env, if present, as a pre-fill hint
        use_env_key = False
        if config.OPENAI_API_KEY:
            use_env_key = st.checkbox("Use the key configured in this app's .env file instead")

        verify_clicked = st.form_submit_button("Test key & Continue")

    if verify_clicked:
        key_to_test = config.OPENAI_API_KEY if use_env_key else entered_key
        with st.spinner("Testing your API key..."):
            is_valid, err = test_api_key(key_to_test)

        if is_valid:
            st.session_state.api_key_verified = True
            st.session_state.verified_api_key = key_to_test.strip()
            st.success("✅ API key verified! Loading the app...")
            st.rerun()
        else:
            st.error(f"❌ {err}")

    st.stop()  # Don't render anything below until the key is verified

# ---------------------------------------------------------------------------
# FROM HERE ON: key is verified — this is the original app
# ---------------------------------------------------------------------------
active_api_key = st.session_state.verified_api_key

with st.sidebar:
    st.title("🩺 MediGuide AI")
    st.caption("AI-Powered Medical Symptom Assessment & Patient Guidance (Educational Prototype)")

    st.warning(config.MEDICAL_DISCLAIMER)

    st.subheader("⚙️ Model Configuration")
    st.text(f"Model: {config.MODEL_NAME}")
    st.text(f"Temperature: {config.MODEL_TEMPERATURE}")

    st.subheader("🔑 API Key")
    st.success("Using verified API key for this session.")
    if st.button("Change API key"):
        st.session_state.api_key_verified = False
        st.session_state.verified_api_key = ""
        st.rerun()

    st.subheader("🌐 Answer Language")
    language = st.selectbox("Language", config.LANGUAGE_OPTIONS, key="language_select")

    st.subheader("⚡ Caching")
    cache_choice = st.selectbox(
        "Cache mode", ["None", "In-Memory", "SQLite"],
        help="In-Memory: fastest, cleared on restart. SQLite: saved to disk, "
             "survives restarts. Submit the same form twice to see the speed-up.",
    )
    apply_cache_choice(cache_choice)
    st.caption(f"Active cache: `{get_cache_mode()}`")

    with st.expander("ℹ️ About this prototype"):
        st.write(
            "MediGuide AI is a learning project built with LangChain and "
            "Streamlit. It demonstrates prompt engineering, structured JSON "
            "output, streaming, and caching. It is **not** a medical device."
        )

# ---------------------------------------------------------------------------
# MAIN AREA — disclaimer banner + intake form
# ---------------------------------------------------------------------------
st.title("MediGuide AI — Symptom Guidance Assistant")
st.info(config.MEDICAL_DISCLAIMER)

with st.form("patient_form"):
    col1, col2 = st.columns(2)
    with col1:
        age = st.text_input("Patient age", placeholder="e.g. 29")
        gender = st.selectbox("Gender", config.GENDER_OPTIONS)
        duration = st.selectbox("Duration of symptoms", config.DURATION_OPTIONS)
    with col2:
        severity = st.slider("Severity (1 = mild, 10 = severe)", 1, 10, 3)
        symptoms_selected = st.multiselect("Symptoms", config.SYMPTOM_OPTIONS)
        symptoms_extra = st.text_input("Other symptoms (free text, optional)")

    conditions = st.text_area("Existing medical conditions", placeholder="e.g. asthma, diabetes")
    medications = st.text_area("Current medications", placeholder="e.g. metformin 500mg")
    notes = st.text_area("Additional notes", placeholder="Anything else relevant")

    submitted = st.form_submit_button("Get Guidance")

# ---------------------------------------------------------------------------
# ON SUBMIT
# ---------------------------------------------------------------------------
if submitted:
    all_symptoms = symptoms_selected + (
        [s.strip() for s in symptoms_extra.split(",") if s.strip()] if symptoms_extra else []
    )

    if not all_symptoms:
        st.warning("Please select or enter at least one symptom before submitting.")
        st.stop()

    if not age.strip():
        st.warning("Please enter the patient's age.")
        st.stop()

    inputs = {
        "age": age,
        "gender": gender,
        "symptoms": ", ".join(all_symptoms),
        "duration": duration,
        "severity": severity,
        "conditions": conditions,
        "medications": medications,
        "notes": notes,
        "language": language,
    }

    tab_summary, tab_dashboard, tab_narrative, tab_debug = st.tabs(
        ["📋 Patient Summary", "📊 Guidance Dashboard", "📝 Narrative (streamed)", "🔧 Debug"]
    )

    with tab_summary:
        st.markdown(build_patient_summary_text(inputs))

    # --- Structured JSON assessment via LLMChain -----------------------
    start = time.time()
    chain = build_assessment_chain(api_key=active_api_key)
    raw_output = chain.run(**inputs)
    elapsed = time.time() - start

    data, error = safe_parse_json(raw_output)

    with tab_dashboard:
        st.caption(f"Response time: {elapsed:.2f}s (cache mode: {get_cache_mode()})")

        if error:
            st.error(f"Sorry, something went wrong reading the AI's response: {error}")
            with st.expander("Show raw AI output (for debugging)"):
                st.code(raw_output)
        else:
            urgency = data.get("urgency_level", "LOW").upper()
            icon = urgency_icon(urgency)

            col_a, col_b = st.columns([1, 3])
            with col_a:
                st.metric("Urgency Level", f"{icon} {urgency}")
            with col_b:
                st.write(data.get("summary", ""))

            if urgency == "EMERGENCY":
                st.error("🚨 This may be an EMERGENCY. Seek immediate medical help / call emergency services now.")
            elif urgency == "HIGH":
                st.error("🔴 High urgency — please see a healthcare professional promptly.")
            elif urgency == "MEDIUM":
                st.warning("🟠 Medium urgency — a check-up with a healthcare professional is recommended.")
            else:
                st.success("🟢 Low urgency — monitor symptoms and rest, but consult a professional if things worsen.")

            st.subheader("Possible Conditions (education only, not a diagnosis)")
            for cond in data.get("possible_conditions", []):
                with st.expander(cond.get("name", "Unnamed")):
                    st.write(cond.get("reason", ""))

            col_c, col_d = st.columns(2)
            with col_c:
                st.subheader("✅ Recommended Next Steps")
                for step in data.get("recommended_next_steps", []):
                    st.write(f"- {step}")

                st.subheader("❓ Questions for Your Doctor")
                for q in data.get("questions_for_doctor", []):
                    st.write(f"- {q}")

            with col_d:
                st.subheader("⚠️ Warning Signs — Seek Immediate Care If:")
                for sign in data.get("warning_signs", []):
                    st.write(f"- {sign}")

            st.warning(config.MEDICAL_DISCLAIMER)

    # --- Streamed human-readable narrative ------------------------------
    with tab_narrative:
        st.caption("Live-streamed narrative version of the guidance:")
        st.write_stream(stream_narrative(inputs, api_key=active_api_key))
        st.warning(config.MEDICAL_DISCLAIMER)

    # --- Debug tab: raw JSON + message-roles demo -----------------------
    with tab_debug:
        st.caption("Raw JSON returned by the LLMChain:")
        st.code(raw_output, language="json")

        if st.checkbox("Run System/Human/AI message demo"):
            convo = demo_message_roles(
                "In one sentence, what should someone with a mild headache do?",
                api_key=active_api_key,
            )
            for msg in convo:
                st.write(f"**{msg.__class__.__name__}:** {msg.content}")

else:
    st.caption("Fill in the form above and click **Get Guidance** to begin.")
