from __future__ import annotations
from pathlib import Path
from typing import Optional

try:
    from PIL import Image, ImageFilter, ImageOps
except Exception:  # pragma: no cover
    Image = None  # type: ignore
    ImageFilter = None  # type: ignore
    ImageOps = None  # type: ignore


DEFAULT_MAX_W = 1600


def preprocess_image(image_path: str, out_dir: Optional[str] = None) -> str:
    """
    Basic preprocessing: resize to max width, convert to grayscale, slight sharpening.
    Returns the output image path (may be same as input if PIL missing).
    """
    p = Path(image_path)
    out_dir_path = Path(out_dir) if out_dir else p.parent
    out_dir_path.mkdir(parents=True, exist_ok=True)
    out_path = out_dir_path / f"pre_{p.name}"

    if Image is None:
        # Best effort fallback: just copy path semantics
        return str(p)

    try:
        with Image.open(p) as im:
            im = im.convert("L")  # grayscale
            w, h = im.size
            if w > DEFAULT_MAX_W:
                ratio = DEFAULT_MAX_W / float(w)
                im = im.resize((int(w * ratio), int(h * ratio)))
            # Boost contrast and sharpness slightly
            im = ImageOps.autocontrast(im)
            if ImageFilter is not None:
                im = im.filter(ImageFilter.SHARPEN)
            im.save(out_path)
            return str(out_path)
    except Exception:
        return str(p)
