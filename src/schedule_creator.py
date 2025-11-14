"""
schedule_creator.py
Schedule for creator

Responsibilities:
- Map parsed dosage patterns (e.g. "1-0-1", "twice a day") to concrete times.
- Generate full reminder schedule for N days starting from a start date.
- Create cron-like job entries (Unix) or return time entries for Task Scheduler (Windows).
- Save schedule via provided DB interface (db.save_schedule_entries).
- Provide robust defaults and validation.

Design goals:
- Clear public API
- Pure functions where possible
- Docstrings and type hints for easy explanation
"""

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, date, time, timedelta
from typing import List, Optional, Tuple, Dict
import re
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)


# -----------------------
# Data classes / types
# -----------------------
@dataclass
class MedicineSchedule:
    medicine: str
    dose_pattern: str              # e.g., "1-0-1", "1 tab daily", "twice a day"
    duration_days: int             # number of days
    start_date: date               # when schedule begins
    times: List[time]              # concrete times (per day)
    notes: Optional[str] = None    # free-text instructions


# -----------------------
# Defaults & constants
# -----------------------
# Common time-of-day presets (you can tweak to local conventions)
DEFAULT_MORNING = time(hour=8, minute=0)
DEFAULT_AFTERNOON = time(hour=13, minute=0)
DEFAULT_EVENING = time(hour=18, minute=0)
DEFAULT_NIGHT = time(hour=21, minute=0)

# Mapping of tokens -> time slots
TIME_TOKEN_MAP: Dict[str, time] = {
    "morning": DEFAULT_MORNING,
    "afternoon": DEFAULT_AFTERNOON,
    "evening": DEFAULT_EVENING,
    "night": DEFAULT_NIGHT,
    "noon": time(hour=12, minute=0),
}


# -----------------------
# Utility functions
# -----------------------
def normalize_text(s: str) -> str:
    """Lowercase and strip redundant spaces for pattern matching."""
    return re.sub(r"\s+", " ", s.strip().lower())


def parse_numeric_pattern(pattern: str) -> Optional[List[int]]:
    """
    Parse patterns like '1-0-1', '1-1-1', '0-1-0' into list of integers.
    Returns None if pattern not matched.
    """
    pattern = pattern.strip()
    m = re.match(r"^([0-9])\-([0-9])\-([0-9])$", pattern)
    if m:
        return [int(m.group(i)) for i in range(1, 4)]
    return None


def map_counts_to_times(counts: List[int]) -> List[time]:
    """
    Given [a,b,c] mapping to morning/afternoon/night counts (1 or 0),
    return concrete times in order (morning -> afternoon -> night).
    """
    slots = []
    mapping = [DEFAULT_MORNING, DEFAULT_AFTERNOON, DEFAULT_NIGHT]
    for count, slot in zip(counts, mapping):
        if count and slot not in slots:
            slots.append(slot)
    return slots


