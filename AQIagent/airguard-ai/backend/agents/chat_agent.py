"""
AI Chat Agent
Handles natural-language questions about air quality.

Priority:
  1. Groq (qwen/qwen3.8-27b) — fast, available on this key
  2. IBM watsonx (Granite) — if configured
  3. Rule-based + RAG fallback — always works offline
"""

import os
import re
from backend.rag.knowledge_base import search_knowledge


def _strip_thinking(text: str) -> str:
    """Remove <think>...</think> blocks that some models emit."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

# ── Groq config ──────────────────────────────────────
GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL   = os.environ.get("GROQ_MODEL", "qwen/qwen3.8-27b")

# ── IBM watsonx config (optional fallback) ────────────
IBM_WATSONX_URL        = os.environ.get("IBM_WATSONX_URL", "")
IBM_WATSONX_API_KEY    = os.environ.get("IBM_WATSONX_API_KEY", "")
IBM_WATSONX_PROJECT_ID = os.environ.get("IBM_WATSONX_PROJECT_ID", "")
IBM_MODEL_ID           = os.environ.get("IBM_MODEL_ID", "ibm/granite-13b-instruct-v2")

SYSTEM_PROMPT = (
    "You are AirGuard AI, a knowledgeable and friendly air quality assistant. "
    "Answer questions about AQI, air pollution, health precautions, pollutants, "
    "and community actions in simple, clear language. "
    "Always use the AQI context provided when answering. "
    "Keep answers concise (3-5 sentences). "
    "Never provide medical diagnoses. Always suggest consulting a doctor for personal health concerns."
)


# ── Groq LLM ─────────────────────────────────────────
def _try_groq(question: str, context: str, aqi_context: dict) -> str | None:
    """Call Groq API. Returns None if key not set or call fails."""
    if not GROQ_API_KEY:
        return None
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        aqi       = aqi_context.get("aqi", "N/A")
        city      = aqi_context.get("city", "your location")
        category  = aqi_context.get("category", "")
        main_poll = aqi_context.get("main_pollutant", "PM2.5")

        user_msg = (
            f"Current air quality context:\n"
            f"  City: {city}\n"
            f"  AQI: {aqi} ({category})\n"
            f"  Main Pollutant: {main_poll}\n\n"
            f"Relevant knowledge:\n{context}\n\n"
            f"User question: {question}"
        )

        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.5,
            max_tokens=350,
        )
        raw = completion.choices[0].message.content.strip()
        answer = _strip_thinking(raw)
        return answer if answer else None
    except Exception as e:
        print(f"[Groq] Error: {e}")
        return None


# ── IBM watsonx LLM ───────────────────────────────────
def _try_watsonx(question: str, context: str, aqi_context: dict) -> str | None:
    """Call IBM watsonx. Returns None if not configured or fails."""
    if not IBM_WATSONX_URL or not IBM_WATSONX_API_KEY:
        return None
    try:
        import requests
        aqi       = aqi_context.get("aqi", "N/A")
        city      = aqi_context.get("city", "your location")
        category  = aqi_context.get("category", "")
        main_poll = aqi_context.get("main_pollutant", "PM2.5")

        prompt = (
            f"{SYSTEM_PROMPT}\n\n"
            f"AQI Context: City={city}, AQI={aqi}, Category={category}, Main Pollutant={main_poll}\n\n"
            f"Knowledge:\n{context}\n\n"
            f"Question: {question}\nAnswer:"
        )
        headers = {
            "Authorization": f"Bearer {IBM_WATSONX_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model_id": IBM_MODEL_ID,
            "input": prompt,
            "parameters": {"decoding_method": "greedy", "max_new_tokens": 250},
            "project_id": IBM_WATSONX_PROJECT_ID,
        }
        resp = requests.post(
            f"{IBM_WATSONX_URL}/ml/v1/text/generation?version=2023-05-29",
            json=payload, headers=headers, timeout=15,
        )
        if resp.status_code == 200:
            generated = resp.json().get("results", [{}])[0].get("generated_text", "").strip()
            return generated or None
        return None
    except Exception:
        return None


# ── Rule-based fallback ───────────────────────────────
def _rule_based_answer(question: str, aqi_context: dict, kb_docs: list) -> str:
    aqi       = aqi_context.get("aqi", 0)
    city      = aqi_context.get("city", "your location")
    cat       = aqi_context.get("category", "Unknown")
    main_poll = aqi_context.get("main_pollutant", "PM2.5")
    q         = question.lower()
    kb_text   = " ".join([d["content"] for d in kb_docs[:2]]) if kb_docs else ""

    if any(w in q for w in ["exercise", "run", "jog", "workout", "sport", "outdoor activity"]):
        if aqi <= 50:
            return f"Today's AQI in {city} is {aqi} ({cat}) — great news! You can exercise outdoors freely. Enjoy your workout!"
        elif aqi <= 100:
            return f"AQI is {aqi} ({cat}) in {city}. Exercise is generally safe, but unusually sensitive individuals may want shorter sessions."
        elif aqi <= 150:
            return f"AQI is {aqi} ({cat}) in {city}. Sensitive groups should reduce outdoor exercise. If you're healthy, keep it brief and wear a mask."
        elif aqi <= 200:
            return f"AQI is {aqi} in {city} — Unhealthy. Move your workout indoors today. Exercising in polluted air increases the dose of pollutants you inhale significantly."
        else:
            return f"AQI is dangerously high ({aqi}) in {city}. Do NOT exercise outdoors. Exercise indoors or postpone entirely."

    if any(w in q for w in ["mean", "what is", "explain", "understand", "aqi"]):
        return (
            f"The current AQI in {city} is {aqi}, categorised as '{cat}'. "
            "AQI (Air Quality Index) measures air pollution on a scale of 0–500: "
            "0–50 Good, 51–100 Moderate, 101–150 Unhealthy for Sensitive Groups, "
            "151–200 Unhealthy, 201–300 Very Unhealthy, 301–500 Hazardous. "
            f"The main pollutant today is {main_poll}."
        )

    if any(w in q for w in ["precaution", "protect", "safe", "mask", "window"]):
        if aqi <= 100:
            return f"AQI is {aqi} in {city} — mostly safe. No special precautions needed today!"
        elif aqi <= 150:
            return f"AQI is {aqi} in {city}. Sensitive individuals should limit outdoor exposure. Consider a light mask and close windows during peak hours (11am–4pm)."
        else:
            return (
                f"AQI is {aqi} in {city} — take precautions! Wear an N95/KN95 mask outdoors, "
                "keep windows closed, use an air purifier indoors, and limit outdoor time."
            )

    if any(w in q for w in ["pm2.5", "pm25", "pm 2.5"]):
        return (
            "PM2.5 are fine particles ≤2.5 micrometers in diameter. They penetrate deep into the lungs "
            "and even enter the bloodstream. Long-term exposure is linked to heart disease, lung cancer, "
            f"and respiratory illnesses. Today in {city}, PM2.5 is a key concern."
        )

    if any(w in q for w in ["pm10"]):
        return (
            "PM10 are coarse particles ≤10 micrometers. They irritate the eyes, nose and throat "
            "and worsen respiratory conditions. Sources include road dust, construction, and industrial emissions."
        )

    if any(w in q for w in ["no2", "nitrogen"]):
        return (
            "NO2 (Nitrogen Dioxide) mainly comes from burning fuels in vehicles and power plants. "
            "It irritates airways and can aggravate asthma. It also contributes to smog formation."
        )

    if any(w in q for w in ["ozone", "o3"]):
        return (
            "Ground-level ozone (O3) forms when vehicle and industrial pollutants react in sunlight. "
            "It can cause chest pain, coughing, and airway inflammation. "
            "Children, the elderly, and those with lung disease are most vulnerable."
        )

    if any(w in q for w in ["community", "reduce pollution", "help", "contribute"]):
        return (
            f"Here's how the community in {city} can help: "
            "1) Use public transport or carpool. "
            "2) Avoid open burning of waste or crop stubble. "
            "3) Plant trees in your neighbourhood. "
            "4) Spread AQI awareness on social media. "
            "5) Report industrial violations to the Pollution Control Board."
        )

    if any(w in q for w in ["forecast", "tomorrow", "next", "predict"]):
        return (
            f"Check the Forecast section on the dashboard for the 5-day AQI prediction for {city}. "
            "The Forecasting Agent analyzes recent AQI trends to predict whether air quality "
            "will improve, stay the same, or worsen over the next few days."
        )

    if kb_text:
        return (
            f"Based on air quality guidance: {kb_text[:400]}...\n\n"
            f"Current AQI in {city}: {aqi} ({cat}). "
            "For personal medical advice, please consult a healthcare professional."
        )

    return (
        f"I can help with questions about AQI, PM2.5, PM10, NO2, O3, health precautions, "
        f"community actions, and forecasts for {city} (current AQI: {aqi}, {cat}). "
        "What would you like to know?"
    )


# ── Main entry point ──────────────────────────────────
def chat(question: str, aqi_context: dict = None) -> dict:
    """
    Chat pipeline:
      1. RAG retrieval from knowledge base
      2. Try Groq (llama-3.3-70b) — primary LLM
      3. Try IBM watsonx (Granite) — if Groq unavailable
      4. Rule-based fallback — always works
    """
    if aqi_context is None:
        aqi_context = {}

    # Step 1: RAG
    kb_docs = search_knowledge(question, top_k=3)
    context = "\n\n".join([f"[{d['topic']}] {d['content']}" for d in kb_docs])

    # Step 2: Groq
    answer = _try_groq(question, context, aqi_context)
    if answer:
        source = f"Groq ({GROQ_MODEL})"
    else:
        # Step 3: watsonx
        answer = _try_watsonx(question, context, aqi_context)
        if answer:
            source = "IBM watsonx (Granite)"
        else:
            # Step 4: Rule-based
            answer = _rule_based_answer(question, aqi_context, kb_docs)
            source = "AirGuard AI (Rule-based + RAG)"

    return {
        "question": question,
        "answer": answer,
        "source": source,
        "kb_sources": [{"topic": d["topic"], "id": d["id"]} for d in kb_docs],
        "disclaimer": "This is general health information, not medical advice. Consult a healthcare professional for personal health concerns.",
    }
