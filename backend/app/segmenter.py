import re
from typing import List, Optional
from .schemas import ClauseItem


def detect_document_language(text: str) -> str:
    """
    Detect document language from Unicode script share:
    - Devanagari (\u0900-\u097F) -> 'hi'
    - Tamil (\u0B80-\u0BFF) -> 'ta'
    - else -> 'en'
    """
    if not text or not text.strip():
        return "en"

    devanagari_count = len(re.findall(r'[\u0900-\u097F]', text))
    tamil_count = len(re.findall(r'[\u0B80-\u0BFF]', text))
    latin_count = len(re.findall(r'[a-zA-Z]', text))

    total_chars = devanagari_count + tamil_count + latin_count
    if total_chars == 0:
        return "en"

    deva_share = devanagari_count / total_chars
    tamil_share = tamil_count / total_chars

    if deva_share > 0.15 and devanagari_count > tamil_count:
        return "hi"
    elif tamil_share > 0.15 and tamil_count > devanagari_count:
        return "ta"
    else:
        return "en"


CLAUSE_BOUNDARY_REGEX = re.compile(
    r'(?='
    r'^\s*(?:(?:CLAUSE|SECTION|ARTICLE)\s+[\dA-Za-z.]+|WHEREAS\b|IN\s+WITNESS\s+WHEREOF\b)'
    r'|^\s*(?:(?:खंड|खण्ड|धारा|अनुच्छेद)\s+[\d०-९A-Za-z.]+)'
    r'|^\s*(?:(?:பிரிவு|சரத்து|உறுப்பு)\s+[\d௧-௯A-Za-z.]+)'
    r'|^\s*\d+(?:\.\d+)+\.?\s+'
    r'|^\s*\d+\.\s+'
    r'|^\s*[०-९]+(?:\.[०-९]+)*\.?\s+'
    r'|^\s*[௧-௯]+(?:\.[௧-௯]+)*\.?\s+'
    r'|^\s*\([a-z0-9]+\)\s+'
    r')',
    re.MULTILINE | re.IGNORECASE
)


def segment_text_into_clauses(text: str, detected_language: Optional[str] = None) -> List[ClauseItem]:
    """
    Splits legal document text into clauses using regex patterns matching standard numbering
    and line-start headers in English, Hindi (खंड, धारा, अनुच्छेद, 3., ३.) and Tamil (பிரிவு, சரத்து, உறுப்பு, 3.).
    Does NOT split on mid-sentence conjunctions such as lowercase ', whereas '.
    Preserves exact English segmentation behavior without regression.
    """
    if not text or not text.strip():
        return []

    doc_lang = detected_language if detected_language is not None else detect_document_language(text)

    clean_text = text.replace('\r\n', '\n')
    raw_splits = CLAUSE_BOUNDARY_REGEX.split(clean_text)

    clauses: List[ClauseItem] = []
    idx = 1

    for split in raw_splits:
        chunk = split.strip()
        if not chunk:
            continue

        # Ignore tiny non-clause fragments
        if len(chunk) < 15 and not re.search(r'[\w\u0900-\u097F\u0B80-\u0BFF]{3,}', chunk):
            continue

        header_match = re.match(
            r'^(?:CLAUSE|SECTION|ARTICLE)\s+[\dA-Z.]+'
            r'|^(?:खंड|खण्ड|धारा|अनुच्छेद)\s+[\d०-९A-Za-z.]+'
            r'|^(?:பிரிவு|சரத்து|உறுப்பு)\s+[\d௧-௯A-Za-z.]+'
            r'|^\d+(?:\.\d+)+\.?'
            r'|^\d+\.'
            r'|^[०-९]+(?:\.[०-९]+)*\.?'
            r'|^[௧-௯]+(?:\.[௧-௯]+)*\.?'
            r'|^WHEREAS\b|^IN\s+WITNESS\s+WHEREOF\b',
            chunk, re.IGNORECASE
        )

        if header_match:
            clause_id = header_match.group(0).strip()
        else:
            clause_id = f"Clause {idx}"

        clauses.append(ClauseItem(clause_id=clause_id, text=chunk, detected_language=doc_lang))
        idx += 1

    if len(clauses) <= 1:
        paragraphs = [p.strip() for p in clean_text.split('\n\n') if p.strip()]
        if len(paragraphs) > 1:
            clauses = []
            for i, p in enumerate(paragraphs, 1):
                clauses.append(ClauseItem(clause_id=f"Paragraph {i}", text=p, detected_language=doc_lang))

    return clauses
