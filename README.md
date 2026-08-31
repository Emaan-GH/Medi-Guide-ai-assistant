# MediGuide AI

An educational LangChain + Streamlit prototype for AI-powered medical symptom
guidance. **This is not a medical device and must never be used for real
diagnosis or treatment.**

## Features

- Patient intake form (age, gender, symptoms, duration, severity, existing
  conditions, medications, notes, answer language).
- Structured JSON guidance (summary, possible conditions, urgency level,
  next steps, doctor questions, warning signs) via `LLMChain` +
  `PromptTemplate`.
- A separate `ChatPromptTemplate` conversation streamed live into the UI
  with `st.write_stream`.
- Safe JSON parsing — malformed output never crashes the app.
- In-memory and SQLite caching, switchable from the sidebar.
- Safety disclaimers on every screen; emergency-level results are flagged
  clearly.

## Project Structure

```
medical_ai_assistant/
├── app.py                 # Streamlit UI - run this
├── requirements.txt
├── .env.example
├── README.md
└── src/
    ├── __init__.py
    ├── config.py           # settings + form options
    ├── prompts.py           # PromptTemplate + ChatPromptTemplate + JSON schema
    ├── chains.py            # ChatOpenAI, LLMChain, streaming, message-role demo
    ├── cache_manager.py     # in-memory + SQLite caching switches
    └── utils.py             # safe JSON parsing + helpers
```

## Setup

1. **Create a virtual environment and install dependencies**
   ```bash
   python -m venv venv
   source venv/bin/activate      # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Get an OpenAI API key**
   - Create an account at platform.openai.com and generate a key under
     *API keys*.

3. **Configure your secrets**
   ```bash
   cp .env.example .env
   ```
   Then edit `.env` and paste your real key:
   ```
   OPENAI_API_KEY=sk-...
   ```
   Never commit `.env` to version control — add it to `.gitignore`.

4. **Run the app**
   ```bash
   streamlit run app.py
   ```

## Caching: In-Memory vs SQLite

LangChain has a single global cache slot, registered with
`set_llm_cache(...)`. Every LLM call checks this cache first — if the exact
same prompt + model + parameters were seen before, LangChain returns the
saved answer instantly instead of calling the API again.

| | InMemoryCache | SQLiteCache |
|---|---|---|
| Stored in | RAM | A `.db` file on disk |
| Speed | Fastest | Fast, slightly slower (disk I/O) |
| Survives app restart? | ❌ No | ✅ Yes |
| Best for | Quick repeated tests in one session | Reusing answers across sessions/days, saving cost long-term |

Pick a cache mode in the sidebar, submit the form once, then submit the
**exact same** inputs again — the second run should be visibly faster
("Response time" shown at the top of the Guidance Dashboard tab).

## Testing Scenarios

| # | Input | Expected behaviour |
|---|---|---|
| 1 | Age 25, runny nose + sore throat, 1-3 days, severity 2 | Urgency LOW; calm monitoring advice |
| 2 | Age 40, fever + cough, 4-7 days, severity 6 | Urgency MEDIUM/HIGH; advises seeing a professional |
| 3 | Severe chest pain + shortness of breath | Urgency HIGH/EMERGENCY; urges immediate help |
| 4 | Submit the same form twice (cache on) | Second run is faster; identical result |
| 5 | Empty symptoms | App warns the user and does not call the API |
| 6 | Language = Urdu | Guidance text returns in Urdu |

## Disclaimer

MediGuide AI is a learning project only. It is not a substitute for
professional medical advice, diagnosis, or treatment. Always seek the advice
of a physician for any medical concern, and call emergency services for
urgent situations.
