"""Pre-flight check — verifies everything is in order before starting the server."""
import sys, os, io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
sys.path.insert(0, ".")

from dotenv import load_dotenv
load_dotenv()

print("=" * 50)
print("  AirGuard AI — Pre-flight Check")
print("=" * 50)

# ── Environment
key = os.environ.get("GROQ_API_KEY", "")
model = os.environ.get("GROQ_MODEL", "qwen/qwen3.8-27b")
port = os.environ.get("PORT", "5000")
db = os.environ.get("DB_PATH", "airguard.db")

print(f"\n[ENV]")
print(f"  GROQ_API_KEY : {'SET (' + key[:12] + '...)' if key else 'NOT SET — will use rule-based fallback'}")
print(f"  GROQ_MODEL   : {model}")
print(f"  PORT         : {port}")
print(f"  DB_PATH      : {db}")

# ── Files
required_files = [
    "run.py",
    "backend/app.py",
    "backend/agents/orchestrator.py",
    "backend/agents/chat_agent.py",
    "backend/agents/aqi_agent.py",
    "backend/agents/health_agent.py",
    "backend/agents/forecast_agent.py",
    "backend/agents/community_agent.py",
    "backend/rag/knowledge_base.py",
    "backend/models/database.py",
    "backend/data/mock_data.py",
    "frontend/templates/index.html",
    "frontend/static/css/style.css",
    "frontend/static/js/app.js",
    "langflow/airguard_workflow.json",
    "orchestrate/orchestrate_skills.json",
    "requirements.txt",
]

print(f"\n[FILES]")
all_ok = True
for f in required_files:
    exists = os.path.exists(f)
    status = "OK  " if exists else "MISSING"
    print(f"  [{status}] {f}")
    if not exists:
        all_ok = False

# ── Imports
print(f"\n[IMPORTS]")
try:
    from backend.app import app
    print("  [OK  ] Flask app")
except Exception as e:
    print(f"  [FAIL] Flask app: {e}")
    all_ok = False

try:
    from groq import Groq
    print("  [OK  ] groq SDK")
except Exception as e:
    print(f"  [FAIL] groq: {e}")
    all_ok = False

# ── Groq live ping
if key:
    print(f"\n[GROQ LIVE TEST]")
    try:
        import re
        client = Groq(api_key=key)
        r = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": "You are a helpful assistant."},
                {"role": "user",   "content": "Reply with exactly: Groq OK"}
            ],
            max_tokens=10, temperature=0
        )
        raw = r.choices[0].message.content.strip()
        clean = re.sub(r"<think>.*?</think>", "", raw, flags=re.DOTALL).strip()
        print(f"  [OK  ] Groq response: {clean}")
    except Exception as e:
        print(f"  [FAIL] Groq call: {e}")
        all_ok = False

# ── Flask endpoints test
print(f"\n[API ENDPOINTS]")
try:
    with app.test_client() as c:
        endpoints = [
            ("GET",  "/api/health",              None),
            ("GET",  "/api/aqi?city=bhilai",     None),
            ("GET",  "/api/forecast?city=bhilai",None),
            ("GET",  "/api/community?city=bhilai",None),
            ("POST", "/api/chat",                {"question":"What is AQI?","city":"bhilai"}),
            ("GET",  "/api/dashboard?city=bhilai",None),
            ("GET",  "/api/analytics",           None),
            ("GET",  "/api/cities",              None),
            ("GET",  "/",                        None),
        ]
        for method, url, body in endpoints:
            if method == "GET":
                resp = c.get(url)
            else:
                resp = c.post(url, json=body)
            ok = resp.status_code == 200
            print(f"  [{'OK  ' if ok else 'FAIL'}] {method} {url}  →  {resp.status_code}")
            if not ok:
                all_ok = False
except Exception as e:
    print(f"  [FAIL] Endpoint test: {e}")
    all_ok = False

print("\n" + "=" * 50)
if all_ok:
    print("  ALL CHECKS PASSED")
    print(f"  Run: python run.py")
    print(f"  Open: http://localhost:{port}")
else:
    print("  SOME CHECKS FAILED — see above")
print("=" * 50)
