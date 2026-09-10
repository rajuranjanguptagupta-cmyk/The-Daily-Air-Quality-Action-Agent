"""
Mock / demo AQI data for cities.
Used when live API is unavailable or in Demo Mode.
"""

import random
from datetime import datetime, timedelta

CITIES = {
    "bhilai": {
        "name": "Bhilai",
        "state": "Chhattisgarh",
        "lat": 21.2090,
        "lon": 81.4285,
        "base_aqi": 142,
        "pollutants": {
            "pm25": 62.4,
            "pm10": 98.1,
            "no2": 34.2,
            "o3": 41.0,
            "co": 1.2,
            "so2": 18.5,
        },
    },
    "raipur": {
        "name": "Raipur",
        "state": "Chhattisgarh",
        "lat": 21.2514,
        "lon": 81.6296,
        "base_aqi": 168,
        "pollutants": {
            "pm25": 78.3,
            "pm10": 121.0,
            "no2": 42.1,
            "o3": 38.5,
            "co": 1.8,
            "so2": 24.0,
        },
    },
    "delhi": {
        "name": "Delhi",
        "state": "Delhi",
        "lat": 28.6139,
        "lon": 77.2090,
        "base_aqi": 215,
        "pollutants": {
            "pm25": 110.5,
            "pm10": 178.2,
            "no2": 68.4,
            "o3": 52.3,
            "co": 2.9,
            "so2": 35.6,
        },
    },
    "mumbai": {
        "name": "Mumbai",
        "state": "Maharashtra",
        "lat": 19.0760,
        "lon": 72.8777,
        "base_aqi": 88,
        "pollutants": {
            "pm25": 38.1,
            "pm10": 62.4,
            "no2": 28.7,
            "o3": 44.9,
            "co": 0.9,
            "so2": 12.1,
        },
    },
}

DEFAULT_CITY = "bhilai"


def _jitter(value: float, pct: float = 0.08) -> float:
    """Add ±pct% random jitter to a value."""
    return round(value * (1 + random.uniform(-pct, pct)), 1)


def get_aqi_category(aqi: int) -> dict:
    if aqi <= 50:
        return {"label": "Good", "color": "#00e400", "risk": "Low", "emoji": "🟢"}
    elif aqi <= 100:
        return {"label": "Moderate", "color": "#ffff00", "risk": "Moderate", "emoji": "🟡"}
    elif aqi <= 150:
        return {
            "label": "Unhealthy for Sensitive Groups",
            "color": "#ff7e00",
            "risk": "Elevated",
            "emoji": "🟠",
        }
    elif aqi <= 200:
        return {"label": "Unhealthy", "color": "#ff0000", "risk": "High", "emoji": "🔴"}
    elif aqi <= 300:
        return {"label": "Very Unhealthy", "color": "#8f3f97", "risk": "Very High", "emoji": "🟣"}
    else:
        return {"label": "Hazardous", "color": "#7e0023", "risk": "Extreme", "emoji": "⚫"}


def get_main_pollutant(pollutants: dict) -> str:
    weights = {"pm25": 1.5, "pm10": 1.0, "no2": 0.9, "o3": 0.8, "co": 0.5, "so2": 0.7}
    scored = {k: v * weights.get(k, 1.0) for k, v in pollutants.items()}
    return max(scored, key=scored.get)


def get_mock_aqi(city_key: str = DEFAULT_CITY) -> dict:
    city_key = city_key.lower().strip()
    city = CITIES.get(city_key, CITIES[DEFAULT_CITY])
    aqi = int(_jitter(city["base_aqi"]))
    pollutants = {k: _jitter(v) for k, v in city["pollutants"].items()}
    category = get_aqi_category(aqi)
    main_pollutant = get_main_pollutant(pollutants)
    return {
        "city": city["name"],
        "state": city["state"],
        "aqi": aqi,
        "category": category["label"],
        "color": category["color"],
        "risk": category["risk"],
        "emoji": category["emoji"],
        "main_pollutant": main_pollutant.upper(),
        "pollutants": {
            "pm25": pollutants["pm25"],
            "pm10": pollutants["pm10"],
            "no2": pollutants["no2"],
            "o3": pollutants["o3"],
            "co": pollutants["co"],
            "so2": pollutants["so2"],
        },
        "updated_at": datetime.utcnow().isoformat() + "Z",
        "source": "Demo / Mock Data",
        "demo": True,
    }


def get_mock_forecast(city_key: str = DEFAULT_CITY) -> list:
    city_key = city_key.lower().strip()
    city = CITIES.get(city_key, CITIES[DEFAULT_CITY])
    base = city["base_aqi"]
    today = datetime.utcnow().date()
    forecast = []
    trend_delta = random.choice([-15, -8, 0, 10, 20])
    for i in range(5):
        day_aqi = int(max(10, _jitter(base + trend_delta * i * 0.4)))
        cat = get_aqi_category(day_aqi)
        forecast.append(
            {
                "date": (today + timedelta(days=i)).isoformat(),
                "label": ["Today", "Tomorrow", "Day 3", "Day 4", "Day 5"][i],
                "aqi": day_aqi,
                "category": cat["label"],
                "color": cat["color"],
                "risk": cat["risk"],
                "demo": True,
            }
        )
    return forecast


def get_available_cities() -> list:
    return [
        {"key": k, "name": v["name"], "state": v["state"]} for k, v in CITIES.items()
    ]
