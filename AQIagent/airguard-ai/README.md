# 🛡️ AirGuard AI — Daily Air Quality Action Agent

> An AI-powered multi-agent web application that converts real-time AQI data into
> simple, personalized, and actionable daily recommendations.

---

## 📋 Table of Contents

1. [Project Overview](#project-overview)
2. [Features](#features)
3. [Architecture](#architecture)
4. [Folder Structure](#folder-structure)
5. [Prerequisites](#prerequisites)
6. [Installation & Setup](#installation--setup)
7. [Run Commands](#run-commands)
8. [API Reference](#api-reference)
9. [Environment Variables](#environment-variables)
10. [IBM Integration](#ibm-integration)
11. [Demo Mode](#demo-mode)
12. [Sample API Responses](#sample-api-responses)
13. [Component Explanations](#component-explanations)
14. [Security Notes](#security-notes)

---

## Project Overview

AirGuard AI is a complete, functional web application that:

- Fetches real-time AQI data for Indian cities
- Analyzes air quality with a multi-agent AI pipeline
- Provides personalized health advisories based on your profile
- Forecasts air quality for the next 5 days
- Suggests community-level actions to reduce pollution
- Answers natural-language questions via an AI chat assistant
- Integrates with IBM watsonx, IBM Langflow, and IBM Orchestrate

---

## Features

| Feature | Description |
|---|---|
| 🏙️ AQI Data Agent | Fetches live AQI from WAQI API, falls back to demo data |
| 🩺 Health Advisory Agent | Personalized recommendations per age/activity/sensitivity |
| 📅 Forecasting Agent | 5-day AQI trend prediction with early warnings |
| 🌍 Community Action Agent | Actionable community-level pollution-reduction tips |
| 🤖 Orchestrator Agent | IBM Orchestrate-style supervisor combining all agents |
| 💬 AI Chat Assistant | RAG + IBM watsonx powered Q&A chatbot |
| 📊 Analytics Dashboard | AQI statistics, trend charts |
| 🏗️ Architecture View | Visual IBM integration diagram |
| 🌙 Dark Mode | Full dark/light theme support |
| 📱 Responsive Design | Mobile-friendly layout |

---

## Architecture

```
User Browser (HTML/CSS/JS + Chart.js)
         ↓  REST API calls
Flask Backend (Python)
         ↓
IBM Orchestrate  ← coordinates all agents
         ↓
┌──────────────┬──────────────┬──────────────┬──────────────┐
│  AQI Agent   │ Health Agent │ Forecast Agent│Community Agent│
└──────┬───────┴──────┬───────┴──────┬────────┴──────┬───────┘
       └──────────────┴──────────────┴───────────────┘
                              ↓
                    IBM Langflow Workflow
                              ↓
              IBM watsonx / Granite-13B (LLM reasoning)
                              ↓
            AQI API  +  RAG Knowledge Base  +  SQLite DB
                              ↓
                   Daily AI Action Plan → Dashboard
```

---

## Folder Structure

```
airguard-ai/
├── run.py                          ← Entry point
├── requirements.txt
├── .env.example                    ← Copy to .env and configure
│
├── backend/
│   ├── app.py                      ← Flask app + all API endpoints
│   ├── agents/
│   │   ├── aqi_agent.py            ← AQI Data Agent
│   │   ├── health_agent.py         ← Personalized Health Advisory Agent
│   │   ├── forecast_agent.py       ← Forecasting Agent
│   │   ├── community_agent.py      ← Community Action Agent
│   │   ├── chat_agent.py           ← AI Chat Agent (RAG + watsonx)
│   │   └── orchestrator.py         ← Orchestrator / Supervisor Agent
│   ├── rag/
│   │   └── knowledge_base.py       ← In-memory RAG knowledge base
│   ├── models/
│   │   └── database.py             ← SQLite models + queries
│   └── data/
│       └── mock_data.py            ← Demo / fallback AQI data
│
├── frontend/
│   ├── templates/
│   │   └── index.html              ← Main dashboard page
│   └── static/
│       ├── css/style.css           ← Complete stylesheet (light+dark)
│       └── js/app.js               ← Frontend application logic
│
├── langflow/
│   └── airguard_workflow.json      ← IBM Langflow workflow definition
│
└── orchestrate/
    └── orchestrate_skills.json     ← IBM Orchestrate skill definitions
```

---

## Prerequisites

- **Python 3.10+**
- **pip**
- Modern web browser (Chrome, Firefox, Edge)
- (Optional) WAQI API token — free at https://aqicn.org/data-platform/token/
- (Optional) IBM Cloud account for watsonx, Langflow, Orchestrate

---

## Installation & Setup

### 1. Clone / Navigate to the project

```bash
cd airguard-ai
```

### 2. Create a virtual environment

```bash
python -m venv venv

# Activate (Windows PowerShell):
.\venv\Scripts\Activate.ps1

# Activate (macOS/Linux):
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

```bash
# Windows:
copy .env.example .env

# macOS/Linux:
cp .env.example .env
```

Edit `.env` and add your API keys (all optional — the app runs in Demo Mode without them).

---

## Run Commands

### Start the application

```bash
python run.py
```

Then open your browser at: **http://localhost:5000**

### Run with custom port

```bash
PORT=8080 python run.py
```

---

## API Reference

All endpoints return JSON `{ "success": true/false, "data": {...} }`.

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/aqi?city=bhilai` | Fetch current AQI for a city |
| GET | `/api/forecast?city=bhilai` | 5-day AQI forecast |
| GET/POST | `/api/recommendation` | Personalized health advisory |
| GET | `/api/community?city=bhilai` | Community action suggestions |
| POST | `/api/chat` | AI chat assistant |
| GET | `/api/dashboard?city=bhilai` | Full orchestrated dashboard data |
| GET | `/api/analytics?city=bhilai` | AQI statistics |
| POST | `/api/profile` | Save user profile |
| GET | `/api/cities` | List available demo cities |
| GET | `/api/health` | Backend health check |

### POST /api/chat — Request Body

```json
{
  "question": "Can I exercise outside today?",
  "city": "bhilai",
  "session_id": "optional-session-id"
}
```

### POST /api/recommendation — Request Body

```json
{
  "city": "delhi",
  "age_group": "adult",
  "activity": "active",
  "sensitivity": "moderate"
}
```

---

## Environment Variables

| Variable | Required | Description |
|---|---|---|
| `WAQI_TOKEN` | Optional | WAQI API token for live AQI data |
| `IBM_WATSONX_URL` | Optional | IBM watsonx regional endpoint |
| `IBM_WATSONX_API_KEY` | Optional | IBM Cloud API key |
| `IBM_WATSONX_PROJECT_ID` | Optional | watsonx project ID |
| `IBM_MODEL_ID` | Optional | Model ID (default: granite-13b-instruct-v2) |
| `DB_PATH` | Optional | SQLite file path (default: airguard.db) |
| `PORT` | Optional | Server port (default: 5000) |
| `FLASK_DEBUG` | Optional | Enable debug mode (default: true) |

---

## IBM Integration

### IBM watsonx

When `IBM_WATSONX_API_KEY` is set, the Chat Agent sends prompts to IBM Granite
models for LLM-powered answers. Without the key, rule-based + RAG answers are used.

### IBM Langflow

The file `langflow/airguard_workflow.json` is a complete workflow definition.
Import it into [IBM Langflow](https://langflow.ibm.com) to visualize and run
the multi-agent pipeline visually.

### IBM Orchestrate

The file `orchestrate/orchestrate_skills.json` defines all skills and automations.
Import into [IBM Orchestrate](https://www.ibm.com/products/ibm-orchestrate) to:
- Register each agent endpoint as a skill
- Configure scheduled daily AQI report automations
- Set up AQI alert triggers

---

## Demo Mode

AirGuard AI runs fully in **Demo Mode** without any API keys.

Demo data is available for:
- **Bhilai** (AQI ~142, Unhealthy for Sensitive Groups)
- **Raipur** (AQI ~168, Unhealthy)
- **Delhi** (AQI ~215, Very Unhealthy)
- **Mumbai** (AQI ~88, Moderate)

Each refresh adds ±8% random variation to keep the demo realistic.
Demo data is clearly labeled with a **📊 Demo Data** badge.

---

## Sample API Responses

### GET /api/aqi?city=bhilai

```json
{
  "success": true,
  "data": {
    "city": "Bhilai",
    "aqi": 142,
    "category": "Unhealthy for Sensitive Groups",
    "risk": "Elevated",
    "main_pollutant": "PM25",
    "pollutants": { "pm25": 62.4, "pm10": 98.1, "no2": 34.2, "o3": 41.0, "co": 1.2, "so2": 18.5 },
    "color": "#ff7e00",
    "demo": true,
    "source": "Demo / Mock Data",
    "interpretation": "The current AQI in Bhilai is 142 — classified as 'Unhealthy for Sensitive Groups'..."
  }
}
```

### POST /api/chat

```json
{
  "success": true,
  "data": {
    "question": "Can I exercise outside today?",
    "answer": "AQI is 142 in Bhilai — Unhealthy for Sensitive Groups. Sensitive groups should reduce outdoor exercise. If you're healthy, keep it brief and wear a mask.",
    "source": "AirGuard AI (Rule-based + RAG)",
    "disclaimer": "This is general information, not medical advice."
  }
}
```

---

## Component Explanations

### AQI Data Agent (`backend/agents/aqi_agent.py`)
Fetches AQI from WAQI API when token is available. Falls back to realistic mock data.
Provides a plain-language interpretation of the AQI number.

### Health Advisory Agent (`backend/agents/health_agent.py`)
Generates tiered health recommendations based on AQI level, age group, activity level,
and health sensitivity. Always includes the health disclaimer.

### Forecasting Agent (`backend/agents/forecast_agent.py`)
Builds a 5-day forecast using mock trend data. Detects whether AQI is improving,
worsening, or stable. Issues early warnings for high-AQI days.

### Community Action Agent (`backend/agents/community_agent.py`)
Selects and returns community actions from a curated pool, prioritizing the most
relevant categories based on current AQI severity.

### Orchestrator (`backend/agents/orchestrator.py`)
Supervisor agent that calls all sub-agents in sequence, builds the Policy Insights
narrative, and compiles the final Daily Action Plan text.

### Chat Agent (`backend/agents/chat_agent.py`)
RAG retrieval → IBM watsonx call → rule-based fallback.
Maintains conversation context per session.

### RAG Knowledge Base (`backend/rag/knowledge_base.py`)
In-memory keyword-scored retrieval over 20 curated air-quality guidance documents
covering AQI categories, pollutants, health precautions, community actions, and policy.

### Database (`backend/models/database.py`)
SQLite tables: `aqi_readings`, `user_profiles`, `alerts`, `chat_history`.
Stores all readings for analytics and trend charts.

---

## Security Notes

- ✅ API keys stored in `.env`, never in source code
- ✅ `.env` excluded from version control (add to `.gitignore`)
- ✅ Input validation on all endpoints
- ✅ No sensitive medical data collected
- ✅ CORS configured for local development
- ✅ No external URLs in frontend JS

---

*Built for the AirGuard AI Hackathon — IBM × AI for Good*
