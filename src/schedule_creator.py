from __future__ import annotations
from datetime import date, timedelta
from typing import Dict, List, Tuple

# Default time slots (24h format)
TIME_SLOTS = {
    "morning": "08:00",
    "noon": "13:00",
    "evening": "18:00",
    "night": "21:00",
}


def _dose_to_times(dose: str) -> List[str]:
    # dose format: "a-b-c" where a=morning, b=noon, c=night
    parts = (dose or "0-0-0").split("-")
    parts = (parts + ["0", "0", "0"])[:3]
    slots = ["morning", "noon", "night"]
    times = [slots[i] for i, p in enumerate(parts) if p.strip() == "1"]
    return times


def build_schedule(parsed: Dict, start: date | None = None) -> List[Dict]:
    """
    Given parsed prescription data, build a list of reminder entries.
    Each entry:
    {
      'medicine': str,
      'when': 'morning'|'noon'|'evening'|'night',
      'time': 'HH:MM',
      'start_date': 'YYYY-MM-DD',
      'end_date': 'YYYY-MM-DD',
      'message': str
    }
    """
    start = start or date.today()
    duration_days: int = int(parsed.get("duration_days") or 1)
    end = start + timedelta(days=duration_days - 1)

    times = parsed.get("time") or _dose_to_times(parsed.get("dose", "0-0-0"))
    # Map 'evening' to a time if mentioned
    normalized_times = []
    for t in times:
        t = t.lower()
        if t == "afternoon":
            t = "noon"
        normalized_times.append(t)

    # Expand to reminders
    reminders: List[Dict] = []
    medicine = parsed.get("medicine") or "Unknown"
    for slot in normalized_times:
        hhmm = TIME_SLOTS.get(slot)
        if not hhmm:
            continue
        msg = f"Take {medicine} ({slot})"
        reminders.append(
            {
                "medicine": medicine,
                "when": slot,
                "time": hhmm,
                "start_date": start.isoformat(),
                "end_date": end.isoformat(),
                "message": msg,
            }
        )
    return reminders
