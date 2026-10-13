import json
import logging
import re
import time
from typing import List, Optional, Tuple, Dict, Any
from .config import GEMINI_API_KEY, ALLOW_HEURISTIC_FALLBACK
from .schemas import FlaggedClause, GroundingExample, ClauseItem
from .translator import translate_clause_analysis_to_hindi, translate_text_to_hindi

logger = logging.getLogger(__name__)

genai_client = None
if GEMINI_API_KEY:
    try:
        from google import genai
        genai_client = genai.Client(api_key=GEMINI_API_KEY)
        logger.info("Gemini client initialized successfully with google.genai SDK.")
    except Exception as e1:
        try:
            import google.generativeai as legacy_genai
            legacy_genai.configure(api_key=GEMINI_API_KEY)
            genai_client = legacy_genai
            logger.info("Gemini client initialized with legacy google.generativeai SDK.")
        except Exception as e2:
            logger.warning(f"Could not initialize Gemini SDK: {e1} | {e2}")

CLAUSE_TITLES = {
    "indemnity": "Indemnity & Hold Harmless",
    "non_compete": "Non-Compete / Restraint of Trade",
    "dispute_resolution": "Arbitration & Dispute Resolution",
    "penalty": "Penalty & Liquidated Damages",
    "termination": "Unilateral Termination"
}

def call_gemini_json(prompt: str, model_name: str = "gemini-3.6-flash") -> Optional[Dict[str, Any]]:
    """Helper to query Gemini API with retries and rate limit handling."""
    if not genai_client:
        if not ALLOW_HEURISTIC_FALLBACK:
            raise RuntimeError("GEMINI_API_KEY is required for Gemini classification but is not configured.")
        logger.info("call_gemini_json skipped: genai_client is None. Using heuristic fallback.")
        return None

    models_to_try = [model_name]
    
    for mod in models_to_try:
        for attempt in range(4):
            try:
                if hasattr(genai_client, 'models'):
                    response = genai_client.models.generate_content(
                        model=mod,
                        contents=prompt,
                        config={'response_mime_type': 'application/json'}
                    )
                    text = response.text
                else:
                    model = genai_client.GenerativeModel(mod)
                    response = model.generate_content(prompt)
                    text = response.text

                logger.info(f"Gemini API Response received from model '{mod}'. Raw text: {text[:200]}...")

                cleaned_text = re.sub(r'^```json\s*', '', text.strip(), flags=re.MULTILINE)
                cleaned_text = re.sub(r'```$', '', cleaned_text.strip(), flags=re.MULTILINE)
                parsed_json = json.loads(cleaned_text)
                parsed_json["_raw_response"] = text
                parsed_json["_model_used"] = mod
                return parsed_json
            except Exception as e:
                err_str = str(e)
                logger.warning(f"Gemini API call attempt {attempt+1} with model '{mod}' failed: {err_str}")
                if "GenerateRequestsPerDayPerProjectPerModel" in err_str or "limit: 20" in err_str:
                    logger.info("Daily API quota reached (20 RPD). Falling back immediately.")
                    break
                elif "429" in err_str or "503" in err_str or "RESOURCE_EXHAUSTED" in err_str or "UNAVAILABLE" in err_str:
                    logger.info("Rate limit / service busy (429/503). Pausing 16 seconds before retrying...")
                    time.sleep(16)
                else:
                    time.sleep(2)
                continue

    if not ALLOW_HEURISTIC_FALLBACK:
        raise RuntimeError("Gemini API call failed for all retries and ALLOW_HEURISTIC_FALLBACK is False.")

    return None

def classify_and_explain_clause(
    clause: ClauseItem,
    grounding_examples: List[GroundingExample]
) -> Optional[FlaggedClause]:
    """
    Classifies clause using Gemini with ChromaDB retrieved examples as grounding context (English only).
    Translates the English explanation and risk_reason at the output layer using local IndicTrans2
    (zero Gemini calls for translation) and enforces fixed legal glossary terms.
    """
    examples_str = "\n".join([
        f"- [{eg.category.upper()}] (Type: {eg.clause_type}): \"{eg.text}\""
        for eg in grounding_examples
    ])

    prompt = f"""You are an expert legal AI reviewer.
Analyze the following document clause using STRICTLY the grounding reference examples provided below. Do NOT use free opinion or ungrounded judgment.

DOCUMENT CLAUSE TO ANALYZE:
"{clause.text}"

GROUNDING REFERENCE EXAMPLES RETRIEVED FROM VECTOR STORE:
{examples_str}

TASK:
1. Determine if the clause matches one of these 5 clause types:
   - "indemnity"
   - "non_compete"
   - "dispute_resolution"
   - "penalty"
   - "termination"
   - "other"
2. Compare the clause to the grounding reference examples:
   - If it resembles the ONE-SIDED examples or creates unreasonable liability, assign classification = "flag-worthy".
   - If it resembles the STANDARD examples or is fair/mutual, assign classification = "standard".
3. If classification is "flag-worthy":
   - Provide a concise plain-English explanation of what the clause means (2 sentences max).
   - Explain why it is risky or unfair to the individual (2 sentences max).
   - Assign severity: "High", "Medium", or "Low".

Return ONLY a JSON object with this exact structure:
{{
  "clause_type": "indemnity|non_compete|dispute_resolution|penalty|termination|other",
  "classification": "standard|flag-worthy",
  "explanation": "...",
  "risk_reason": "...",
  "severity": "High|Medium|Low"
}}
"""

    res = call_gemini_json(prompt)

    if not res:
        if ALLOW_HEURISTIC_FALLBACK:
            res = fallback_heuristic_classification(clause, grounding_examples)
        else:
            raise RuntimeError("Gemini API response failed and ALLOW_HEURISTIC_FALLBACK is disabled.")

    if not res or res.get("classification") != "flag-worthy":
        return None

    clause_type = res.get("clause_type", "other")
    if clause_type not in CLAUSE_TITLES and clause_type != "other":
        clause_type = "other"

    title = CLAUSE_TITLES.get(clause_type, "Potentially Risky Clause")

    explanation_en = res.get("explanation", "This clause contains terms that may create one-sided obligations.")
    risk_reason_en = res.get("risk_reason", "It exposes you to disproportionate liability or limits your legal rights.")

    # Translate English output to Hindi via local IndicTrans2 (zero Gemini calls)
    explanation_hi, risk_reason_hi = translate_clause_analysis_to_hindi(explanation_en, risk_reason_en)

    return FlaggedClause(
        clause_id=clause.clause_id,
        clause_type=clause_type,
        title=title,
        original_text=clause.text,
        classification="flag-worthy",
        explanation=explanation_en,
        risk_reason=risk_reason_en,
        explanation_hi=explanation_hi,
        risk_reason_hi=risk_reason_hi,
        severity=res.get("severity", "Medium"),
        priority_score=0.0,
        grounding_examples=grounding_examples
    )