def estimate_times_from_text(instr: str) -> List[time]:
    """
    Heuristically infer times from free text like 'twice a day', 'once daily', 'every 6 hours',
    or 'after food in the morning'.
    Returns list of times (may be empty).
    """
    s = normalize_text(instr)
    # Common phrases
    if "once" in s or "once a day" in s or "daily" in s and "twice" not in s:
        return [DEFAULT_MORNING]
    if "twice" in s or "two times" in s or "2 times" in s:
        return [DEFAULT_MORNING, DEFAULT_NIGHT]
    if "three" in s or "thrice" in s or "3 times" in s:
        return [DEFAULT_MORNING, DEFAULT_AFTERNOON, DEFAULT_NIGHT]
    # every X hours
    m = re.search(r"every\s+(\d+)\s*hours?", s)
    if m:
        hours = int(m.group(1))
        # produce evenly spaced times starting at morning
        slots = []
        start = DEFAULT_MORNING
        t = datetime.combine(date.today(), start)
        while len(slots) < (24 // max(1, hours)):
            slots.append(t.time())
            t += timedelta(hours=hours)
        return slots
    # attempt to find explicit tokens
    for token, tslot in TIME_TOKEN_MAP.items():
        if token in s and tslot not in []:
            return [tslot]
    return []


# -----------------------
# Public API
# -----------------------
def map_dose_pattern_to_times(dose_pattern: str, fallback_instr: Optional[str] = None) -> List[time]:
    """
    Map a parsed dose pattern string into a list of times.
    dose_pattern: e.g., "1-0-1", "1 tab daily", "twice a day"
    fallback_instr: additional instruction text if dose_pattern is ambiguous.
    """
    if not dose_pattern:
        return []

    s = normalize_text(dose_pattern)

    # 1) Numeric pattern like 1-0-1
    counts = parse_numeric_pattern(s)
    if counts:
        times = map_counts_to_times(counts)
        logger.debug("Mapped numeric pattern %s -> %s", s, times)
        if times:
            return times

    # 2) Keyword-based patterns
    times_from_text = estimate_times_from_text(s)
    if times_from_text:
        logger.debug("Mapped text pattern %s -> %s", s, times_from_text)
        return times_from_text

    # 3) Look into fallback instructions
    if fallback_instr:
        times_from_fallback = estimate_times_from_text(fallback_instr)
        if times_from_fallback:
            logger.debug("Used fallback instruction mapping -> %s", times_from_fallback)
            return times_from_fallback

    # 4) Fallback default: morning + night (safe default for many regimens)
    logger.info("Using default times for ambiguous pattern '%s'", dose_pattern)
    return [DEFAULT_MORNING, DEFAULT_NIGHT]


def generate_schedule_entries_for_medicine(med_name: str,
                                           dose_pattern: str,
                                           duration_days: Optional[int],
                                           start_date: Optional[date] = None,
                                           fallback_instr: Optional[str] = None,
                                           notes: Optional[str] = None) -> MedicineSchedule:
    """
    Create a MedicineSchedule object containing all times for each day for the given duration.
    """
    if start_date is None:
        start_date = date.today()

    if duration_days is None or duration_days <= 0:
        duration_days = 5  # default fallback

    times = map_dose_pattern_to_times(dose_pattern, fallback_instr)

    # If times empty (couldn't parse), apply safe default
    if not times:
        times = [DEFAULT_MORNING, DEFAULT_NIGHT]

    schedule = MedicineSchedule(
        medicine=med_name,
        dose_pattern=dose_pattern,
        duration_days=duration_days,
        start_date=start_date,
        times=times,
        notes=notes
    )
    logger.info("Generated schedule for %s: %s for %d days", med_name, times, duration_days)
    return schedule


def expand_schedule_to_datetime_entries(schedule: MedicineSchedule) -> List[Tuple[datetime, str, str]]:
    """
    Expand a MedicineSchedule to concrete datetime entries.
    Returns list of tuples: (datetime_of_reminder, medicine_name, note)
    """
    entries = []
    for day_offset in range(schedule.duration_days):
        current_date = schedule.start_date + timedelta(days=day_offset)
        for t in schedule.times:
            dt = datetime.combine(current_date, t)
            entries.append((dt, schedule.medicine, schedule.notes or schedule.dose_pattern))
    return entries


def format_cron_line_for_entry(dt: datetime, command: str = "echo 'Reminder'") -> str:
    """
    Return a cron-formatted line for a single datetime 'dt' that can be written into crontab.
    Note: This is simplistic and assumes daily repetition is handled separately.
    For recurring daily reminders, use minute hour * * * command
    """
    return f"{dt.minute} {dt.hour} {dt.day} {dt.month} * {command}"


# -----------------------
# Integration helpers
# -----------------------
def save_schedule_entries(db_module, schedule: MedicineSchedule) -> int:
    """
    Save expanded schedule entries using the provided db_module API.
    db_module must expose:
        - create_schedule_table()
        - insert_schedule_entry(datetime_obj, medicine, note)
    Returns the number of saved entries.
    """
    db_module.create_schedule_table()
    entries = expand_schedule_to_datetime_entries(schedule)
    count = 0
    for dt, med, note in entries:
        db_module.insert_schedule_entry(dt, med, note)
        count += 1
    logger.info("Saved %d schedule rows to DB for %s", count, schedule.medicine)
    return count


# -----------------------
# CLI / example usage
# -----------------------
if __name__ == "__main__":
    # small demonstration when run directly
    from datetime import date
    from pprint import pprint

    demo = generate_schedule_entries_for_medicine(
        med_name="Paracetamol 500mg",
        dose_pattern="1-0-1",
        duration_days=5,
        start_date=date.today(),
        fallback_instr="after food"
    )
    pprint(demo)
    entries = expand_schedule_to_datetime_entries(demo)
    print("First 6 entries:")
    for e in entries[:6]:
        print(e[0].isoformat(), e[1], e[2])
