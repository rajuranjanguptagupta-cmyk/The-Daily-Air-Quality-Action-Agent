"""
Orchestrator / Supervisor Agent
Coordinates all sub-agents and combines their outputs into one
Daily Air Quality Action Plan.

Implements a simplified IBM Orchestrate-style multi-agent workflow.
Uses Groq (llama-3.3-70b) to generate a rich AI narrative when available.
"""

import os
from backend.agents.aqi_agent import fetch_aqi, interpret_aqi
from backend.agents.health_agent import get_recommendations
from backend.agents.forecast_agent import get_forecast
from backend.agents.community_agent import get_community_actions
from backend.rag.knowledge_base import search_knowledge

GROQ_API_KEY = os.environ.get("GROQ_API_KEY", "")
GROQ_MODEL   = os.environ.get("GROQ_MODEL", "qwen/qwen3.8-27b")


def _strip_thinking(text: str) -> str:
    import re
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

ORCHESTRATOR_SYSTEM = (
    "You are AirGuard AI's Orchestrator. "
    "Given air quality data, health recommendations, a forecast, and community actions, "
    "write a concise, friendly Daily Air Quality Action Plan in 5–7 sentences. "
    "Use simple language. Address the reader directly. "
    "Include: today's air quality situation, one key health tip, the forecast trend, "
    "and one community action. End with an encouraging sentence. "
    "Do NOT use bullet points or headers — write as flowing prose."
)


def _groq_daily_plan(aqi_data: dict, health: dict, forecast: dict, community: dict) -> str | None:
    """Generate a rich daily plan narrative using Groq."""
    if not GROQ_API_KEY:
        return None
    try:
        from groq import Groq
        client = Groq(api_key=GROQ_API_KEY)

        city     = aqi_data.get("city", "your city")
        aqi      = aqi_data["aqi"]
        cat      = aqi_data["category"]
        poll     = aqi_data.get("main_pollutant", "PM2.5")
        verdict  = health.get("verdict", "")
        top_rec  = health.get("recommendations", ["Stay safe."])[0]
        trend    = forecast.get("trend", "stable")
        tom_aqi  = forecast.get("tomorrow_aqi", aqi)
        comm_act = community.get("actions", [{}])[0].get("title", "use public transport")

        user_msg = (
            f"City: {city}\n"
            f"Today's AQI: {aqi} ({cat})\n"
            f"Main pollutant: {poll}\n"
            f"Health verdict: {verdict}\n"
            f"Top health tip: {top_rec}\n"
            f"Forecast trend: {trend} (tomorrow AQI ~{tom_aqi})\n"
            f"Top community action: {comm_act}\n\n"
            "Please write the Daily Air Quality Action Plan."
        )

        completion = client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": ORCHESTRATOR_SYSTEM},
                {"role": "user",   "content": user_msg},
            ],
            temperature=0.6,
            max_tokens=220,
        )
        raw  = completion.choices[0].message.content.strip()
        text = _strip_thinking(raw)
        return text if text else None
    except Exception as e:
        print(f"[Groq Orchestrator] Error: {e}")
        return None


def _build_policy_insights(aqi_data: dict, forecast: dict) -> dict:
    """Policy & Awareness Insights section."""
    aqi = aqi_data["aqi"]
    category = aqi_data["category"]
    main_poll = aqi_data.get("main_pollutant", "PM2.5")
    city = aqi_data.get("city", "your area")
    trend = forecast.get("trend", "stable")

    issue = f"Current AQI in {city} is {aqi} ({category}). Main pollutant: {main_poll}."

    if aqi <= 50:
        why = "Good air quality poses minimal risk to public health today."
        public_action = "Maintain sustainable practices. Enjoy the outdoors."
        community_action = "Share the good news and keep up green habits."
        awareness_msg = "Clean air is a public asset — protect it through daily choices."
    elif aqi <= 100:
        why = "Moderate pollution may affect unusually sensitive individuals."
        public_action = "Sensitive groups should monitor symptoms. Limit extended outdoor time if needed."
        community_action = "Encourage public transport use and carpooling in your neighbourhood."
        awareness_msg = "Every trip in a shared vehicle removes one more pollutant source from our air."
    elif aqi <= 150:
        why = (
            f"The elevated {main_poll} levels can irritate airways in children, elderly, "
            "and people with respiratory conditions."
        )
        public_action = "Sensitive groups should stay indoors during peak hours. Consider wearing a mask."
        community_action = "Reduce open burning, avoid unnecessary vehicle use, plant trees."
        awareness_msg = (
            "Air pollution doesn't just come from factories — every engine, every fire counts. "
            "Small changes at home and in commuting can reduce neighbourhood AQI."
        )
    elif aqi <= 200:
        why = (
            f"High {main_poll} concentration affects everyone's health — causing coughing, "
            "irritation, and reduced lung function."
        )
        public_action = "Everyone should limit outdoor activity. Wear N95 masks when outside."
        community_action = "Report open burning. Promote work-from-home policies. Organise community clean-up drives."
        awareness_msg = (
            "Unhealthy air quality is a community emergency. Share AQI alerts with your social networks and "
            "help vulnerable neighbours stay informed and safe."
        )
    else:
        why = (
            "Hazardous AQI levels can cause severe health effects for everyone, "
            "including healthy adults. This requires urgent collective action."
        )
        public_action = "Stay indoors. Avoid all outdoor activity. Seal windows. Use air purifiers."
        community_action = (
            "Contact local authorities to enforce emission controls. Advocate for school and office closures."
        )
        awareness_msg = (
            "This is a public health emergency. Support your community — check on elderly neighbours, "
            "share emergency contacts, and reduce all pollution sources immediately."
        )

    return {
        "current_issue": issue,
        "why_it_matters": why,
        "recommended_public_action": public_action,
        "community_action": community_action,
        "awareness_message": awareness_msg,
        "trend_note": (
            f"Air quality is trending {trend}. "
            + ("Take action now before it worsens." if trend == "worsening" else "Continue monitoring.")
        ),
    }


