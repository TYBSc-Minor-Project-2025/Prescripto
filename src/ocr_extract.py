
# filepath: /Users/anuragbhosale/Desktop/Projects/Prescripto/src/ocr_extract.py
"""
ocr_extract.py
Utilities to run OCR on detected regions of a prescription image.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Iterable, List, Tuple

from PIL import Image

try:
    import pytesseract
except ImportError:  # pytesseract is optional but strongly recommended
    pytesseract = None  # type: ignore

logger = logging.getLogger(__name__)

# Type aliases
BBox = Tuple[int, int, int, int]  # (x1, y1, x2, y2)


def _ensure_pytesseract_available() -> None:
    """
    Raise a clear error if pytesseract is not installed.
    """
    if pytesseract is None:
        raise RuntimeError(
            "pytesseract is not installed. Install it with "
            "`pip install pytesseract` and ensure Tesseract OCR is available "
            "on your system."
        )


def _open_image(path: str | Path) -> Image.Image:
    """
    Open an image from disk and convert to RGB.
    """
    img_path = Path(path)
    if not img_path.exists():
        raise FileNotFoundError(f"Image not found: {img_path}")
    return Image.open(img_path).convert("RGB")


def _ocr_image_region(img: Image.Image, bbox: BBox) -> str:
    """
    Run OCR on a single cropped region.
    """
    _ensure_pytesseract_available()

    x1, y1, x2, y2 = bbox
    crop = img.crop((x1, y1, x2, y2))

    # Configure for single block of text; tweak as needed
    config = "--oem 3 --psm 6"
    text = pytesseract.image_to_string(crop, config=config)  # type: ignore[arg-type]
    return text.strip()


def extract_text_from_image(
    image_path: str | Path,
    regions: Iterable[BBox],
) -> str:
    """
    Given the original image path and list/iterable of bounding boxes,
    run OCR on each region and return the concatenated text.

    Parameters
    ----------
    image_path:
        Path to the original image.
    regions:
        Iterable of (x1, y1, x2, y2) bounding boxes.

    Returns
    -------
    str
        Combined OCR text from all regions, joined by newlines.
    """
    logger.info("Starting OCR on %d region(s)", len(list(regions)))

    img = _open_image(image_path)
    texts: List[str] = []

    for idx, bbox in enumerate(regions):
        try:
            region_text = _ocr_image_region(img, bbox)
            logger.info("Region %d OCR text: %s", idx, region_text.replace("\n", " "))
            if region_text:
                texts.append(region_text)
        except Exception as e:
            logger.error("OCR failed for region %d (%s): %s", idx, bbox, e, exc_info=True)

    combined = "\n".join(texts).strip()
    logger.info("OCR complete, total %d non-empty region(s)", len(texts))
    return combined