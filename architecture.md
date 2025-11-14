SMART MEDICATION REMINDER SYSTEM
--------------------------------

INPUT:
- Image of prescription (jpg/png)

PROCESSING PIPELINE:
1. Image Preprocessing
   - Resize
   - Noise removal
   - Contrast normalization

2. YOLO-based Region Detection 
   - Detect: Medicine Name Box, Dosage, Frequency, Timing keywords.

3. OCR Extraction
   - Crop detected regions
   - Use Tesseract OCR to extract:
        - Medicine name
        - Strength (mg/ml)
        - Dosage (1-0-1 or 1 tab daily)
        - Duration (5 days, 10 days)

4. NLP Parsing
   - Regex + spaCy keyword extraction
   - Map to structured data:
        {
          "medicine": "Paracetamol",
          "dose": "1-0-1",
          "time": ["Morning", "Night"],
          "duration_days": 5
        }

5. Reminder Scheduler
   - Save reminders to SQLite
   - Create triggers using:
        - cron job (Mac/Linux)
        - Windows Task Scheduler

6. Notification Module
   - Desktop notification
   - Email optional
   - CLI print + sound alert optional

OUTPUT:
- Auto-generated medicine schedule
- Daily reminders at correct time
- Summary table

---------------------------------
Tech Stack: Python, YOLOv8, Tesseract, spaCy, SQLite, cron/Task Scheduler
---------------------------------
