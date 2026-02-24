import sqlite3
from datetime import datetime
import json

DB_NAME = "pmp_app.db"


def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS attempts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT,
            mode TEXT,
            score INTEGER,
            total INTEGER,
            percentage REAL,
            domain_stats TEXT
        )
    """)

    conn.commit()
    conn.close()


def save_attempt(mode, score, total, domain_stats):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    percentage = (score / total) * 100

    cursor.execute("""
        INSERT INTO attempts (date, mode, score, total, percentage, domain_stats)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (
        datetime.now().strftime("%Y-%m-%d %H:%M"),
        mode,
        score,
        total,
        percentage,
        json.dumps(domain_stats)
    ))

    conn.commit()
    conn.close()


def get_attempts():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("SELECT date, mode, score, total, percentage, domain_stats FROM attempts")
    rows = cursor.fetchall()

    conn.close()

    attempts = []
    for row in rows:
        attempts.append({
            "date": row[0],
            "mode": row[1],
            "score": row[2],
            "total": row[3],
            "percentage": row[4],
            "domain_stats": json.loads(row[5]) if row[5] else {}
        })

    return attempts

