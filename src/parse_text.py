from __future__ import annotations
import re
from typing import Dict, List, Optional, Tuple

DURATION_RE = re.compile(r"\b(\d+)\s*(day|days|week|weeks)\b", re.I)
DOSE_RE = re.compile(r"\b(\d-\d-\d)\b")
# include common abbreviations often seen in prescriptions
TIME_WORDS = ["morning", "noon", "afternoon", "aft", "evening", "eve", "night"]
TIME_RE = re.compile(r"\b(" + "|".join(TIME_WORDS) + r")\b", re.I)


def _guess_medicine_names(text: str) -> List[str]:
    # Heuristic: pick capitalized words 3+ chars or lines starting with a name-like token
    meds: List[str] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        tokens = re.findall(r"[A-Za-z][A-Za-z\-]{2,}", line)
        # Filter common non-medicine words
        blacklist = {"morning", "afternoon", "evening", "night", "daily", "tablet", "tabs", "capsule", "mg", "ml"}
        cand = [t for t in tokens if t.lower() not in blacklist]
        if cand:
            meds.append(cand[0])
    # Deduplicate while preserving order
    out: List[str] = []
    for m in meds:
        if m not in out:
            out.append(m)
    return out[:1]  # return first guess


def _parse_duration_days(text: str) -> Optional[int]:
    m = DURATION_RE.search(text)
    if not m:
        return None
    num = int(m.group(1))
    unit = m.group(2).lower()
    if unit.startswith("week"):
        return num * 7
    return num


def _parse_times(text: str) -> List[str]:
    hits = [m.group(1).lower() for m in TIME_RE.finditer(text)]
    # Normalize noon/afternoon overlap
    norm = []
    for t in hits:
        if t in ("afternoon", "aft"):
            norm.append("noon")
        elif t == "eve":
            norm.append("evening")
        else:
            norm.append(t)
    # Deduplicate preserve order
    seen, out = set(), []
    for t in norm:
        if t not in seen:
            seen.add(t)
            out.append(t)
    return out


def parse_prescription_text(text: str) -> Dict:
    """
    Map raw OCR text to structured prescription data.
    Returns a dict like:
    {
      "medicine": "Paracetamol",
      "dose": "1-0-1",
      "time": ["morning", "night"],
      "duration_days": 5
    }
    """
    text = text or ""
    medicine = None
    meds = _guess_medicine_names(text)
    if meds:
        medicine = meds[0]

    dose = None
    m = DOSE_RE.search(text)
    if m:
        dose = m.group(1)

    times = _parse_times(text)

    duration_days = _parse_duration_days(text)

    # If dose is present but times missing, infer from dose pattern
    if dose and not times:
        parts = dose.split("-")
        slot_names = ["morning", "noon", "night"]
        for idx, p in enumerate(parts[:3]):
            if p == "1":
                times.append(slot_names[idx])

    # If times present but dose missing, infer a simple 1 per time
    if times and not dose:
        slots = ["morning", "noon", "night"]
        dose = "-".join(["1" if s in times else "0" for s in slots])

    return {
        "medicine": medicine or "Unknown",
        "dose": dose or "0-0-0",
        "time": times or [],
        "duration_days": duration_days or 1,
    }


# ---------- Multi-item parsing (table or enumerated list) ----------

ITEM_START_RE = re.compile(r"^\s*(\d+)\)\s*(.+)$", re.M)


def _split_items(text: str) -> List[Tuple[str, int, int]]:
    """Return list of (item_text, start_index, end_index)."""
    matches = list(ITEM_START_RE.finditer(text))
    if not matches:
        return []
    items: List[Tuple[str, int, int]] = []
    for i, m in enumerate(matches):
        start = m.start()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(text)
        items.append((text[start:end].strip(), start, end))
    return items


def _clean_medicine_name(line: str) -> str:
    # Remove leading ordinal like "1)"
    line = re.sub(r"^\s*\d+\)\s*", "", line).strip()
    # Drop common dosage form prefixes
    line = re.sub(r"^(TAB\.?|CAP\.?|SYR\.?|INJ\.?)\s*", "", line, flags=re.I).strip()
    # Collapse extra spaces / punctuation
    line = re.sub(r"\s{2,}", " ", line)
    return line


def parse_prescription_items(text: str) -> List[Dict]:
    """
    Parse multiple prescription rows like:
    1) TAB. NAME ... \n 1 Morning, 1 Night ... \n 10 Days
    Returns a list of dicts with the same schema as parse_prescription_text.
    """
    segments = _split_items(text or "")
    items: List[Dict] = []
    if not segments:
        return items
    for seg, _s, _e in segments:
        lines = [ln.strip() for ln in seg.splitlines() if ln.strip()]
        if not lines:
            continue
        med_line = lines[0]
        medicine = _clean_medicine_name(med_line)
        # Reuse single-item parser on the segment to capture dose/time/duration
        parsed = parse_prescription_text(seg)
        parsed["medicine"] = medicine or parsed.get("medicine") or "Unknown"
        items.append(parsed)
    return items
