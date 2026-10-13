import re
from typing import List
from .schemas import ClauseItem

CLAUSE_BOUNDARY_REGEX = re.compile(
    r'(?=^\s*(?:(?:CLAUSE|SECTION|ARTICLE)\s+[\dA-Za-z.]+|WHEREAS\b|IN\s+WITNESS\s+WHEREOF\b)|^\s*\d+(?:\.\d+)+\.?\s+|^\s*\d+\.\s+|^\s*\([a-z0-9]+\)\s+)',
    re.MULTILINE | re.IGNORECASE
)

def segment_text_into_clauses(text: str) -> List[ClauseItem]:
    """
    Splits legal document text into clauses using regex patterns matching standard numbering
    and line-start headers (e.g. '1.', '1.1', 'Clause 3', line-start 'WHEREAS', 'Section X').
    Does NOT split on mid-sentence conjunctions such as lowercase ', whereas '.
    """
    if not text or not text.strip():
        return []

    clean_text = text.replace('\r\n', '\n')
    raw_splits = CLAUSE_BOUNDARY_REGEX.split(clean_text)
    
    clauses: List[ClauseItem] = []
    idx = 1
    
    for split in raw_splits:
        chunk = split.strip()
        if not chunk:
            continue
            
        if len(chunk) < 15 and not re.search(r'\w{3,}', chunk):
            continue

        header_match = re.match(
            r'^(?:CLAUSE|SECTION|ARTICLE)\s+[\dA-Z.]+|^\d+(?:\.\d+)+\.?|^\d+\.|^WHEREAS\b|^IN\s+WITNESS\s+WHEREOF\b',
            chunk, re.IGNORECASE
        )
        
        if header_match:
            clause_id = header_match.group(0).strip()
        else:
            clause_id = f"Clause {idx}"
            
        clauses.append(ClauseItem(clause_id=clause_id, text=chunk))
        idx += 1

    if len(clauses) <= 1:
        paragraphs = [p.strip() for p in clean_text.split('\n\n') if p.strip()]
        if len(paragraphs) > 1:
            clauses = []
            for i, p in enumerate(paragraphs, 1):
                clauses.append(ClauseItem(clause_id=f"Paragraph {i}", text=p))

    return clauses
