"""
AirGuard AI — Flask Backend
Exposes all API endpoints consumed by the frontend.
"""

import os
import uuid
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv

load_dotenv()

# Import agents and DB
from backend.agents.orchestrator import run_orchestrator
from backend.agents.aqi_agent import fetch_aqi, interpret_aqi
from backend.agents.health_agent import get_recommendations
from backend.agents.forecast_agent import get_forecast
from backend.agents.community_agent import get_community_actions
from backend.agents.chat_agent import chat
from backend.models.database import (
    init_db,
    save_aqi_reading,
    save_alert,
    get_analytics,
    save_chat,
    upsert_profile,
)
from backend.data.mock_data import get_available_cities

app = Flask(
    __name__,
    static_folder="../frontend/static",
    template_folder="../frontend/templates",
)
CORS(app)

# -----------------------------------------------------------------
# Initialise DB on startup
# -----------------------------------------------------------------
with app.app_context():
    init_db()


# -----------------------------------------------------------------
# Serve frontend
# -----------------------------------------------------------------
@app.route("/")
def index():
    return send_from_directory("../frontend/templates", "index.html")


# -----------------------------------------------------------------
# /api/aqi  — AQI Data
# -----------------------------------------------------------------
@app.route("/api/aqi", methods=["GET"])
def api_aqi():
    city = request.args.get("city", "bhilai").lower().strip()
    try:
        data = fetch_aqi(city)
        interpretation = interpret_aqi(data)
        data["interpretation"] = interpretation
        # Persist to DB
        try:
            save_aqi_reading(data)
            if data["aqi"] > 150:
                save_alert(
                    city=data["city"],
                    aqi=data["aqi"],
                    level=data["category"],
                    message=interpretation,
                )
        except Exception:
            pass
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# -----------------------------------------------------------------
# /api/forecast  — 5-day forecast
# -----------------------------------------------------------------
@app.route("/api/forecast", methods=["GET"])
def api_forecast():
    city = request.args.get("city", "bhilai").lower().strip()
    try:
        data = get_forecast(city)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# -----------------------------------------------------------------
# /api/recommendation  — Health advisory
# -----------------------------------------------------------------
@app.route("/api/recommendation", methods=["GET", "POST"])
def api_recommendation():
    if request.method == "POST":
        body = request.get_json(silent=True) or {}
    else:
        body = request.args

    city = body.get("city", "bhilai")
    age_group = body.get("age_group", "adult")
    activity = body.get("activity", "moderate")
    sensitivity = body.get("sensitivity", "none")

    try:
        aqi_data = fetch_aqi(city)
        recs = get_recommendations(
            aqi=aqi_data["aqi"],
            age_group=age_group,
            activity=activity,
            sensitivity=sensitivity,
            city=city,
        )
        return jsonify({"success": True, "data": recs, "aqi": aqi_data["aqi"]})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# -----------------------------------------------------------------
# /api/community  — Community actions
# -----------------------------------------------------------------
@app.route("/api/community", methods=["GET"])
def api_community():
    city = request.args.get("city", "bhilai").lower().strip()
    try:
        aqi_data = fetch_aqi(city)
        data = get_community_actions(aqi=aqi_data["aqi"], city=city)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# -----------------------------------------------------------------
# /api/chat  — AI chatbot
# -----------------------------------------------------------------
@app.route("/api/chat", methods=["POST"])
def api_chat():
    body = request.get_json(silent=True) or {}
    question = (body.get("question") or "").strip()
    session_id = body.get("session_id") or str(uuid.uuid4())
    city = body.get("city", "bhilai")

    if not question:
        return jsonify({"success": False, "error": "Question is required."}), 400

    try:
        aqi_data = fetch_aqi(city)
        response = chat(question=question, aqi_context=aqi_data)
        # Save to history
        try:
            save_chat(session_id, question, response["answer"], response["source"])
        except Exception:
            pass
        return jsonify({"success": True, "data": response, "session_id": session_id})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# -----------------------------------------------------------------
# /api/dashboard  — Full orchestrated dashboard data
# -----------------------------------------------------------------
@app.route("/api/dashboard", methods=["GET"])
def api_dashboard():
    city = request.args.get("city", "bhilai").lower().strip()
    age_group = request.args.get("age_group", "adult")
    activity = request.args.get("activity", "moderate")
    sensitivity = request.args.get("sensitivity", "none")
    try:
        data = run_orchestrator(
            city=city,
            age_group=age_group,
            activity=activity,
            sensitivity=sensitivity,
        )
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# -----------------------------------------------------------------
# /api/analytics  — Admin analytics
# -----------------------------------------------------------------
@app.route("/api/analytics", methods=["GET"])
def api_analytics():
    city = request.args.get("city", None)
    try:
        data = get_analytics(city)
        return jsonify({"success": True, "data": data})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# -----------------------------------------------------------------
# /api/profile  — User profile
# -----------------------------------------------------------------
@app.route("/api/profile", methods=["POST"])
def api_profile():
    body = request.get_json(silent=True) or {}
    required = ["name", "age_group", "city"]
    for field in required:
        if not body.get(field):
            return jsonify({"success": False, "error": f"'{field}' is required."}), 400
    try:
        profile_id = upsert_profile(body)
        return jsonify({"success": True, "profile_id": profile_id, "message": "Profile saved."})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500


# -----------------------------------------------------------------
# /api/cities  — Available cities for demo
# -----------------------------------------------------------------
@app.route("/api/cities", methods=["GET"])
def api_cities():
    return jsonify({"success": True, "cities": get_available_cities()})


# -----------------------------------------------------------------
# Health check
# -----------------------------------------------------------------
@app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify(
        {
            "status": "ok",
            "service": "AirGuard AI Backend",
            "version": "1.0.0",
            "ibm_watsonx_configured": bool(os.environ.get("IBM_WATSONX_API_KEY")),
            "waqi_configured": bool(os.environ.get("WAQI_TOKEN")),
        }
    )


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    debug = os.environ.get("FLASK_DEBUG", "true").lower() == "true"
    app.run(host="0.0.0.0", port=port, debug=debug)
