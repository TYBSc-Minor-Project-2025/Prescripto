
# filepath: /Users/anuragbhosale/Desktop/Projects/Prescripto/src/parse_text.py
"""
parse_text.py
Parse raw OCR text from a prescription into a structured representation.

This is intentionally simple and heuristic-based; you can refine it over time
for your own prescription formats.
"""

from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Dict, Optional

logger = logging.getLogger(__name__)


@dataclass
class ParsedPrescription:
    medicine: str
    dose: str
    duration_days: int
    notes: str = ""


DOSE_PATTERN = re.compile(r"\b(\d-\d-\d)\b")
DURATION_PATTERN = re.compile(r"(\d+)\s*(day|days|d)\b", re.IGNORECASE)


def _extract_medicine_name(text: str) -> str:
    """
    Very naive medicine name extractor: take the first non-empty line
    that does not look like a pure dose or duration line.
    """
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    if not lines:
        return "Unknown Medicine"

    for line in lines:
        if DOSE_PATTERN.search(line):
            continue
        if DURATION_PATTERN.search(line):
            continue
        # First reasonable candidate
        return line

    # Fallback to first line
    return lines[0]


def _extract_dose(text: str) -> str:
    """
    Find a pattern like '1-0-1' in the text.
    """
    m = DOSE_PATTERN.search(text)
    if m:
        return m.group(1)
    return "0-0-0"


def _extract_duration_days(text: str) -> int:
    """
    Find something like '5 days' and return 5.
    Defaults to 5 if not found.
    """
    m = DURATION_PATTERN.search(text)
    if not m:
        return 5
    try:
        return int(m.group(1))
    except ValueError:
        return 5


def _extract_notes(text: str, medicine: str, dose: str) -> str:
    """
    Very simple notes extractor: return remaining text that isn't clearly
    the medicine or dose line. You can improve this later.
    """
    cleaned = text.replace(medicine, "").replace(dose, "")
    cleaned = cleaned.strip()
    return cleaned


def parse_prescription_text(text: str) -> Dict[str, object]:
    """
    Parse raw OCR text into a structured dictionary.

    Returns
    -------
    {
        "medicine": str,
        "dose": str,           # "1-0-1"
        "duration_days": int,  # e.g. 5
        "notes": str,
    }
    """
    if not text or not text.strip():
        logger.warning("Empty OCR text passed to parse_prescription_text")
        return {
            "medicine": "Unknown Medicine",
            "dose": "0-0-0",
            "duration_days": 5,
            "notes": "",
        }

    logger.info("Parsing OCR text:\n%s", text)

    medicine = _extract_medicine_name(text)
    dose = _extract_dose(text)
    duration_days = _extract_duration_days(text)
    notes = _extract_notes(text, medicine, dose)

    parsed = ParsedPrescription(
        medicine=medicine,
        dose=dose,
        duration_days=duration_days,
        notes=notes,
    )

    logger.info("Parsed prescription: %s", parsed)

    # Return as a plain dict to keep the rest of the code simple
    return {
        "medicine": parsed.medicine,
        "dose": parsed.dose,
        "duration_days": parsed.duration_days,
        "notes": parsed.notes,
    }