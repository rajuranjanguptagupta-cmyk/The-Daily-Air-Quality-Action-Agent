"""
Community Action Agent
Generates community-level recommendations based on AQI level and local context.
"""

COMMUNITY_ACTIONS_POOL = {
    "transport": [
        {
            "icon": "🚌",
            "title": "Use Public Transport",
            "detail": "Take the bus or metro instead of personal vehicles. One bus replaces ~40 cars on the road.",
        },
        {
            "icon": "🚗",
            "title": "Organise Carpooling",
            "detail": "Share rides with neighbours and colleagues heading the same direction. Apps like BlaBlaCar or WhatsApp groups can help coordinate.",
        },
        {
            "icon": "🚲",
            "title": "Cycle or Walk",
            "detail": "For trips under 3 km, consider walking or cycling. Zero emissions and great for health on clean-air days.",
        },
        {
            "icon": "⚡",
            "title": "Consider Electric Vehicles",
            "detail": "If buying or renting, choose electric or hybrid vehicles. They produce no tailpipe emissions.",
        },
        {
            "icon": "🏠",
            "title": "Work From Home",
            "detail": "On high-AQI days, encourage employers to allow remote work to reduce commuter traffic.",
        },
    ],
    "burning": [
        {
            "icon": "🚫",
            "title": "Stop Open Waste Burning",
            "detail": "Open burning of garbage, leaves, or crop residue produces heavy PM2.5. Use composting or authorised waste disposal instead.",
        },
        {
            "icon": "🌾",
            "title": "Avoid Crop Stubble Burning",
            "detail": "Use bio-decomposers, happy seeders, or other sustainable alternatives to burning agricultural waste.",
        },
        {
            "icon": "🎆",
            "title": "Minimise Fireworks",
            "detail": "Postpone or replace fireworks events on high-AQI days. Community light shows are a safer alternative.",
        },
    ],
    "green": [
        {
            "icon": "🌳",
            "title": "Plant Trees",
            "detail": "Organise neighbourhood tree-plantation drives. Native species like Neem and Peepal are excellent air purifiers.",
        },
        {
            "icon": "🌿",
            "title": "Maintain Green Belts",
            "detail": "Advocate for green buffer zones around schools, hospitals, and industrial areas.",
        },
        {
            "icon": "🏡",
            "title": "Rooftop & Balcony Gardens",
            "detail": "Grow air-purifying indoor plants (Spider Plant, Peace Lily, Boston Fern) at home.",
        },
    ],
    "awareness": [
        {
            "icon": "📢",
            "title": "Spread Air Quality Awareness",
            "detail": "Share AQI updates on community WhatsApp/Telegram groups. Educate neighbours about pollution sources.",
        },
        {
            "icon": "🏫",
            "title": "School Awareness Programs",
            "detail": "Engage schools to educate children about air quality. Children are powerful change agents in communities.",
        },
        {
            "icon": "📋",
            "title": "Petition for Better Monitoring",
            "detail": "Encourage local government to install more AQI monitoring stations and publish real-time data.",
        },
    ],
    "industrial": [
        {
            "icon": "🏭",
            "title": "Report Industrial Violations",
            "detail": "If you observe industries emitting excess smoke or dust, report to the Pollution Control Board.",
        },
        {
            "icon": "♻️",
            "title": "Support Clean Industry Initiatives",
            "detail": "Buy from companies with certified green or low-emission manufacturing practices.",
        },
    ],
}


def _select_actions(aqi: int, city: str) -> list:
    actions = []
    # Always include transport and awareness
    actions += COMMUNITY_ACTIONS_POOL["transport"][:2]
    actions += COMMUNITY_ACTIONS_POOL["awareness"][:1]

    if aqi > 100:
        actions += COMMUNITY_ACTIONS_POOL["burning"][:1]
        actions += COMMUNITY_ACTIONS_POOL["green"][:1]
    if aqi > 150:
        actions += COMMUNITY_ACTIONS_POOL["industrial"][:1]
        actions += COMMUNITY_ACTIONS_POOL["transport"][2:3]
    if aqi > 200:
        actions += COMMUNITY_ACTIONS_POOL["burning"][1:2]
        actions += COMMUNITY_ACTIONS_POOL["awareness"][1:2]

    # Deduplicate by title
    seen = set()
    unique = []
    for a in actions:
        if a["title"] not in seen:
            seen.add(a["title"])
            unique.append(a)
    return unique[:6]


def get_community_actions(aqi: int, city: str = "") -> dict:
    actions = _select_actions(aqi, city)

    if aqi <= 50:
        summary = "Air quality is good today. Keep up sustainable habits to maintain clean air."
    elif aqi <= 100:
        summary = "Air quality is acceptable. Small community actions today can prevent it from worsening."
    elif aqi <= 150:
        summary = "Air quality is concerning for sensitive groups. Community action can make a real difference."
    elif aqi <= 200:
        summary = "Air quality is unhealthy. Collective community effort is needed to reduce pollution sources."
    else:
        summary = (
            "Air quality is at a serious level. Urgent community and individual actions are required. "
            "Every action counts towards reducing pollution."
        )

    return {
        "summary": summary,
        "actions": actions,
        "total_actions": len(actions),
        "agent": "Community Action Agent",
    }
