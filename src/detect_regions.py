
# filepath: /Users/anuragbhosale/Desktop/Projects/Prescripto/src/detect_regions.py
"""
detect_regions.py
Use a YOLO model (if available) to detect text/medicine regions in a prescription.

If the YOLO dependency isn't installed or the model can't be loaded,
this module falls back to returning a single region covering the whole image.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import List, Tuple

from PIL import Image

try:
    from ultralytics import YOLO  # type: ignore
except ImportError:
    YOLO = None  # type: ignore

logger = logging.getLogger(__name__)

# Type aliases
BBox = Tuple[int, int, int, int]  # (x1, y1, x2, y2)


def _load_model(model_path: str | Path | None = None):
    """
    Load the YOLO model if ultralytics is available.
    """
    if YOLO is None:
        logger.warning(
            "ultralytics is not installed. "
            "Install it with `pip install ultralytics` to enable region detection."
        )
        return None

    # Allow a custom model path, or default to a local file if shipped with the project
    if model_path is None:
        model_path = Path(__file__).parent / "models" / "prescripto-yolo.pt"

    model_path = Path(model_path)
    if not model_path.exists():
        logger.warning(
            "YOLO model not found at %s. Falling back to full-image region.",
            model_path,
        )
        return None

    try:
        logger.info("Loading YOLO model from %s", model_path)
        return YOLO(str(model_path))
    except Exception as e:
        logger.error("Failed to load YOLO model: %s", e, exc_info=True)
        return None


def _full_image_region(image_path: str | Path) -> List[BBox]:
    """
    Fallback: return a single region that covers the whole image.
    """
    img = Image.open(image_path)
    w, h = img.size
    logger.info("Using full-image region fallback: width=%d height=%d", w, h)
    return [(0, 0, w, h)]


def detect_regions(image_path: str | Path) -> List[BBox]:
    """
    Detect text/medicine regions on the prescription image.

    Returns
    -------
    List[Tuple[int, int, int, int]]
        A list of bounding boxes in (x1, y1, x2, y2) format.
    """
    image_path = str(image_path)
    model = _load_model()

    # If no model, fallback
    if model is None:
        return _full_image_region(image_path)

    try:
        logger.info("Running YOLO detection on %s", image_path)
        results = model(image_path)
    except Exception as e:
        logger.error("YOLO inference failed: %s", e, exc_info=True)
        return _full_image_region(image_path)

    boxes: List[BBox] = []

    # ultralytics.YOLO returns a list of Results; we take the first
    for r in results:
        if not hasattr(r, "boxes") or r.boxes is None:
            continue

        for box in r.boxes:  # type: ignore[attr-defined]
            # xyxy format: [x1, y1, x2, y2]
            xyxy = box.xyxy[0].tolist()  # type: ignore[index]
            x1, y1, x2, y2 = map(int, xyxy)
            boxes.append((x1, y1, x2, y2))

    if not boxes:
        logger.warning("YOLO returned no boxes; using full-image region fallback.")
        return _full_image_region(image_path)

    logger.info("Detected %d region(s)", len(boxes))
    return boxes