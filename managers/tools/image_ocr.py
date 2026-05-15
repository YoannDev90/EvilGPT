"""_summary_."""
import base64
import io
from typing import Optional

import pytesseract
import requests
from PIL import Image, ImageOps

from utils.logger import get_logger

logger = get_logger()


def _build_tesseract_config(psm: Optional[int], oem: Optional[int]) -> str:
    """_summary_.

    Parameters
    ----------
    psm : Optional[int]
        _description_
    oem : Optional[int]
        _description_

    Returns
    -------
    str
        _description_
    """
    parts = []
    if psm is not None:
        parts.append(f"--psm {psm}")
    if oem is not None:
        parts.append(f"--oem {oem}")
    return " ".join(parts)


def _load_image_bytes(
    image_path: Optional[str], image_url: Optional[str], image_base64: Optional[str]
) -> bytes:
    """_summary_.

    Parameters
    ----------
    image_path : Optional[str]
        _description_
    image_url : Optional[str]
        _description_
    image_base64 : Optional[str]
        _description_

    Returns
    -------
    bytes
        _description_

    Raises
    ------
    ValueError
        _description_
    """
    if image_path:
        with open(image_path, "rb") as f:
            return f.read()

    if image_url:
        response = requests.get(image_url, timeout=20)
        response.raise_for_status()
        return response.content

    if image_base64:
        return base64.b64decode(image_base64)

    raise ValueError("Provide one source: image_path, image_url, or image_base64")


async def image_ocr(
    image_path: str = "",
    image_url: str = "",
    image_base64: str = "",
    lang: str = "eng",
    psm: Optional[int] = None,
    oem: Optional[int] = None,
) -> str:
    """Extract text from image with Tesseract OCR.

    Parameters
    ----------
    image_path : str
        _description_ (Default value = '')
    image_url : str
        _description_ (Default value = '')
    image_base64 : str
        _description_ (Default value = '')
    lang : str
        _description_ (Default value = 'eng')
    psm : Optional[int]
        _description_ (Default value = None)
    oem : Optional[int]
        _description_ (Default value = None)

    Returns
    -------
    str
        _description_
    """
    try:
        raw = _load_image_bytes(image_path, image_url, image_base64)
        image = Image.open(io.BytesIO(raw))

        # Basic preprocessing improves OCR quality on screenshots/memes.
        image = ImageOps.grayscale(image)
        config = _build_tesseract_config(psm, oem)
        text = pytesseract.image_to_string(image, lang=lang, config=config)

        cleaned = text.strip()
        if not cleaned:
            return "No text detected in image."
        return cleaned
    except pytesseract.TesseractNotFoundError:
        logger.error("Tesseract binary not found")
        return (
            "Error: Tesseract OCR is not installed on host (install `tesseract-ocr`)."
        )
    except Exception as e:
        logger.error(f"image_ocr failed: {e}")
        return f"Error: {str(e)}"