def _build_daily_plan(aqi_data: dict, health: dict, forecast: dict, community: dict) -> str:
    """Compose the final AI Daily Action Plan narrative."""
    city = aqi_data.get("city", "your location")
    aqi = aqi_data["aqi"]
    cat = aqi_data["category"]
    trend = forecast.get("trend", "stable")
    verdict = health.get("verdict", "")
    top_recs = health.get("recommendations", [])[:3]
    top_community = [a["title"] for a in community.get("actions", [])[:3]]

    plan = f"📍 {city} — AQI {aqi} ({cat})\n\n"

    if trend == "worsening":
        plan += "⚠️ Air quality is trending worse — take preventive action today.\n"
    elif trend == "improving":
        plan += "📈 Air quality is expected to improve — conditions may be better tomorrow.\n"
    else:
        plan += "📊 Air quality is stable — maintain current precautions.\n"

    plan += f"\n🔔 Today's Verdict: {verdict}\n\n"
    plan += "🩺 Health Actions:\n"
    for r in top_recs:
        plan += f"  • {r}\n"

    plan += "\n🌍 Community Actions:\n"
    for c in top_community:
        plan += f"  • {c}\n"

    plan += (
        "\n💡 Remember: Small individual actions, multiplied across a community, "
        "create large improvements in air quality. Stay informed, stay safe."
    )
    return plan


def run_orchestrator(
    city: str = "bhilai",
    age_group: str = "adult",
    activity: str = "moderate",
    sensitivity: str = "none",
) -> dict:
    """
    Main orchestration workflow — runs all agents and combines results.

    Workflow:
      1. AQI Data Agent  →  fetch AQI
      2. Health Advisory Agent  →  personalized recommendations
      3. Forecasting Agent  →  trend & risk prediction
      4. Community Action Agent  →  community recommendations
      5. Policy Insights  →  awareness narrative
      6. Daily Action Plan (Groq LLM → fallback rule-based)
    """

    # Step 1 — AQI Data Agent
    aqi_data = fetch_aqi(city)
    aqi_interpretation = interpret_aqi(aqi_data)
    aqi = aqi_data["aqi"]

    # Step 2 — Health Advisory Agent
    health = get_recommendations(
        aqi=aqi,
        age_group=age_group,
        activity=activity,
        sensitivity=sensitivity,
        city=city,
    )

    # Step 3 — Forecasting Agent
    forecast = get_forecast(city)

    # Step 4 — Community Action Agent
    community = get_community_actions(aqi=aqi, city=city)

    # Step 5 — Policy Insights
    policy = _build_policy_insights(aqi_data, forecast)

    # Step 6 — Daily Action Plan: try Groq first, fallback to rule-based
    groq_plan = _groq_daily_plan(aqi_data, health, forecast, community)
    if groq_plan:
        daily_plan = groq_plan
        plan_source = f"Groq ({GROQ_MODEL})"
    else:
        daily_plan = _build_daily_plan(aqi_data, health, forecast, community)
        plan_source = "AirGuard AI (Rule-based)"

    return {
        "status": "success",
        "city": city,
        "aqi_data": aqi_data,
        "aqi_interpretation": aqi_interpretation,
        "health_advisory": health,
        "forecast": forecast,
        "community": community,
        "policy_insights": policy,
        "daily_plan": daily_plan,
        "plan_source": plan_source,
        "workflow": {
            "name": "AirGuard AI Multi-Agent Workflow",
            "agents_run": [
                "AQI Data Agent",
                "Health Advisory Agent",
                "Forecasting Agent",
                "Community Action Agent",
                "Orchestrator / Supervisor Agent",
            ],
            "orchestrated_by": "IBM Orchestrate (simulated)",
            "llm": plan_source,
        },
    }
