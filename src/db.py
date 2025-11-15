
# filepath: /Users/anuragbhosale/Desktop/Projects/Prescripto/src/db.py
"""
db.py
SQLite helper utilities for Prescripto.
"""

from __future__ import annotations

import logging
import os
import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Iterator, Optional

logger = logging.getLogger(__name__)

# DB path can be overridden by environment variable
DB_PATH = Path(os.getenv("PRESCRIPTO_DB_PATH", "data/prescripto.db"))


@dataclass
class Reminder:
    id: Optional[int]
    medicine: str
    remind_at: datetime
    slot: str
    notes: str = ""


def _ensure_parent_dir(path: Path) -> None:
    if not path.parent.exists():
        path.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def get_conn() -> Iterator[sqlite3.Connection]:
    """
    Context manager that opens a connection and ensures it is closed.
    """
    _ensure_parent_dir(DB_PATH)
    conn = sqlite3.connect(DB_PATH)
    try:
        conn.row_factory = sqlite3.Row
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """
    Create the reminders table if it does not exist.
    """
    with get_conn() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS reminders (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                medicine TEXT NOT NULL,
                remind_at TEXT NOT NULL,
                slot TEXT NOT NULL,
                notes TEXT DEFAULT ''
            );
            """
        )
    logger.info("Database initialized at %s", DB_PATH)


def insert_reminder(
    medicine: str,
    remind_at,
    slot: str,
    notes: str = "",
) -> int:
    """
    Insert a reminder row and return its new ID.
    `remind_at` can be a datetime or ISO string.
    """
    if isinstance(remind_at, datetime):
        remind_at_str = remind_at.isoformat()
    else:
        remind_at_str = str(remind_at)

    with get_conn() as conn:
        cur = conn.execute(
            """
            INSERT INTO reminders (medicine, remind_at, slot, notes)
            VALUES (?, ?, ?, ?)
            """,
            (medicine, remind_at_str, slot, notes),
        )
        reminder_id = int(cur.lastrowid)
    logger.info(
        "Inserted reminder id=%d medicine=%s at %s (%s)",
        reminder_id,
        medicine,
        remind_at_str,
        slot,
    )
    return reminder_id


def get_upcoming_reminders(limit: int = 50):
    """
    Fetch upcoming reminders ordered by time.
    """
    with get_conn() as conn:
        cur = conn.execute(
            """
            SELECT id, medicine, remind_at, slot, notes
            FROM reminders
            ORDER BY remind_at ASC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()

    reminders = []
    for r in rows:
        reminders.append(
            Reminder(
                id=r["id"],
                medicine=r["medicine"],
                remind_at=datetime.fromisoformat(r["remind_at"]),
                slot=r["slot"],
                notes=r["notes"] or "",
            )
        )
    return reminders