def fallback_heuristic_classification(clause: ClauseItem, grounding_examples: List[GroundingExample]) -> Dict[str, Any]:
    """Fallback rule-based classifier when Gemini API is unavailable (Dev Mode Only). Returns English only."""
    text_lower = clause.text.lower()
    nearest_one_sided = [eg for eg in grounding_examples if eg.category == "one_sided"]
    
    is_one_sided_phrase = any(w in text_lower for w in [
        "indemnify and hold harmless", "unconditionally indemnify", "sole discretion",
        "shall not engage in", "perpetually restrained", "exclusive right to choose",
        "waives all rights", "immediate penalty", "punitive penalty", "without notice",
        "terminate at any time"
    ])

    if nearest_one_sided or is_one_sided_phrase:
        clause_type = "other"
        if "indemn" in text_lower:
            clause_type = "indemnity"
        elif "compete" in text_lower or "restraint" in text_lower or "solicit" in text_lower:
            clause_type = "non_compete"
        elif "arbitrat" in text_lower or "jurisdiction" in text_lower or "court" in text_lower or "dispute" in text_lower:
            clause_type = "dispute_resolution"
        elif "penalty" in text_lower or "damages" in text_lower or "forfeit" in text_lower:
            clause_type = "penalty"
        elif "terminat" in text_lower or "evict" in text_lower or "cancel" in text_lower:
            clause_type = "termination"
            
        if clause_type == "other" and grounding_examples:
            clause_type = grounding_examples[0].clause_type

        return {
            "clause_type": clause_type,
            "classification": "flag-worthy",
            "explanation": f"This {clause_type.replace('_', ' ')} clause establishes strict requirements or obligations.",
            "risk_reason": "It resembles one-sided sample terms that may unfairly penalize or burden you.",
            "severity": "High" if "penalty" in clause_type or "indemnity" in clause_type else "Medium"
        }
    
    return {
        "clause_type": "other",
        "classification": "standard",
        "explanation": "",
        "risk_reason": "",
        "severity": "Low"
    }


def generate_document_summary(full_text: str, total_clauses: int, flagged_count: int) -> Tuple[str, str]:
    """Generate high-level executive summary of the document in English, then translate to Hindi via local IndicTrans2."""
    summary_en = ""
    if genai_client:
        prompt = f"""Synthesize a clear, 3-sentence executive summary for the following legal document text in English.

DOCUMENT TEXT:
"{full_text[:3000]}"

State:
1. What type of legal agreement this appears to be.
2. The core purpose and key obligations.
3. A brief summary of risk level based on having {flagged_count} flagged clauses out of {total_clauses} total clauses.

Return ONLY a JSON object:
{{
  "summary_en": "..."
}}
"""
        models_to_try = ["gemini-3.6-flash"]
        for mod in models_to_try:
            for attempt in range(4):
                try:
                    if hasattr(genai_client, 'models'):
                        res = genai_client.models.generate_content(
                            model=mod,
                            contents=prompt,
                            config={'response_mime_type': 'application/json'}
                        )
                        raw_text = res.text
                    else:
                        model = genai_client.GenerativeModel(mod)
                        res = model.generate_content(prompt)
                        raw_text = res.text

                    cleaned_text = re.sub(r'^```json\s*', '', raw_text.strip(), flags=re.MULTILINE)
                    cleaned_text = re.sub(r'```$', '', cleaned_text.strip(), flags=re.MULTILINE)
                    parsed = json.loads(cleaned_text)
                    summary_en = parsed.get("summary_en", "")
                    if summary_en:
                        break
                except Exception as e:
                    err_str = str(e)
                    logger.warning(f"Document summary generation attempt {attempt+1} with '{mod}' failed: {err_str}")
                    if "429" in err_str or "503" in err_str or "RESOURCE_EXHAUSTED" in err_str or "UNAVAILABLE" in err_str:
                        time.sleep(10)
                    else:
                        time.sleep(2)
            if summary_en:
                break

    if not summary_en:
        if not ALLOW_HEURISTIC_FALLBACK:
            raise RuntimeError("Gemini API is required for document summary generation but is not configured.")
        summary_en = f"This document contains {total_clauses} segmented clauses with {flagged_count} flagged risk items requiring review. Please inspect the detailed clause breakdown below."

    summary_hi = translate_text_to_hindi(summary_en)
    return summary_en, summary_hi

