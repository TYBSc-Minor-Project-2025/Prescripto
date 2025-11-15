
# filepath: /Users/anuragbhosale/Desktop/Projects/Prescripto/src/main.py
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

import argparse
import logging
import os
from typing import Optional

from src.ocr_extract import extract_text_from_image
from src.detect_regions import detect_regions
from src.parse_text import parse_prescription_text
from src.schedule_creator import (
    generate_schedule_entries_for_medicine,
    save_schedule_entries,
)
import src.db as db

# -------------------------
# Logging setup
# -------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
)
logger = logging.getLogger(__name__)


def process_prescription(image_path: str) -> Optional[None]:
    """
    Run the full pipeline:
    1. detect regions
    2. OCR those regions
    3. parse text
    4. generate schedule
    5. save schedule to DB
    """
    if not os.path.exists(image_path):
        logger.error("[ERROR] Image path does not exist: %s", image_path)
        return

    logger.info("[INFO] Processing prescription: %s", image_path)

    # -------------------------
    # 1. Detect regions
    # -------------------------
    try:
        regions = detect_regions(image_path)
        logger.info("[OK] Regions detected")
    except Exception as e:
        logger.error(
            "Region detection failed for image %s: %s",
            image_path,
            e,
            exc_info=True,
        )
        return

    # -------------------------
    # 2. OCR extraction
    # -------------------------
    try:
        extracted_text = extract_text_from_image(image_path, regions)
        logger.info("[OK] OCR extraction complete")
    except Exception as e:
        logger.error(
            "OCR failed for image %s: %s",
            image_path,
            e,
            exc_info=True,
        )
        return

    # -------------------------
    # 3. Parse prescription
    # -------------------------
    try:
        parsed = parse_prescription_text(extracted_text)
        logger.info("[OK] Parsing complete")
        logger.info("Parsed Output: %s", parsed)
    except Exception as e:
        logger.error("Parsing failed for extracted text: %s", e, exc_info=True)
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
            med_name=parsed.get("medicine", "Unknown Medicine"),
            dose_pattern=parsed.get("dose", "0-0-0"),
            duration_days=parsed.get("duration_days", 5),
            fallback_instr=parsed.get("notes", ""),
            start_date=None,
        )
        logger.info("[OK] Schedule generated")
    except Exception as e:
        logger.error(
            "Schedule creation failed for medicine %s: %s",
            parsed.get("medicine", "Unknown"),
            e,
            exc_info=True,
        )
        return

    # -------------------------
    # 5. Save to DB
    # -------------------------
    try:
        saved_count = save_schedule_entries(db, schedule)
        logger.info(
            "[OK] Saved %d reminders to DB for %s",
            saved_count,
            schedule.medicine,
        )
    except Exception as e:
        logger.error(
            "Saving schedule failed for medicine %s: %s",
            schedule.medicine,
            e,
            exc_info=True,
        )
        return


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Process a prescription image and create reminders."
    )
    parser.add_argument(
        "image_path",
        help="Path to the prescription image (e.g. data/sample_prescriptions/prescription.png)",
    )
    args = parser.parse_args()

    process_prescription(args.image_path)


if __name__ == "__main__":
    main()