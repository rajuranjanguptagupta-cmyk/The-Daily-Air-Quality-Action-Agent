"""
Live Groq integration test — uses the real API key from .env
"""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from dotenv import load_dotenv
load_dotenv()

from backend.app import app
from backend.agents.chat_agent import chat, GROQ_API_KEY, GROQ_MODEL
from backend.agents.orchestrator import run_orchestrator

print(f"Groq model  : {GROQ_MODEL}")
print(f"Key present : {'YES (' + GROQ_API_KEY[:12] + '...)' if GROQ_API_KEY else 'NO'}")
print()

# 1. Chat live test
print("--- Chat Agent (Groq live) ---")
resp = chat(
    "Can I exercise outside today?",
    {"aqi": 168, "city": "Raipur", "category": "Unhealthy", "main_pollutant": "PM25"}
)
print(f"Source : {resp['source']}")
print(f"Answer : {resp['answer'][:300]}")
print()

# 2. Orchestrator daily plan
print("--- Orchestrator Daily Plan (Groq live) ---")
result = run_orchestrator("delhi", "adult", "active", "moderate")
print(f"Plan source : {result['plan_source']}")
print(f"Daily Plan  : {result['daily_plan'][:400]}")
print()

# 3. Full API test via Flask
print("--- Flask API endpoints ---")
with app.test_client() as client:
    for city in ["bhilai", "delhi", "mumbai"]:
        r = client.get(f"/api/dashboard?city={city}&age_group=adult&activity=moderate&sensitivity=none")
        d = r.get_json()
        assert d["success"], f"dashboard failed for {city}"
        src = d["data"].get("plan_source", "?")
        aqi = d["data"]["aqi_data"]["aqi"]
        print(f"  {city:8s} AQI={aqi:3d}  Plan source={src}")

    # Chat endpoint
    r = client.post("/api/chat", json={
        "question": "What precautions should I take today?",
        "city": "delhi"
    })
    d = r.get_json()
    assert d["success"]
    print(f"\nChat source : {d['data']['source']}")
    print(f"Chat answer : {d['data']['answer'][:200]}")

print("\n=================================")
print("  ALL LIVE TESTS PASSED")
print("=================================")
