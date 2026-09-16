import io
import re
import logging
import pdfplumber
from typing import Tuple

logger = logging.getLogger(__name__)

def is_text_garbled_or_empty(text: str) -> bool:
    """
    Check if extracted text is empty, too short, or contains high ratio of garbled characters.
    """
    if not text or len(text.strip()) < 50:
        return True
    
    # Check printable character ratio
    printable_chars = sum(1 for c in text if c.isprintable() and not c.isspace())
    total_chars = len(text.strip())
    
    if total_chars == 0:
        return True
        
    ratio = printable_chars / total_chars
    if ratio < 0.6:  # Less than 60% printable
        return True
        
    # Check for excessive unreadable symbols or replacement chars
    garbage_count = len(re.findall(r'[\ufffd\x00-\x08\x0b\x0c\x0e-\x1f]', text))
    if garbage_count > 10:
        return True

    return False

def extract_text_pdfplumber(pdf_bytes: bytes) -> str:
    """Extract text from PDF using pdfplumber."""
    extracted_pages = []
    with pdfplumber.open(io.BytesIO(pdf_bytes)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                extracted_pages.append(page_text)
    return "\n\n".join(extracted_pages)

def extract_text_ocr(pdf_bytes: bytes) -> str:
    """Fallback OCR text extraction using pdf2image and pytesseract."""
    try:
        from pdf2image import convert_from_bytes
        import pytesseract
    except ImportError:
        logger.warning("pdf2image or pytesseract missing for OCR fallback.")
        return ""

    try:
        images = convert_from_bytes(pdf_bytes)
        ocr_texts = []
        for i, img in enumerate(images):
            text = pytesseract.image_to_string(img)
            if text:
                ocr_texts.append(text)
        return "\n\n".join(ocr_texts)
    except Exception as e:
        logger.warning(f"OCR extraction failed or Tesseract binary unavailable: {e}")
        return ""

def parse_pdf(pdf_bytes: bytes) -> Tuple[str, str]:
    """
    Main PDF parser: Tries pdfplumber first, falls back to OCR if text is empty/garbled.
    Returns tuple of (extracted_text, method_used).
    """
    text = extract_text_pdfplumber(pdf_bytes)
    
    if not is_text_garbled_or_empty(text):
        return text, "pdfplumber"
        
    logger.info("pdfplumber text was empty or garbled. Attempting OCR fallback...")
    ocr_text = extract_text_ocr(pdf_bytes)
    
    if ocr_text and len(ocr_text.strip()) >= 50:
        return ocr_text, "ocr"
    elif text and len(text.strip()) > 0:
        # If OCR fails but pdfplumber extracted something, return pdfplumber output with notice
        return text, "pdfplumber (partial)"
    else:
        return ocr_text or text or "", "ocr (failed)"
