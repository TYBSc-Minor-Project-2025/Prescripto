"""
db.py
Simple SQLite wrapper used by schedule_creator.py.

API:
- create_schedule_table()
- insert_schedule_entry(datetime_obj, medicine, note)
- fetch_schedules()
"""

import sqlite3
from datetime import datetime
from typing import List, Tuple

DB_PATH = "data/prescripto.db"


def get_connection():
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    return conn


def create_schedule_table():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS schedule (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            reminder_at TIMESTAMP NOT NULL,
            medicine TEXT NOT NULL,
            note TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def insert_schedule_entry(reminder_at: datetime, medicine: str, note: str = None):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO schedule (reminder_at, medicine, note) VALUES (?, ?, ?)
    """, (reminder_at, medicine, note))
    conn.commit()
    conn.close()


def fetch_schedules(limit: int = 100) -> List[Tuple]:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT id, reminder_at, medicine, note FROM schedule ORDER BY reminder_at LIMIT ?", (limit,))
    rows = cur.fetchall()
    conn.close()
    return rows
