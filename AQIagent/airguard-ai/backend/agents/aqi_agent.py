"""
AQI Data Agent
Fetches real-time AQI data from OpenAQ or WAQI public API.
Falls back to mock data when the API is unavailable.
"""

import os
import requests
from datetime import datetime
from backend.data.mock_data import get_mock_aqi, get_aqi_category, get_main_pollutant

WAQI_TOKEN = os.environ.get("WAQI_TOKEN", "")
OPENAQ_BASE = "https://api.openaq.io/v2"


def _fetch_waqi(city: str) -> dict | None:
    """Attempt to fetch from WAQI (World Air Quality Index) API."""
    if not WAQI_TOKEN:
        return None
    try:
        url = f"https://api.waqi.info/feed/{city}/?token={WAQI_TOKEN}"
        resp = requests.get(url, timeout=6)
        data = resp.json()
        if data.get("status") != "ok":
            return None
        d = data["data"]
        iaqi = d.get("iaqi", {})
        pollutants = {
            "pm25": iaqi.get("pm25", {}).get("v", 0),
            "pm10": iaqi.get("pm10", {}).get("v", 0),
            "no2": iaqi.get("no2", {}).get("v", 0),
            "o3": iaqi.get("o3", {}).get("v", 0),
            "co": iaqi.get("co", {}).get("v", 0),
            "so2": iaqi.get("so2", {}).get("v", 0),
        }
        aqi = int(d.get("aqi", 0))
        cat = get_aqi_category(aqi)
        main_poll = get_main_pollutant(pollutants)
        return {
            "city": d.get("city", {}).get("name", city),
            "state": "",
            "aqi": aqi,
            "category": cat["label"],
            "color": cat["color"],
            "risk": cat["risk"],
            "emoji": cat["emoji"],
            "main_pollutant": main_poll.upper(),
            "pollutants": pollutants,
            "updated_at": datetime.utcnow().isoformat() + "Z",
            "source": "WAQI API",
            "demo": False,
        }
    except Exception:
        return None


def fetch_aqi(city: str = "bhilai") -> dict:
    """
    Main entry point for the AQI Data Agent.
    Returns AQI data from live API or falls back to mock data.
    """
    live = _fetch_waqi(city)
    if live:
        return live
    # Fallback
    result = get_mock_aqi(city)
    result["agent"] = "AQI Data Agent"
    return result


def interpret_aqi(data: dict) -> str:
    """Generate a plain-language interpretation of current AQI."""
    aqi = data["aqi"]
    category = data["category"]
    main = data.get("main_pollutant", "PM2.5")
    city = data.get("city", "your location")

    lines = [
        f"The current AQI in {city} is {aqi} — classified as '{category}'.",
    ]
    if aqi <= 50:
        lines.append(
            "The air quality is good today. It is safe to be outdoors and enjoy normal activities."
        )
    elif aqi <= 100:
        lines.append(
            "Air quality is acceptable. Unusually sensitive people may want to limit prolonged outdoor exertion."
        )
    elif aqi <= 150:
        lines.append(
            "Sensitive groups (children, elderly, those with respiratory conditions) should reduce prolonged "
            "outdoor activity. The general public is unlikely to be affected."
        )
    elif aqi <= 200:
        lines.append(
            "Everyone may begin to experience some health effects. Sensitive groups should reduce outdoor "
            "exertion significantly. Consider wearing a mask outdoors."
        )
    elif aqi <= 300:
        lines.append(
            "Health alert! Everyone should reduce outdoor activities. Sensitive groups should stay indoors. "
            "Keep windows closed and use air purifiers if available."
        )
    else:
        lines.append(
            "Emergency health conditions! Avoid all outdoor activities. Use N95 masks if you must go outside. "
            "Keep indoors with windows sealed and use air purifiers."
        )
    lines.append(f"The primary pollutant driving the AQI today is {main}.")
    return " ".join(lines)
