"""
main.py
End-to-end pipeline for prescription → reminders system.

Flow:
1. Detect medicine/dose regions (YOLO)
2. Extract text via OCR
3. Parse medicine name, dose pattern, duration
4. Generate schedule
5. Save to SQLite DB
"""

from src.ocr_extract import extract_text_from_image
from src.detect_regions import detect_regions
from src.parse_text import parse_prescription_text
from src.schedule_creator import (
    generate_schedule_entries_for_medicine,
    save_schedule_entries
)
import src.db as db


def process_prescription(image_path: str):
    print(f"\n[INFO] Processing prescription: {image_path}")

    # -------------------------
    # 1. Detect regions
    # -------------------------
    try:
        regions = detect_regions(image_path)
        print("[OK] Regions detected")
    except Exception as e:
        print("[ERROR] Region detection failed:", e)
        return

    # -------------------------
    # 2. OCR extraction
    # -------------------------
    try:
        extracted_text = extract_text_from_image(image_path, regions)
        print("[OK] OCR extraction complete")
    except Exception as e:
        print("[ERROR] OCR failed:", e)
        return

    # -------------------------
    # 3. Parse prescription
    # -------------------------
    try:
        parsed = parse_prescription_text(extracted_text)
        print("[OK] Parsing complete")
        print("Parsed Output:", parsed)
    except Exception as e:
        print("[ERROR] Parsing failed:", e)
        return

    # Expected parsed output structure:
    # {
    #   "medicine": "Paracetamol 500mg",
    #   "dose": "1-0-1",
    #   "duration_days": 5,
    #   "notes": "after food"
    # }

    # -------------------------
    # 4. Generate schedule
    # -------------------------
    try:
        schedule = generate_schedule_entries_for_medicine(
            med_name=parsed["medicine"],
            dose_pattern=parsed["dose"],
            duration_days=parsed.get("duration_days", 5),
            fallback_instr=parsed.get("notes"),
            start_date=None
        )
        print("[OK] Schedule generated")
    except Exception as e:
        print("[ERROR] Schedule creation failed:", e)
        return

    # -------------------------
    # 5. Save to DB
    # -------------------------
    try:
        saved_count = save_schedule_entries(db, schedule)
        print(f"[OK] Saved {saved_count} reminders to DB for {schedule.medicine}")
    except Exception as e:
        print("[ERROR] Saving schedule failed:", e)
        return


if __name__ == "__main__":
    # temp test image
    sample_image = "data/sample_prescriptions/prescription.png"
    process_prescription(sample_image)
