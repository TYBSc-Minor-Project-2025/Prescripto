from __future__ import annotations
import argparse
from pathlib import Path

from src.detect_regions import RegionDetector
from src.ocr_extract import extract_text
from src.parse_text import parse_prescription_text, parse_prescription_items
from src.schedule_creator import build_schedule
from src.db import init_db, save_schedule, list_reminders
from utils.preprocess import preprocess_image
from utils.helpers import ensure_dir, write_lines


def create_cron_suggestions(reminders: list[dict], out_path: Path) -> None:
    """
    Write suggested crontab entries to a file (non-invasive).
    On macOS, you may prefer launchd, but cron is simpler for demo purposes.
    """
    lines: list[str] = [
        "# Suggested cron entries for medication reminders",
        "# Install with: crontab data/cron_suggestions.txt (after review)",
        "# Use absolute paths to your Python interpreter and main script.",
        "",
    ]
    python_path = "python3"  # Adjust if needed
    main_py = str((Path(__file__).resolve()).parent / "main.py")
    for r in reminders:
        hh, mm = (r["time"].split(":") + ["0", "0"])[:2]
        message = r["message"].replace("\"", "'")
        cmd = f'{int(mm)} {int(hh)} * * * {python_path} {main_py} --notify "{message}"'
        lines.append(cmd)
    write_lines(out_path, lines)


def run_pipeline(image_path: str, model_path: str | None = None) -> dict:
    # Ensure output directories
    data_dir = ensure_dir(Path(__file__).resolve().parent.parent / "data" / "ocr_output")

    # Preprocess image
    pre_img = preprocess_image(image_path, out_dir=str(data_dir))

    # Detect regions (if model is provided)
    detector = RegionDetector(model_path=model_path)
    regions = detector.detect(pre_img)

    # OCR
    ocr = extract_text(pre_img, regions=regions)

    # Parse (support multi-item prescriptions)
    raw_text = ocr.get("raw_text", "")
    items = parse_prescription_items(raw_text)
    if items:
        parsed_list = items
    else:
        parsed_list = [parse_prescription_text(raw_text)]

    # Schedule for each item
    reminders = []
    for p in parsed_list:
        reminders.extend(build_schedule(p))

    return {
        "regions": regions,
        "ocr": ocr,
        "parsed": parsed_list,
        "reminders": reminders,
    }


def main() -> None:
    parser = argparse.ArgumentParser(description="Smart Medication Reminder - Prescripto")
    parser.add_argument("image", nargs="?", help="Path to prescription image (jpg/png)")
    parser.add_argument("--model", dest="model", default=None, help="Path to YOLO model (optional)")
    parser.add_argument("--notify", dest="notify_msg", default=None, help="Send a one-off notification and exit")
    args = parser.parse_args()

    if args.notify_msg:
        # On-demand notify mode
        from src.notify import desktop_notify, play_sound

        desktop_notify("Medication Reminder", args.notify_msg)
        play_sound()
        return

    if not args.image:
        print("Please provide an image path. Example: python -m src.main data/sample_prescriptions/p1.jpg")
        return

    # Initialize DB
    init_db()

    # Run pipeline
    result = run_pipeline(args.image, model_path=args.model)

    # Persist schedule for each parsed item
    parsed_items = result["parsed"] if isinstance(result["parsed"], list) else [result["parsed"]]
    for p in parsed_items:
        save_schedule(p, [r for r in result["reminders"] if r.get("medicine") == p.get("medicine")])

    # Output summary
    print("Parsed items:")
    for p in parsed_items:
        print(p)

    # List reminders
    reminders = list_reminders()
    print("\nReminders saved (total: %d):" % len(reminders))
    for r in reminders:
        print(f"- {r['start_date']} {r['time']} {r['message']}")

    # Suggest cron
    cron_file = Path(__file__).resolve().parent.parent / "data" / "cron_suggestions.txt"
    create_cron_suggestions(result["reminders"], cron_file)
    print(f"\nCron suggestions written to: {cron_file}")


if __name__ == "__main__":
    main()
