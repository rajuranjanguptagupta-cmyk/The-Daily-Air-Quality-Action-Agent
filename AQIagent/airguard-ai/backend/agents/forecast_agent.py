"""
Forecasting Agent
Analyzes recent AQI trends and predicts near-future air quality risk.
Uses mock/historical data when live forecast API is unavailable.
"""

import random
from datetime import datetime, timedelta
from backend.data.mock_data import get_mock_forecast, get_aqi_category, CITIES


def _trend_direction(values: list) -> str:
    if len(values) < 2:
        return "stable"
    delta = values[-1] - values[0]
    if delta > 20:
        return "worsening"
    elif delta < -20:
        return "improving"
    return "stable"


def _risk_label(aqi: int) -> str:
    if aqi <= 50:
        return "Low"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Elevated"
    elif aqi <= 200:
        return "High"
    elif aqi <= 300:
        return "Very High"
    return "Extreme"


def _preventive_action(trend: str, aqi_tomorrow: int) -> str:
    cat = get_aqi_category(aqi_tomorrow)
    base_cat = cat["label"]
    if trend == "worsening":
        return (
            f"Air quality is forecast to worsen (category: {base_cat}). "
            "Plan outdoor activities today rather than tomorrow. "
            "Prepare masks and keep indoor air clean. "
            "Sensitive individuals should arrange alternative indoor activities."
        )
    elif trend == "improving":
        return (
            f"Air quality is expected to improve (forecast: {base_cat}). "
            "You may plan outdoor activities for later in the week. "
            "Continue monitoring the forecast."
        )
    else:
        return (
            f"Air quality is expected to remain similar (forecast: {base_cat}). "
            "Maintain current precautions. "
            "Check the forecast again tomorrow morning."
        )


def get_forecast(city: str = "bhilai") -> dict:
    """
    Returns a 5-day AQI forecast.
    Currently uses demo data; connect to a real weather/AQI forecast API here.
    """
    forecast_days = get_mock_forecast(city)
    aqi_values = [d["aqi"] for d in forecast_days]
    trend = _trend_direction(aqi_values)

    today_aqi = aqi_values[0]
    tomorrow_aqi = aqi_values[1] if len(aqi_values) > 1 else today_aqi

    # Early warning
    warning = None
    if tomorrow_aqi > 150:
        warning = {
            "level": "⚠️ Early Warning",
            "message": (
                f"AQI is forecast to reach {tomorrow_aqi} tomorrow — '{get_aqi_category(tomorrow_aqi)['label']}'. "
                "Take preventive measures today."
            ),
        }
    elif tomorrow_aqi > 100:
        warning = {
            "level": "ℹ️ Advisory",
            "message": (
                f"AQI may reach {tomorrow_aqi} tomorrow. Sensitive groups should plan accordingly."
            ),
        }

    return {
        "city": city.title(),
        "forecast": forecast_days,
        "trend": trend,
        "today_aqi": today_aqi,
        "today_risk": _risk_label(today_aqi),
        "tomorrow_aqi": tomorrow_aqi,
        "tomorrow_risk": _risk_label(tomorrow_aqi),
        "preventive_action": _preventive_action(trend, tomorrow_aqi),
        "warning": warning,
        "note": "📊 Forecast based on historical patterns and demo data. Connect live weather API for real predictions.",
        "agent": "Forecasting Agent",
        "demo": True,
    }
