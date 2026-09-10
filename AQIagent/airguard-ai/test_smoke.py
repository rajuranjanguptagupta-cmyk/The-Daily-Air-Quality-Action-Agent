import sys, os
sys.path.insert(0, ".")
# Force UTF-8 for Windows console
if sys.stdout.encoding != "utf-8":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

from backend.data.mock_data import get_mock_aqi, get_available_cities
from backend.rag.knowledge_base import search_knowledge
from backend.agents.aqi_agent import fetch_aqi
from backend.agents.health_agent import get_recommendations
from backend.agents.forecast_agent import get_forecast
from backend.agents.community_agent import get_community_actions
from backend.agents.chat_agent import chat
from backend.agents.orchestrator import run_orchestrator
from backend.models.database import init_db, save_aqi_reading, get_analytics

errors = []

# 1. Orchestrator
result = run_orchestrator("delhi", "adult", "moderate", "none")
assert result["aqi_data"]["aqi"] > 0, "AQI should be positive"
assert "daily_plan" in result, "daily_plan missing"
assert len(result["health_advisory"]["recommendations"]) > 0, "recs empty"
print("[PASS] Orchestrator end-to-end")

# 2. Forecast
fc = get_forecast("raipur")
assert len(fc["forecast"]) == 5, "Expected 5 forecast days"
assert fc["trend"] in ("improving","worsening","stable")
print("[PASS] Forecast agent")

# 3. Community
comm = get_community_actions(180, "delhi")
assert len(comm["actions"]) > 0, "Community actions empty"
print("[PASS] Community agent")

# 4. Chat
c = chat("What does PM2.5 mean?", {"aqi": 170, "city": "Delhi", "category": "Unhealthy", "main_pollutant": "PM25"})
assert "answer" in c and len(c["answer"]) > 20
print("[PASS] Chat agent")

# 5. RAG
docs = search_knowledge("pm25 dangerous particles")
assert len(docs) > 0, "RAG returned no results"
print("[PASS] RAG knowledge base")

# 6. DB
init_db()
save_aqi_reading(result["aqi_data"])
analytics = get_analytics("Delhi")
assert analytics["total_readings"] >= 1
print("[PASS] Database")

# 7. All cities
cities = get_available_cities()
assert len(cities) == 4
print("[PASS] Mock data (4 cities)")

# 8. Flask test client
from backend.app import app
with app.test_client() as client:
    r = client.get("/api/aqi?city=bhilai")
    assert r.status_code == 200
    data = r.get_json()
    assert data["success"] is True
    assert data["data"]["aqi"] > 0
    print("[PASS] /api/aqi endpoint")

    r2 = client.get("/api/forecast?city=raipur")
    assert r2.status_code == 200
    assert r2.get_json()["success"] is True
    print("[PASS] /api/forecast endpoint")

    r3 = client.get("/api/community?city=delhi")
    assert r3.status_code == 200
    assert r3.get_json()["success"] is True
    print("[PASS] /api/community endpoint")

    r4 = client.post("/api/chat", json={"question": "Can I exercise outside?", "city": "bhilai"})
    assert r4.status_code == 200
    chat_resp = r4.get_json()
    assert chat_resp["success"] is True
    print("[PASS] /api/chat endpoint")

    r5 = client.get("/api/dashboard?city=mumbai")
    assert r5.status_code == 200
    assert r5.get_json()["success"] is True
    print("[PASS] /api/dashboard endpoint")

    r6 = client.get("/api/health")
    assert r6.status_code == 200
    print("[PASS] /api/health endpoint")

print("\n=============================")
print("  ALL TESTS PASSED")
print("=============================")
