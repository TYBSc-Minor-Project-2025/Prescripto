from __future__ import annotations
from pathlib import Path
from typing import Dict, Optional, Tuple, Any
import io

try:
    from PIL import Image
except Exception:  # pragma: no cover
    Image = None  # type: ignore

try:  # optional dependency
    import pytesseract  # type: ignore
except Exception:  # pragma: no cover
    pytesseract = None  # type: ignore

BBox = Tuple[int, int, int, int]


def _crop_region(image_path: str, bbox: BBox) -> Optional[Any]:
    if Image is None:
        return None
    try:
        with Image.open(image_path) as im:
            x, y, w, h = bbox
            x2, y2 = x + max(0, w), y + max(0, h)
            return im.crop((x, y, x2, y2)).copy()
    except Exception:
        return None


def _ocr_image(img: Any, lang: str = "eng") -> str:
    if pytesseract is None:
        return ""  # graceful fallback
    try:
        return pytesseract.image_to_string(img, lang=lang) or ""
    except Exception:
        return ""


def extract_text(image_path: str, regions: Optional[Dict[str, BBox]] = None, lang: str = "eng") -> Dict:
    """
    OCR the full image or detected regions.

    Returns dict:
    {
      'raw_text': '...',
      'by_region': {'medicine': 'Paracetamol', ...}
    }
    """
    image_path = str(Path(image_path))
    by_region: Dict[str, str] = {}

    if regions:
        for name, bbox in regions.items():
            img = _crop_region(image_path, bbox)
            if img is None and Image is not None:
                try:
                    img = Image.open(image_path)  # fallback: whole image
                except Exception:
                    img = None
            if img is not None:
                by_region[name] = _ocr_image(img, lang=lang)
    else:
        # Full image OCR
        if Image is not None:
            try:
                with Image.open(image_path) as im:
                    by_region["full"] = _ocr_image(im, lang=lang)
            except Exception:
                by_region["full"] = ""
        else:
            by_region["full"] = ""

    raw_text = "\n".join([t for t in by_region.values() if t]).strip()
    return {"raw_text": raw_text, "by_region": by_region}
