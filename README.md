# Prescripto – Smart Medication Reminder

A simple end-to-end pipeline that extracts medication schedules from a prescription image and creates reminders. Built with Python, optional YOLOv8 for region detection, Tesseract OCR, and SQLite for storage.

## Features
- Image preprocessing (resize, grayscale, contrast, sharpen)
- Optional YOLO region detection (medicine, dose, duration, etc.)
- OCR with Tesseract
- Regex/NLP parsing of the OCR text
- Schedule builder with standard time slots
- SQLite persistence
- Desktop notification helper and cron suggestion file

## Project structure
```
smart-med-reminder/
├── data/
│   ├── sample_prescriptions/
│   └── ocr_output/
├── models/
│   └── yolo_med.pt         # optional
├── src/
│   ├── detect_regions.py
│   ├── ocr_extract.py
│   ├── parse_text.py
│   ├── schedule_creator.py
│   ├── notify.py
│   ├── db.py
│   └── main.py
├── utils/
│   ├── preprocess.py
│   └── helpers.py
├── architecture.md
├── flowchart.txt
├── README.md
└── requirements.txt
```

Your workspace already reflects this layout inside `Prescripto/`.

## Requirements
- Python 3.10+
- Tesseract OCR installed on your system
- Pip packages: see `requirements.txt`

Install Tesseract on macOS (Homebrew):
```bash
brew install tesseract
```

Install Python deps:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Optional (YOLOv8 and OpenCV) if you want region detection:
```bash
pip install ultralytics opencv-python-headless
```

## Quick start
Put a sample image into `data/sample_prescriptions/` and run:
```bash
python -m src.main data/sample_prescriptions/your_image.jpg
```

What happens:
1. Preprocess image to `data/ocr_output/pre_your_image.jpg`
2. Run YOLO detection if `--model models/yolo_med.pt` is provided, else fall back to full-image OCR
3. OCR with Tesseract
4. Parse text with regex to extract medicine, dose, times and duration
5. Build schedule and save to SQLite (`data/prescripto.db`)
6. Write `data/cron_suggestions.txt` with cron entries you can review and install

Send a quick notification test:
```bash
python -m src.main --notify "Time to take your meds"
```

## Notes
- Region detection is optional; you can add a custom YOLO model at `models/yolo_med.pt`.
- The parsing is heuristic. You can refine regexes or integrate spaCy for better extraction.
- Cron scheduling is non-invasive here; we only write suggestions to a file. Review and install manually if desired.

## Troubleshooting
- If OCR is empty, verify Tesseract is installed and your image is readable.
- If imports fail for optional packages (ultralytics, opencv), either install them or ignore region detection.
- On macOS, notifications use AppleScript if `plyer` isn’t available.
