
"""
schedule_creator.py
Create reminder schedules from parsed prescription data and save to the DB.
"""


from __future__ import annotations

import datetime as dt
import logging
from dataclasses import dataclass
from typing import Iterable, List, Protocol

logger = logging.getLogger(__name__)

@dataclass
class ScheduleEntry:
    medicine: str
    time: dt.datetime
    dose_label: str  # e.g. "morning", "afternoon", "night"
    notes: str = ""


class DBLike(Protocol):
    def insert_reminder(self, entry: ScheduleEntry) -> None: ...
    # You can extend this protocol if your db module has different APIs.


DOSE_SLOTS = ("morning", "afternoon", "night")


def _parse_dose_pattern(dose_pattern: str) -> List[int]:
    """
    Convert "1-0-1" → [1, 0, 1].
    """
    parts = dose_pattern.split("-")
    if len(parts) != 3:
        logger.warning("Unexpected dose pattern '%s', defaulting to '0-0-0'", dose_pattern)
        return [0, 0, 0]

    slots: List[int] = []
    for p in parts:
        try:
            slots.append(int(p))
        except ValueError:
            slots.append(0)
    return slots


def _default_times_for_day(base_date: dt.date) -> List[dt.datetime]:
    """
    Returns default times (08:00, 14:00, 20:00) for a given date.
    """
    return [
        dt.datetime.combine(base_date, dt.time(hour=8, minute=0)),
        dt.datetime.combine(base_date, dt.time(hour=14, minute=0)),
        dt.datetime.combine(base_date, dt.time(hour=20, minute=0)),
    ]


def generate_schedule_entries_for_medicine(
    med_name: str,
    dose_pattern: str,
    duration_days: int,
    fallback_instr: str = "",
    start_date: dt.date | None = None,
) -> List[ScheduleEntry]:
    """
    Generate a list of ScheduleEntry for the given medicine.

    Parameters
    ----------
    med_name:
        Name of the medicine.
    dose_pattern:
        String like "1-0-1" meaning morning/afternoon/night intakes per day.
    duration_days:
        For how many days this schedule should last.
    fallback_instr:
        Any extra notes/instructions.
    start_date:
        Starting date (default: today).

    Returns
    -------
    List[ScheduleEntry]
    """
    if duration_days <= 0:
        logger.warning(
            "duration_days is %d for %s, defaulting to 5 days",
            duration_days,
            med_name,
        )
        duration_days = 5

    if start_date is None:
        start_date = dt.date.today()

    logger.info(
        "Generating schedule for %s: pattern=%s, days=%d, start=%s",
        med_name,
        dose_pattern,
        duration_days,
        start_date,
    )

    slots = _parse_dose_pattern(dose_pattern)
    entries: List[ScheduleEntry] = []

    for day_offset in range(duration_days):
        current_date = start_date + dt.timedelta(days=day_offset)
        times = _default_times_for_day(current_date)

        for idx, count in enumerate(slots):
            if count <= 0:
                continue

            for _ in range(count):
                entry = ScheduleEntry(
                    medicine=med_name,
                    time=times[idx],
                    dose_label=DOSE_SLOTS[idx],
                    notes=fallback_instr,
                )
                entries.append(entry)

    logger.info("Generated %d schedule entries for %s", len(entries), med_name)
    return entries


def save_schedule_entries(db_module, entries: Iterable[ScheduleEntry]) -> int:
    """
    Persist schedule entries using the provided db module.

    The db module is expected to provide a function like:
        db.insert_reminder(medicine, time, dose_label, notes)

    Returns
    -------
    int
        Number of saved entries.
    """
    saved = 0
    for entry in entries:
        try:
            # Adapt this call to match your actual db API.
            db_module.insert_reminder(
                medicine=entry.medicine,
                remind_at=entry.time,
                slot=entry.dose_label,
                notes=entry.notes,
            )
            saved += 1
        except Exception as e:
            logger.error("Failed to save entry %s: %s", entry, e, exc_info=True)

    logger.info("Saved %d/%d schedule entries", saved, len(list(entries)))
    return saved