"""
Database models and setup for AirGuard AI.
Uses SQLite by default; configure DATABASE_URL for PostgreSQL.
"""

import os
import sqlite3
from datetime import datetime

DB_PATH = os.environ.get("DB_PATH", "airguard.db")


def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    """Create database tables if they don't exist."""
    conn = get_connection()
    c = conn.cursor()

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS aqi_readings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT NOT NULL,
            aqi INTEGER NOT NULL,
            category TEXT,
            pm25 REAL,
            pm10 REAL,
            no2 REAL,
            o3 REAL,
            co REAL,
            so2 REAL,
            recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS user_profiles (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            age_group TEXT,
            city TEXT,
            activity_level TEXT,
            sensitivity TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS alerts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            city TEXT,
            aqi INTEGER,
            level TEXT,
            message TEXT,
            generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    c.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            question TEXT,
            answer TEXT,
            source TEXT,
            asked_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
        """
    )

    conn.commit()
    conn.close()


def save_aqi_reading(data: dict):
    conn = get_connection()
    c = conn.cursor()
    poll = data.get("pollutants", {})
    c.execute(
        """
        INSERT INTO aqi_readings (city, aqi, category, pm25, pm10, no2, o3, co, so2)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            data.get("city", ""),
            data.get("aqi", 0),
            data.get("category", ""),
            poll.get("pm25", 0),
            poll.get("pm10", 0),
            poll.get("no2", 0),
            poll.get("o3", 0),
            poll.get("co", 0),
            poll.get("so2", 0),
        ),
    )
    conn.commit()
    conn.close()


def save_alert(city: str, aqi: int, level: str, message: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO alerts (city, aqi, level, message) VALUES (?, ?, ?, ?)",
        (city, aqi, level, message),
    )
    conn.commit()
    conn.close()


def get_analytics(city: str = None) -> dict:
    conn = get_connection()
    c = conn.cursor()
    if city:
        c.execute(
            """
            SELECT AVG(aqi) avg_aqi, MAX(aqi) max_aqi, MIN(aqi) min_aqi,
                   COUNT(*) total, AVG(pm25) avg_pm25, AVG(pm10) avg_pm10
            FROM aqi_readings WHERE city = ?
            """,
            (city,),
        )
    else:
        c.execute(
            """
            SELECT AVG(aqi) avg_aqi, MAX(aqi) max_aqi, MIN(aqi) min_aqi,
                   COUNT(*) total, AVG(pm25) avg_pm25, AVG(pm10) avg_pm10
            FROM aqi_readings
            """
        )
    row = c.fetchone()

    c.execute("SELECT COUNT(*) cnt FROM alerts" + (" WHERE city = ?" if city else ""), ([city] if city else []))
    alerts_count = c.fetchone()["cnt"]

    # Most common pollutant: whichever average is highest (pm25 vs pm10)
    avg_pm25 = row["avg_pm25"] or 0
    avg_pm10 = row["avg_pm10"] or 0
    most_common = "PM2.5" if avg_pm25 >= avg_pm10 else "PM10"

    # Recent trend (last 10)
    if city:
        c.execute(
            "SELECT aqi, recorded_at FROM aqi_readings WHERE city = ? ORDER BY recorded_at DESC LIMIT 10",
            (city,),
        )
    else:
        c.execute(
            "SELECT aqi, recorded_at FROM aqi_readings ORDER BY recorded_at DESC LIMIT 10"
        )
    recent = [{"aqi": r["aqi"], "time": r["recorded_at"]} for r in c.fetchall()]

    conn.close()
    return {
        "avg_aqi": round(row["avg_aqi"] or 0, 1),
        "max_aqi": row["max_aqi"] or 0,
        "min_aqi": row["min_aqi"] or 0,
        "total_readings": row["total"] or 0,
        "most_common_pollutant": most_common,
        "alerts_generated": alerts_count,
        "recent_trend": recent,
    }


def save_chat(session_id: str, question: str, answer: str, source: str):
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        "INSERT INTO chat_history (session_id, question, answer, source) VALUES (?, ?, ?, ?)",
        (session_id, question, answer, source),
    )
    conn.commit()
    conn.close()


def upsert_profile(profile: dict) -> int:
    conn = get_connection()
    c = conn.cursor()
    c.execute(
        """
        INSERT INTO user_profiles (name, age_group, city, activity_level, sensitivity)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            profile.get("name", ""),
            profile.get("age_group", "adult"),
            profile.get("city", ""),
            profile.get("activity_level", "moderate"),
            profile.get("sensitivity", "none"),
        ),
    )
    row_id = c.lastrowid
    conn.commit()
    conn.close()
    return row_id
