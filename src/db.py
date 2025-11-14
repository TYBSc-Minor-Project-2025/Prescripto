from __future__ import annotations
import sqlite3
from pathlib import Path
from typing import Dict, Iterable, List, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "prescripto.db"


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    p = Path(db_path) if db_path else DB_PATH
    p.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(p))
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(conn: Optional[sqlite3.Connection] = None) -> None:
    own_conn = conn is None
    conn = conn or get_connection()
    try:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS medications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medicine_id INTEGER NOT NULL,
                "when" TEXT NOT NULL,
                time TEXT NOT NULL,
                start_date TEXT NOT NULL,
                end_date TEXT NOT NULL,
                message TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (medicine_id) REFERENCES medications(id) ON DELETE CASCADE
            );
            """
        )
        conn.commit()
    finally:
        if own_conn:
            conn.close()


def upsert_medicine(conn: sqlite3.Connection, name: str) -> int:
    cur = conn.execute("SELECT id FROM medications WHERE name = ?", (name,))
    row = cur.fetchone()
    if row:
        return int(row[0])
    cur = conn.execute("INSERT INTO medications(name) VALUES (?)", (name,))
    conn.commit()
    return int(cur.lastrowid)


def save_schedule(parsed: Dict, reminders: List[Dict], conn: Optional[sqlite3.Connection] = None) -> List[int]:
    own_conn = conn is None
    conn = conn or get_connection()
    try:
        med_id = upsert_medicine(conn, parsed.get("medicine") or "Unknown")
        ids: List[int] = []
        for r in reminders:
            cur = conn.execute(
                """
                INSERT INTO reminders(medicine_id, "when", time, start_date, end_date, message)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    med_id,
                    r.get("when"),
                    r.get("time"),
                    r.get("start_date"),
                    r.get("end_date"),
                    r.get("message"),
                ),
            )
            ids.append(int(cur.lastrowid))
        conn.commit()
        return ids
    finally:
        if own_conn:
            conn.close()


def list_reminders(conn: Optional[sqlite3.Connection] = None) -> List[Dict]:
    own_conn = conn is None
    conn = conn or get_connection()
    try:
        cur = conn.execute(
            """
            SELECT r.id, m.name as medicine, r."when", r.time, r.start_date, r.end_date, r.message
            FROM reminders r
            JOIN medications m ON m.id = r.medicine_id
            ORDER BY r.start_date, r.time
            """
        )
        cols = [c[0] for c in cur.description]
        rows = cur.fetchall()
        return [dict(zip(cols, row)) for row in rows]
    finally:
        if own_conn:
            conn.close()
