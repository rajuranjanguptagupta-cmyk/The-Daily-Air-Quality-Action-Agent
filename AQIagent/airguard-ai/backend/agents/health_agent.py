"""
Personalized Health Advisory Agent
Generates recommendations based on AQI level, user profile, and activity.

DISCLAIMER: Recommendations are general health guidance only.
Users should consult healthcare professionals for medical concerns.
"""

HEALTH_DISCLAIMER = (
    "⚠️ Disclaimer: These are general public-health guidelines, not medical advice. "
    "Please consult a qualified healthcare professional for personal medical concerns."
)

AGE_GROUPS = ["child", "teenager", "adult", "senior", "elderly"]
ACTIVITY_LEVELS = ["sedentary", "light", "moderate", "active", "athlete"]
SENSITIVITY = ["none", "mild", "moderate", "high", "very_high"]


def _base_recommendations(aqi: int) -> list:
    recs = []
    if aqi <= 50:
        recs += [
            "✅ Air quality is good. You can enjoy outdoor activities freely.",
            "✅ Great day for a walk, run, or outdoor exercise.",
            "✅ No special precautions needed today.",
        ]
    elif aqi <= 100:
        recs += [
            "✅ Air quality is acceptable for most people.",
            "🟡 Unusually sensitive individuals should consider limiting prolonged outdoor activity.",
            "🟡 Keep an eye on air quality trends throughout the day.",
        ]
    elif aqi <= 150:
        recs += [
            "🟠 Sensitive groups should reduce prolonged outdoor exertion.",
            "🟠 Children, elderly, and those with respiratory issues should limit outdoor time.",
            "🟠 Consider wearing a cloth or surgical mask when outdoors for extended periods.",
            "🟠 Keep outdoor windows partially closed during midday peak pollution.",
        ]
    elif aqi <= 200:
        recs += [
            "🔴 Reduce all prolonged and heavy outdoor exertion.",
            "🔴 Everyone should limit time outdoors, especially during active hours.",
            "🔴 Wear an N95 or KN95 mask if you must go outside.",
            "🔴 Keep indoor air clean — close windows and use air purifiers.",
            "🔴 Sensitive individuals should stay indoors.",
        ]
    elif aqi <= 300:
        recs += [
            "🟣 Avoid all outdoor activity — serious health risk for everyone.",
            "🟣 Stay indoors with windows and doors sealed.",
            "🟣 Use air purifiers with HEPA filters.",
            "🟣 Wear a properly fitted N95 mask if going outside is unavoidable.",
            "🟣 Keep sensitive individuals (children, elderly, ill) strictly indoors.",
            "🟣 Avoid cooking that produces indoor smoke.",
        ]
    else:
        recs += [
            "⚫ HAZARDOUS conditions. Do NOT go outdoors unless absolutely necessary.",
            "⚫ Wear N95 mask at all times if you must go outside.",
            "⚫ Seal gaps in doors and windows with damp cloth or tape.",
            "⚫ Run air purifiers continuously.",
            "⚫ Check on vulnerable neighbours and family members.",
            "⚫ Schools and outdoor workplaces should consider closure.",
        ]
    return recs


def _age_recs(aqi: int, age_group: str) -> list:
    extra = []
    age = age_group.lower() if age_group else "adult"
    if age in ("child", "teenager") and aqi > 100:
        extra.append("👶 Children and teens are especially vulnerable — keep outdoor play time short.")
    if age in ("senior", "elderly") and aqi > 100:
        extra.append("👴 Older adults should avoid all outdoor strenuous activity and stay in air-conditioned spaces if possible.")
    return extra


def _activity_recs(aqi: int, activity: str) -> list:
    extra = []
    act = activity.lower() if activity else "moderate"
    if act in ("active", "athlete") and aqi > 100:
        extra.append("🏃 Athletes and active individuals should move training sessions indoors.")
    if act == "moderate" and aqi > 150:
        extra.append("🚶 Even moderate outdoor activity carries health risk today. Take breaks and stay hydrated.")
    return extra


def _sensitivity_recs(aqi: int, sensitivity: str) -> list:
    extra = []
    sens = sensitivity.lower() if sensitivity else "none"
    if sens in ("moderate", "high", "very_high") and aqi > 100:
        extra.append("💊 Due to your health sensitivity, avoid outdoor exposure and ensure medications are accessible.")
    if sens == "very_high" and aqi > 50:
        extra.append("💊 With very high sensitivity, monitor your symptoms closely even on moderate AQI days.")
    return extra


def get_recommendations(
    aqi: int,
    age_group: str = "adult",
    activity: str = "moderate",
    sensitivity: str = "none",
    city: str = "",
) -> dict:
    recs = _base_recommendations(aqi)
    recs += _age_recs(aqi, age_group)
    recs += _activity_recs(aqi, activity)
    recs += _sensitivity_recs(aqi, sensitivity)

    # Determine go-outdoor verdict
    if aqi <= 100:
        verdict = "✅ Safe to go outdoors"
        verdict_color = "#00e400" if aqi <= 50 else "#b8b800"
    elif aqi <= 150:
        verdict = "🟠 Sensitive groups: limit outdoor time"
        verdict_color = "#ff7e00"
    elif aqi <= 200:
        verdict = "🔴 Reduce outdoor activity"
        verdict_color = "#ff0000"
    elif aqi <= 300:
        verdict = "🟣 Avoid outdoor activity"
        verdict_color = "#8f3f97"
    else:
        verdict = "⚫ Stay indoors — hazardous air"
        verdict_color = "#7e0023"

    return {
        "verdict": verdict,
        "verdict_color": verdict_color,
        "recommendations": recs,
        "disclaimer": HEALTH_DISCLAIMER,
        "profile": {
            "age_group": age_group,
            "activity": activity,
            "sensitivity": sensitivity,
            "city": city,
        },
        "agent": "Health Advisory Agent",
    }
