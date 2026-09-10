"""
RAG Knowledge Base for AirGuard AI.

Provides a simple in-memory retrieval system over curated air-quality guidance.
In production this would be backed by a vector store (e.g. Chroma / Milvus).
"""

import re

KNOWLEDGE_BASE = [
    # ----- AQI Categories -----
    {
        "id": "aqi_good",
        "topic": "AQI Categories",
        "content": (
            "AQI 0–50 is GOOD. Air quality is satisfactory and poses little or no risk. "
            "It is safe to be outdoors. All groups can enjoy normal outdoor activities."
        ),
        "keywords": ["good", "0-50", "safe", "satisfactory"],
    },
    {
        "id": "aqi_moderate",
        "topic": "AQI Categories",
        "content": (
            "AQI 51–100 is MODERATE. Air quality is acceptable, but some pollutants may "
            "cause moderate concern for a small number of unusually sensitive people. "
            "Sensitive individuals should consider limiting prolonged outdoor exertion."
        ),
        "keywords": ["moderate", "51-100", "acceptable", "sensitive"],
    },
    {
        "id": "aqi_usg",
        "topic": "AQI Categories",
        "content": (
            "AQI 101–150 is UNHEALTHY FOR SENSITIVE GROUPS. People with lung disease, "
            "older adults, children, and people who are active outdoors should reduce "
            "prolonged or heavy outdoor exertion. The general public is not likely to be affected."
        ),
        "keywords": ["unhealthy sensitive", "101-150", "children", "elderly", "lung disease"],
    },
    {
        "id": "aqi_unhealthy",
        "topic": "AQI Categories",
        "content": (
            "AQI 151–200 is UNHEALTHY. Everyone may begin to experience health effects. "
            "Members of sensitive groups may experience more serious health effects. "
            "Everyone should reduce prolonged or heavy outdoor exertion."
        ),
        "keywords": ["unhealthy", "151-200", "health effects", "reduce outdoor"],
    },
    {
        "id": "aqi_very_unhealthy",
        "topic": "AQI Categories",
        "content": (
            "AQI 201–300 is VERY UNHEALTHY. Health warnings of emergency conditions. "
            "The entire population is more likely to be affected. Sensitive groups should "
            "avoid all outdoor exertion. Everyone else should avoid prolonged outdoor exertion."
        ),
        "keywords": ["very unhealthy", "201-300", "emergency", "avoid outdoor"],
    },
    {
        "id": "aqi_hazardous",
        "topic": "AQI Categories",
        "content": (
            "AQI 301–500 is HAZARDOUS. Health alert: everyone may experience more serious "
            "health effects. Everyone should avoid all outdoor exertion. Wear N95 masks "
            "if you must go outside. Keep indoor air clean with air purifiers."
        ),
        "keywords": ["hazardous", "301-500", "health alert", "n95", "avoid all outdoor"],
    },
    # ----- Pollutants -----
    {
        "id": "pm25_info",
        "topic": "Pollutants",
        "content": (
            "PM2.5 are fine particulate matter with diameter ≤2.5 micrometers. "
            "They can penetrate deep into the lungs and even enter the bloodstream. "
            "Long-term exposure is linked to heart disease, stroke, lung cancer, and respiratory diseases. "
            "Sources include vehicle exhaust, industrial emissions, biomass burning, and dust."
        ),
        "keywords": ["pm2.5", "pm25", "fine particles", "particulate matter", "lung", "dangerous"],
    },
    {
        "id": "pm10_info",
        "topic": "Pollutants",
        "content": (
            "PM10 are coarse particles with diameter ≤10 micrometers. They can irritate the eyes, "
            "nose, and throat, and worsen respiratory conditions. Sources include road dust, "
            "construction sites, and industrial processes."
        ),
        "keywords": ["pm10", "coarse particles", "dust", "respiratory"],
    },
    {
        "id": "no2_info",
        "topic": "Pollutants",
        "content": (
            "NO2 (Nitrogen Dioxide) is produced mainly from burning fuels in vehicles and power plants. "
            "It irritates the airways in the lungs and can aggravate respiratory diseases such as asthma. "
            "It also contributes to smog and acid rain formation."
        ),
        "keywords": ["no2", "nitrogen dioxide", "vehicle", "asthma", "smog"],
    },
    {
        "id": "o3_info",
        "topic": "Pollutants",
        "content": (
            "O3 (Ground-level Ozone) is not emitted directly; it forms when pollutants from cars, "
            "power plants, and other sources react in sunlight. It can trigger chest pain, coughing, "
            "throat irritation, and airway inflammation. Children, elderly people, and those with "
            "lung diseases are especially vulnerable."
        ),
        "keywords": ["o3", "ozone", "ground level ozone", "sunlight", "chest pain", "coughing"],
    },
    {
        "id": "co_info",
        "topic": "Pollutants",
        "content": (
            "CO (Carbon Monoxide) is a colorless, odorless gas from incomplete combustion. "
            "At high concentrations it can cause serious health effects by reducing oxygen delivery "
            "to organs. Sources include vehicle exhaust and burning fuels indoors."
        ),
        "keywords": ["co", "carbon monoxide", "combustion", "vehicle exhaust"],
    },
    {
        "id": "so2_info",
        "topic": "Pollutants",
        "content": (
            "SO2 (Sulfur Dioxide) comes mainly from burning fossil fuels and smelting mineral ores. "
            "It can affect the respiratory system, cause irritation of the nose and throat, and "
            "worsen existing respiratory and cardiovascular disease. It also contributes to acid rain."
        ),
        "keywords": ["so2", "sulfur dioxide", "fossil fuels", "acid rain", "respiratory"],
    },
    # ----- Health Precautions -----
    {
        "id": "exercise_advice",
        "topic": "Health Precautions",
        "content": (
            "During high AQI days, reduce intensity and duration of outdoor exercise. "
            "Prefer indoor workouts. If you must exercise outside, do so in the early morning "
            "when ozone levels are lower, avoid heavily trafficked roads, and stay hydrated. "
            "Wear an N95 or KN95 mask when AQI exceeds 150."
        ),
        "keywords": ["exercise", "outdoor workout", "jogging", "running", "sport", "mask"],
    },
    {
        "id": "indoor_air",
        "topic": "Health Precautions",
        "content": (
            "To improve indoor air quality: keep windows closed during high pollution periods, "
            "use air purifiers with HEPA filters, maintain indoor plants, avoid smoking indoors, "
            "ventilate when outdoor air quality is good (early morning), and clean floors with "
            "a damp mop rather than dry sweeping."
        ),
        "keywords": ["indoor air", "windows", "purifier", "hepa", "ventilate", "indoors"],
    },
    {
        "id": "sensitive_groups",
        "topic": "Health Precautions",
        "content": (
            "Sensitive groups include: children under 14, adults over 65, pregnant women, people "
            "with heart disease, people with lung disease (asthma, COPD), and anyone who is ill. "
            "These groups should reduce outdoor activity at AQI >100 and avoid outdoor activity "
            "at AQI >150. Always consult a healthcare provider for personal medical advice."
        ),
        "keywords": ["sensitive", "children", "elderly", "pregnant", "asthma", "heart", "copd"],
    },
    # ----- Community Actions -----
    {
        "id": "community_transport",
        "topic": "Community Actions",
        "content": (
            "Reducing vehicle use is one of the most impactful community actions. Options include: "
            "carpooling with neighbours, using public transport (bus/metro), cycling or walking for "
            "short distances, switching to electric vehicles, and avoiding unnecessary engine idling."
        ),
        "keywords": ["carpool", "public transport", "cycling", "electric vehicle", "idle", "traffic"],
    },
    {
        "id": "community_burning",
        "topic": "Community Actions",
        "content": (
            "Open burning of waste, crop stubble, and leaves is a major source of PM2.5. "
            "Communities should promote composting, proper waste disposal, and alternatives to "
            "crop burning such as bio-decomposers. Avoid fireworks during high-AQI days."
        ),
        "keywords": ["burning", "waste", "crop stubble", "biomass", "compost", "fireworks"],
    },
    {
        "id": "community_green",
        "topic": "Community Actions",
        "content": (
            "Tree plantation drives can significantly improve local air quality over time. "
            "Native tree species absorb CO2 and filter particulates. Communities should maintain "
            "green belts around industrial areas and schools, and protect existing green cover."
        ),
        "keywords": ["tree", "plantation", "green", "park", "forest", "vegetation"],
    },
    {
        "id": "community_awareness",
        "topic": "Community Actions",
        "content": (
            "Community awareness campaigns help educate citizens about air pollution sources, "
            "effects, and solutions. Activities include: local workshops, social media campaigns, "
            "school programs, distributing informational materials, and engaging local government "
            "for better air-quality monitoring and regulation."
        ),
        "keywords": ["awareness", "campaign", "education", "school", "social media", "workshop"],
    },
    # ----- Public Policy -----
    {
        "id": "policy_general",
        "topic": "Policy & Awareness",
        "content": (
            "Air quality is regulated through national ambient air quality standards (NAAQS). "
            "In India, the Central Pollution Control Board (CPCB) sets and monitors these standards. "
            "Citizens can report violations, participate in public consultations, and vote for "
            "representatives who prioritize environmental policies."
        ),
        "keywords": ["policy", "cpcb", "naaqs", "regulation", "government", "standards"],
    },
]


def search_knowledge(query: str, top_k: int = 3) -> list:
    """Simple keyword-based retrieval from the knowledge base."""
    query_lower = query.lower()
    scored = []
    for doc in KNOWLEDGE_BASE:
        score = 0
        for kw in doc["keywords"]:
            if kw in query_lower:
                score += 2
        # also check content words
        words = re.findall(r"\w+", query_lower)
        for w in words:
            if len(w) > 3 and w in doc["content"].lower():
                score += 1
        if score > 0:
            scored.append((score, doc))
    scored.sort(key=lambda x: x[0], reverse=True)
    return [doc for _, doc in scored[:top_k]]


def get_all_topics() -> list:
    topics = {}
    for doc in KNOWLEDGE_BASE:
        topics.setdefault(doc["topic"], []).append(doc)
    return topics
