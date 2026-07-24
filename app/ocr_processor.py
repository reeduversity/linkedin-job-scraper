"""
Real OCR processing module for LinkedIn post images.

Pipeline:
1. Receive image URL from Apify actor output
2. Download the image
3. Process with Tesseract OCR (if available)
4. Extract real text
5. Return OCR text and confidence
6. If OCR is unavailable or fails, record failure status without fabrication

Requires: pytesseract, Pillow (PIL)
Install: pip install pytesseract Pillow
System: Tesseract OCR engine must be installed (brew install tesseract / apt install tesseract-ocr)
"""
from __future__ import annotations

import logging
import os
import tempfile
from pathlib import Path
from typing import Any

logger = logging.getLogger("ocr_processor")

# Tesseract availability check
TESSERACT_AVAILABLE = False
try:
    import pytesseract
    from PIL import Image
    import requests
    TESSERACT_AVAILABLE = True
    logger.info("Tesseract OCR is available")
except ImportError:
    pytesseract = None  # type: ignore
    Image = None  # type: ignore
    requests = None  # type: ignore
    logger.warning("pytesseract/Pillow not installed. OCR will be unavailable.")


def is_ocr_available() -> bool:
    """Check if OCR dependencies (pytesseract + tesseract binary) are available."""
    if not TESSERACT_AVAILABLE:
        return False
    try:
        import pytesseract
        pytesseract.get_tesseract_version()
        return True
    except Exception:
        return False


def download_image(image_url: str, timeout: int = 30) -> bytes | None:
    """
    Download an image from URL. Returns raw bytes or None on failure.
    Does NOT generate/fabricate image data.
    """
    if not TESSERACT_AVAILABLE:
        return None
    try:
        import requests
        resp = requests.get(image_url, timeout=timeout, headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        })
        resp.raise_for_status()
        content_type = resp.headers.get("Content-Type", "")
        if not content_type.startswith("image/"):
            logger.warning(f"URL did not return an image (Content-Type: {content_type}): {image_url[:80]}")
            return None
        return resp.content
    except requests.RequestException as e:
        logger.error(f"Failed to download image {image_url[:80]}: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error downloading image {image_url[:80]}: {e}")
        return None


def ocr_image(image_bytes: bytes) -> dict[str, Any]:
    """
    Run OCR on image bytes. Returns a dict with extracted text and metadata.
    
    Returns:
        {
            "ocr_text": str | None,       # Extracted text or None if failed
            "ocr_confidence": float | None, # Average confidence (0.0-100.0) or None
            "ocr_processed": bool,         # True if OCR was attempted
            "ocr_extraction_status": str,  # "SUCCESS", "FAILED", "NO_TESSERACT", "NO_IMAGE"
        }
    
    Never fabricates text. If OCR fails, ocr_text remains None.
    """
    result = {
        "ocr_text": None,
        "ocr_confidence": None,
        "ocr_processed": False,
        "ocr_extraction_status": "NO_TESSERACT",
    }

    if not TESSERACT_AVAILABLE or pytesseract is None or Image is None:
        result["ocr_extraction_status"] = "NO_TESSERACT"
        return result

    if not image_bytes:
        result["ocr_extraction_status"] = "NO_IMAGE"
        return result

    try:
        from PIL import Image
        import io
        image = Image.open(io.BytesIO(image_bytes))

        # Run OCR
        ocr_data = pytesseract.image_to_data(image, output_type=pytesseract.Output.DICT)  # type: ignore
        extracted_text = " ".join(
            word for word, conf in zip(ocr_data.get("text", []), ocr_data.get("conf", []))
            if word.strip() and conf != "-1" and int(conf) > 0
        ).strip()

        # Calculate average confidence from non-zero confidences
        conf_values = []
        for conf in ocr_data.get("conf", []):
            try:
                c = float(conf)
                if c > 0:
                    conf_values.append(c)
            except (ValueError, TypeError):
                pass

        avg_confidence = round(sum(conf_values) / len(conf_values), 2) if conf_values else None

        if extracted_text:
            result["ocr_text"] = extracted_text
            result["ocr_confidence"] = avg_confidence
            result["ocr_processed"] = True
            result["ocr_extraction_status"] = "SUCCESS"
            logger.info(f"OCR succeeded: {len(extracted_text)} chars, confidence={avg_confidence}")
        else:
            result["ocr_processed"] = True
            result["ocr_extraction_status"] = "FAILED"
            logger.warning("OCR completed but no text extracted")

    except pytesseract.TesseractNotFoundError:  # type: ignore
        result["ocr_extraction_status"] = "NO_TESSERACT"
        logger.error("Tesseract binary not found. Install tesseract-ocr on your system.")
    except Exception as e:
        result["ocr_processed"] = True
        result["ocr_extraction_status"] = "FAILED"
        logger.error(f"OCR processing failed: {e}")

    return result


def process_image_url(image_url: str) -> dict[str, Any]:
    """
    End-to-end: download image -> run OCR -> return results.
    
    If image_url is empty or invalid, returns failure status.
    Never generates fake data.
    """
    if not image_url:
        return {
            "ocr_text": None,
            "ocr_confidence": None,
            "ocr_processed": False,
            "ocr_extraction_status": "NO_IMAGE",
        }

    if not is_ocr_available():
        return {
            "ocr_text": None,
            "ocr_confidence": None,
            "ocr_processed": False,
            "ocr_extraction_status": "NO_TESSERACT",
        }

    image_bytes = download_image(image_url)
    if image_bytes is None:
        return {
            "ocr_text": None,
            "ocr_confidence": None,
            "ocr_processed": True,
            "ocr_extraction_status": "DOWNLOAD_FAILED",
        }

    return ocr_image(image_bytes)

