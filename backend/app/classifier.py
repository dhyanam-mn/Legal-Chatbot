import json
import logging
import re
import time
from typing import List, Optional, Tuple, Dict, Any
from .config import (
    GEMINI_API_KEY,
    GEMINI_MODELS,
    MANDATORY_DISCLAIMER,
    MANDATORY_DISCLAIMER_HI,
    MANDATORY_DISCLAIMER_TA,
)
from .schemas import (
    FlaggedClause,
    GroundingExample,
    ClauseItem,
    StatutoryProvision,
    StatutoryCitation,
)
from .translator import (
    translate_clause_analysis_multilingual,
    translate_clause_analysis_to_hindi,
    translate_text_to_hindi,
    translate_text_to_tamil,
    translate_texts_multilingual,
)

logger = logging.getLogger(__name__)

NO_STATUTE_MESSAGE = "No statutory provision retrieved"
NO_STATUTE_MESSAGE_HI = "कोई वैधानिक प्रावधान प्राप्त नहीं हुआ (No statutory provision retrieved)"
NO_STATUTE_MESSAGE_TA = "சட்ட விதி எதுவும் கண்டறியப்படவில்லை (No statutory provision retrieved)"

LEGAL_BASIS_UNAVAILABLE_MESSAGE = "Legal basis unavailable right now"
LEGAL_BASIS_UNAVAILABLE_MESSAGE_HI = "कानूनी आधार अभी उपलब्ध नहीं है (Legal basis unavailable right now)"
LEGAL_BASIS_UNAVAILABLE_MESSAGE_TA = "சட்ட அடிப்படை இப்போது கிடைக்கவில்லை (Legal basis unavailable right now)"

# Audit log of dropped citation hallucination attempts
HALLUCINATION_LOG: List[Dict[str, Any]] = []


def get_hallucination_log() -> List[Dict[str, Any]]:
    return list(HALLUCINATION_LOG)


def clear_hallucination_log() -> None:
    HALLUCINATION_LOG.clear()


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
    "termination": "Unilateral Termination",
    "penal_interest": "Penal / Default Interest",
    "acceleration": "Acceleration of Loan",
    "foreclosure_charges": "Foreclosure / Prepayment Charges",
    "unilateral_interest_change": "Unilateral Interest Rate Change",
    "guarantor_liability": "Guarantor Liability",
    "set_off_lien": "Set-Off / Banker Lien",
    "service_bond": "Service Bond / Mandatory Lock-in",
    "ip_assignment": "IP Assignment / Invention Ownership",
    "notice_period_garden_leave": "Notice Period / Garden Leave Imbalance",
}


def _enforce_descriptive_wording(text: str) -> str:
    """
    Ensures strictly descriptive wording and removes prohibited conclusory or prescriptive terms:
    never states 'unenforceable', 'illegal', or 'you should', and never states that the user's
    clause 'is void'.
    """
    if not text:
        return text
    out = text
    # Replace conclusory phrases about the user's clause
    out = re.sub(
        r"\bmaking\s+this\s+[^.,;]*?\b(?:unenforceable|illegal|void)\b",
        "which is the statutory standard applicable to such terms",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(
        r"\brendering\s+[^.,;]*?\b(?:unenforceable|illegal|void)\b",
        "which defines the statutory scope for such covenants",
        out,
        flags=re.IGNORECASE,
    )
    out = re.sub(r"\bunenforceable\b", "subject to statutory limits", out, flags=re.IGNORECASE)
    out = re.sub(r"\byou\s+should\s+demand\b", "standard agreements typically state", out, flags=re.IGNORECASE)
    out = re.sub(r"\byou\s+should\b", "parties typically", out, flags=re.IGNORECASE)
    out = re.sub(r"\bthis\s+clause\s+is\s+void\b", "this provision addresses such terms", out, flags=re.IGNORECASE)
    return out


def _clean_and_rewrite_statutory_reason(text: str) -> str:
    """
    Ensures descriptive wording and rewrites archaic statutory phrasing into short plain sentences:
    - Never uses 'saving/savings' for statutory 'saving of contract' (replaces with 'protects agreements').
    - Keeps 'Exception' wording in English.
    - Enforces descriptive non-prescriptive wording.
    """
    if not text:
        return text
    out = _enforce_descriptive_wording(text)
    # Remove archaic statutory 'saving of contract' or 'saving' / 'savings'
    out = re.sub(r"\b(?:saving|savings)\s+of\s+contracts?\s+to\s+refer\s+to\s+arbitration\b", "protects agreements to refer disputes to arbitration", out, flags=re.IGNORECASE)
    out = re.sub(r"\b(?:saving|savings)\s+of\s+contracts?\s+to\s+refer\b", "protects agreements to refer", out, flags=re.IGNORECASE)
    out = re.sub(r"\b(?:saving|savings)\s+of\s+contracts?\b", "protects agreements", out, flags=re.IGNORECASE)
    out = re.sub(r"\b(?:saving|savings)\s+of\s+a\s+guarantee\s+agreement\b", "protects guarantee agreements", out, flags=re.IGNORECASE)
    out = re.sub(r"\b(?:saving|savings)\s+of\b", "protects", out, flags=re.IGNORECASE)
    out = re.sub(r"\bproviding\s+a\s+saving\s+for\b", "protecting", out, flags=re.IGNORECASE)
    out = re.sub(r"\ba\s+saving\s+for\b", "protection for", out, flags=re.IGNORECASE)
    out = re.sub(r"\bwith\s+a\s+saving\s+clause\b", "with a protective exception", out, flags=re.IGNORECASE)
    out = re.sub(r"\bsavings?\s+clause\b", "protective exception", out, flags=re.IGNORECASE)
    out = re.sub(r"\bsavings?\b", "protection", out, flags=re.IGNORECASE)
    return out


def call_gemini_json(
    prompt: str,
    model_name: Optional[str] = None,
    allow_rotation: bool = True,
) -> Dict[str, Any]:
    """
    Queries Gemini API using the ordered GEMINI_MODELS list from config.py.
    - Logs the model used on every call and stores it in the returned dict as '_model_used'.
    - If allow_rotation=True, rotates across GEMINI_MODELS on 429/503 quota/availability errors.
    - If allow_rotation=False, attempts only model_name (or GEMINI_MODELS[0]) and raises without rotating to lite models.
    - NEVER falls back to the heuristic classifier.
    """
    if not genai_client:
        raise RuntimeError(
            "GEMINI_API_KEY is required for Gemini API calls; heuristic fallback is disabled."
        )

    if not allow_rotation:
        models_to_try = [model_name or (GEMINI_MODELS[0] if GEMINI_MODELS else "gemini-3.7-flash")]
    else:
        models_to_try = []
        if model_name:
            models_to_try.append(model_name)
        for m in GEMINI_MODELS:
            if m not in models_to_try:
                models_to_try.append(m)

    last_err = None
    for mod in models_to_try:
        for attempt in range(4):
            try:
                if hasattr(genai_client, "models"):
                    response = genai_client.models.generate_content(
                        model=mod,
                        contents=prompt,
                        config={"response_mime_type": "application/json"},
                    )
                    text = response.text
                else:
                    model = genai_client.GenerativeModel(mod)
                    response = model.generate_content(prompt)
                    text = response.text

                cleaned_text = re.sub(r"^```json\s*", "", text.strip(), flags=re.MULTILINE)
                cleaned_text = re.sub(r"```$", "", cleaned_text.strip(), flags=re.MULTILINE)
                parsed_json = json.loads(cleaned_text)
                parsed_json["_raw_response"] = text
                parsed_json["_model_used"] = mod
                logger.info(
                    f"call_gemini_json succeeded: _model_used='{mod}' (attempt {attempt + 1}). "
                    f"Raw snippet: {text[:180]}..."
                )
                return parsed_json
            except Exception as e:
                last_err = e
                err_str = str(e)
                logger.warning(
                    f"call_gemini_json attempt {attempt + 1} with model '{mod}' failed: {err_str}"
                )
                if "GenerateRequestsPerDayPerProjectPerModel" in err_str or "limit: 20" in err_str:
                    logger.info(
                        f"Daily API quota reached (20 RPD) for '{mod}'. Rotating to next model in GEMINI_MODELS..."
                    )
                    break
                elif (
                    "429" in err_str
                    or "503" in err_str
                    or "RESOURCE_EXHAUSTED" in err_str
                    or "UNAVAILABLE" in err_str
                ):
                    pause_s = 4 * (attempt + 1)
                    logger.info(
                        f"Rate limit / service busy (429/503) on '{mod}'. Pausing {pause_s}s before retry/rotation..."
                    )
                    time.sleep(pause_s)
                else:
                    time.sleep(1)
                continue

    raise RuntimeError(
        f"All Gemini models in GEMINI_MODELS ({models_to_try}) failed or exhausted quota. "
        f"Heuristic fallback is strictly disabled. Last error: {last_err}"
    )


def _record_hallucination_attempt(
    clause_id: str,
    attempted_id: str,
    attempted_reason: str,
    allowed_ids: List[str],
    violation_type: str,
    detail: str,
) -> Dict[str, Any]:
    entry = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "clause_id": clause_id,
        "attempted_provision_id": attempted_id,
        "attempted_reason": attempted_reason,
        "allowed_retrieved_ids": allowed_ids,
        "violation_type": violation_type,
        "detail": detail,
        "action": "DROPPED",
    }
    HALLUCINATION_LOG.append(entry)
    logger.warning(
        f"[HALLUCINATION_ATTEMPT] Clause '{clause_id}': DROPPED citation "
        f"(id='{attempted_id}', violation={violation_type}, detail='{detail}'). "
        f"Allowed retrieved IDs: {allowed_ids} | Attempted reason: '{attempted_reason}'"
    )
    return entry


def validate_statutory_citations(
    clause_id: str,
    raw_citations: List[Dict[str, Any]],
    retrieved_provisions: List[StatutoryProvision],
    model_used: Optional[str] = None,
) -> Tuple[List[StatutoryCitation], List[Dict[str, Any]]]:
    """
    Validates every Gemini-generated citation against the retrieved statutory provision set.
    - Drops any citation whose provision_id is not in retrieved_provisions.
    - Drops any citation that references case law or outside sections/articles/statute IDs not in retrieved_provisions.
    - Logs every dropped citation as a [HALLUCINATION_ATTEMPT].
    """
    retrieved_by_id: Dict[str, StatutoryProvision] = {p.id: p for p in retrieved_provisions}
    allowed_ids = list(retrieved_by_id.keys())

    allowed_sec_nums = set()
    for p in retrieved_provisions:
        for m in re.finditer(r"\b(\d+[A-Za-z]?)\b", p.section):
            allowed_sec_nums.add(m.group(1).upper())

    validated: List[StatutoryCitation] = []
    hallucinations: List[Dict[str, Any]] = []
    seen_valid_ids = set()

    for item in raw_citations or []:
        if not isinstance(item, dict):
            continue
        pid = str(item.get("provision_id", "")).strip()
        reason = str(item.get("reason", "")).strip()

        # 1. Validate provision_id is in the retrieved set
        if not pid or pid not in retrieved_by_id:
            h = _record_hallucination_attempt(
                clause_id=clause_id,
                attempted_id=pid or "<MISSING_ID>",
                attempted_reason=reason,
                allowed_ids=allowed_ids,
                violation_type="UNRETRIEVED_PROVISION_ID",
                detail=f"Provision ID '{pid}' is not in the retrieved set {allowed_ids}.",
            )
            hallucinations.append(h)
            continue

        # 2. Reject any case law citation in reason
        case_law_match = re.search(
            r"\b(?:v\.|vs\.|versus|AIR\s+\d{4}|\d+\s+SCC\b|\d+\s+SCR\b|Supreme\s+Court\s+held|High\s+Court\s+held)\b",
            reason,
            flags=re.IGNORECASE,
        )
        if case_law_match:
            h = _record_hallucination_attempt(
                clause_id=clause_id,
                attempted_id=pid,
                attempted_reason=reason,
                allowed_ids=allowed_ids,
                violation_type="CASE_LAW_PROHIBITED",
                detail=f"Case law reference '{case_law_match.group(0)}' detected in citation reason.",
            )
            hallucinations.append(h)
            continue

        # 3. Reject any outside statute ID smuggled into the reason text
        mentioned_ids = re.findall(
            r"\b(?:ICA-\d{4}-s\d+[A-Za-z]?|COI-art\d+[A-Za-z]?|ACA-\d{4}-s\d+[A-Za-z]?|CPA-\d{4}-s\d+[A-Za-z]?)\b",
            reason,
        )
        outside_ids = [mid for mid in mentioned_ids if mid not in retrieved_by_id]
        if outside_ids:
            h = _record_hallucination_attempt(
                clause_id=clause_id,
                attempted_id=pid,
                attempted_reason=reason,
                allowed_ids=allowed_ids,
                violation_type="OUTSIDE_STATUTE_ID_IN_REASON",
                detail=f"Reason references unretrieved statute ID(s) {outside_ids} outside {allowed_ids}.",
            )
            hallucinations.append(h)
            continue

        # 4. Reject any outside Section / Article number smuggled into the reason text
        mentioned_secs = re.findall(
            r"\b(?:Section|Sections|Article|Articles|Sec\.|Art\.|s\.)\s*(\d+[A-Za-z]?)\b",
            reason,
            flags=re.IGNORECASE,
        )
        outside_secs = [s for s in mentioned_secs if s.upper() not in allowed_sec_nums]
        if outside_secs:
            h = _record_hallucination_attempt(
                clause_id=clause_id,
                attempted_id=pid,
                attempted_reason=reason,
                allowed_ids=allowed_ids,
                violation_type="OUTSIDE_SECTION_IN_REASON",
                detail=f"Reason references unretrieved Section/Article number(s) {outside_secs}; allowed: {sorted(allowed_sec_nums)}.",
            )
            hallucinations.append(h)
            continue

        if pid in seen_valid_ids:
            continue

        prov = retrieved_by_id[pid]
        one_line_reason = _clean_and_rewrite_statutory_reason(" ".join(reason.splitlines()).strip())
        if not one_line_reason:
            one_line_reason = (
                f"Under {prov.id}, {prov.section} of the {prov.act} provides the statutory rule regarding {prov.title.lower()}."
            )
        else:
            if prov.act not in one_line_reason:
                one_line_reason = f"Under {prov.id} ({prov.section} of the {prov.act}), {one_line_reason[0].lower() + one_line_reason[1:]}"
            elif prov.id not in one_line_reason:
                one_line_reason = f"Under {prov.id}, {one_line_reason}"

        validated.append(
            StatutoryCitation(
                provision_id=prov.id,
                act=prov.act,
                section=prov.section,
                title=prov.title,
                source_url=prov.source_url,
                statutory_text=prov.text,
                reason=one_line_reason,
                model_used=model_used,
            )
        )
        seen_valid_ids.add(pid)

    return validated, hallucinations


def generate_statutory_citations(
    clause_id: str,
    clause_text: str,
    retrieved_provisions: List[StatutoryProvision],
    translate: bool = True,
) -> Tuple[List[StatutoryCitation], str, List[Dict[str, Any]], Optional[str]]:
    """
    Passes ONLY the retrieved statutory provisions to Gemini, requires output as a list
    of provision_ids + one-line descriptive plain-language reasons, validates every cited ID
    against the retrieved set, drops and logs any hallucination attempts, and translates valid
    reasons into Hindi and Tamil while keeping statute IDs, section numbers, and Act names in English.

    STRICT PINNING: Only ever uses GEMINI_MODELS[0]. Rotation to lite or alternative models
    is strictly prohibited. On failure or quota exhaustion of GEMINI_MODELS[0], returns
    LEGAL_BASIS_UNAVAILABLE_MESSAGE ('Legal basis unavailable right now') and logs _model_used=None.
    """
    if not retrieved_provisions:
        logger.info(f"Clause '{clause_id}': 0 statutory provisions retrieved -> '{NO_STATUTE_MESSAGE}'.")
        return [], NO_STATUTE_MESSAGE, [], None

    provisions_str = "\n".join([
        f"- id: \"{p.id}\" | Act: \"{p.act}\" | Section: \"{p.section}\" | Title: \"{p.title}\"\n  Text: \"{p.text}\""
        for p in retrieved_provisions
    ])

    prompt = f"""You are a strict, descriptive statutory legal citation engine.
You are given a contract clause and a CLOSED list of retrieved statutory provisions.

CONTRACT CLAUSE:
"{clause_text}"

RETRIEVED STATUTORY PROVISIONS (CLOSED SET — DO NOT USE ANY OUTSIDE PROVISION):
{provisions_str}

STRICT INSTRUCTIONS:
1. Pass and cite ONLY provisions from the RETRIEVED STATUTORY PROVISIONS list above that directly address the subject matter of the contract clause.
2. Output each applicable citation with its exact `provision_id` (e.g., "ICA-1872-s27") and a single short plain-English sentence as `reason`.
3. DESCRIPTIVE WORDING AND PLAIN SENTENCES:
   - Output a short plain-English sentence stating what the provision covers (and summarize any proviso or exception retrieved).
   - Write short, clear, simple sentences. Avoid archaic statutory jargon.
   - NEVER use the word "saving" or "savings" for statutory "saving of contract" (instead state "Exception 1 protects agreements to refer disputes to arbitration" or "Exception 1 allows arbitration agreements").
   - Keep any "Exception" wording strictly in English (e.g. write "Exception 1", "Exception 2", do NOT alter the word Exception).
   - Base the description STRICTLY on the text and concepts of the retrieved provision. Do NOT introduce external concepts.
   - NEVER state that the user's contract clause "is void", "is unenforceable", or "is illegal".
   - NEVER use the words "unenforceable", "illegal", or "you should".
   - Example of required descriptive phrasing: "Under ICA-1872-s27, Section 27 of the Indian Contract Act, 1872 provides that agreements restraining a lawful profession, trade, or business are void to that extent; Exception 1 protects agreements not to carry on a business of which good-will is sold."
4. ARBITRATION / DISPUTE RESOLUTION SPECIFIC DIRECTIVE:
   When evaluating arbitration or dispute resolution clauses:
   - Analyze the specific procedural defects in the clause:
     * UNILATERAL APPOINTMENT OF ARBITRATOR: If the clause gives one party exclusive or unilateral authority to appoint or select the arbitrator (e.g. "arbitration selected exclusively by Landlord" or "sole discretion of Employer to appoint arbitrator"), you MUST prefer and cite ACA-1996-s11 (appointment of arbitrators) and/or ACA-1996-s12 (grounds for challenge: independence and impartiality of the arbitrator).
     * PROCEDURAL INEQUALITY: If the clause creates one-sided dispute terms (e.g. one party must arbitrate while the other can sue in court), cite ACA-1996-s18 (equal treatment of parties) and/or ICA-1872-s28 (agreements in restraint of legal proceedings, where Exception 1 protects arbitration agreements).
     * GENERAL ARBITRATION: If it is a balanced arbitration clause, cite ACA-1996-s7 and ICA-1872-s28.
   - Always prioritize provisions that directly address the clause's specific structural defect (e.g., unilateral appointment -> s.11 / s.12) rather than only generic provisions.
5. Explicitly include the `provision_id`, `Section`/`Article` number, and `Act` name in English in the `reason`.
6. Do NOT cite any provision ID, section number, article number, or Act that is NOT in the retrieved list above, even if you know another statute exists.
7. Do NOT cite any case law, court judgments, or external articles.
8. If NONE of the retrieved provisions in the list above are substantively relevant to the contract clause (for example, if only general short-title/commencement provisions or unrelated statutes were retrieved), return an empty list `"citations": []` rather than guessing.

Return ONLY a JSON object with this exact structure:
{{
  "citations": [
    {{
      "provision_id": "EXACT_ID_FROM_RETRIEVED_LIST",
      "reason": "Descriptive one-line summary of what the provision covers, including provision_id, Section/Article number, and Act name."
    }}
  ]
}}
"""

    strongest_model = GEMINI_MODELS[0] if GEMINI_MODELS else "gemini-3.8-flash"
    try:
        res = call_gemini_json(prompt, model_name=strongest_model, allow_rotation=False)
        citation_model_used = res.get("_model_used", strongest_model) if res else strongest_model
    except Exception as e:
        logger.warning(
            f"Pinning enforcement: strongest model '{strongest_model}' failed for citation generation: {e}. "
            f"Returning '{LEGAL_BASIS_UNAVAILABLE_MESSAGE}' and logging _model_used=None. "
            "Rotation to lite or alternative models is strictly prohibited."
        )
        return [], LEGAL_BASIS_UNAVAILABLE_MESSAGE, [], None

    raw_citations: List[Dict[str, Any]] = []
    if res and isinstance(res.get("citations"), list):
        raw_citations = res["citations"]

    validated_citations, hallucinations = validate_statutory_citations(
        clause_id=clause_id,
        raw_citations=raw_citations,
        retrieved_provisions=retrieved_provisions,
        model_used=citation_model_used,
    )

    if not validated_citations:
        return [], NO_STATUTE_MESSAGE, hallucinations, citation_model_used

    if translate:
        reasons_en = [c.reason for c in validated_citations]
        reasons_hi, reasons_ta = translate_texts_multilingual(reasons_en)
        for idx, c in enumerate(validated_citations):
            r_hi = reasons_hi[idx] if idx < len(reasons_hi) else c.reason
            r_ta = reasons_ta[idx] if idx < len(reasons_ta) else c.reason

            # Strict contract guarantee: ensure c.provision_id, c.act, and c.section appear in English
            if c.provision_id not in r_hi:
                r_hi = f"{c.provision_id} - {r_hi}"
            if c.act not in r_hi:
                r_hi = f"{c.act}, {r_hi}"
            if c.section not in r_hi:
                r_hi = f"{c.section}: {r_hi}"

            if c.provision_id not in r_ta:
                r_ta = f"{c.provision_id} - {r_ta}"
            if c.act not in r_ta:
                r_ta = f"{c.act}, {r_ta}"
            if c.section not in r_ta:
                r_ta = f"{c.section}: {r_ta}"

            c.reason_hi = r_hi
            c.reason_ta = r_ta

    return validated_citations, "", hallucinations, citation_model_used


def classify_and_explain_clause(
    clause: ClauseItem,
    grounding_examples: List[GroundingExample],
) -> Optional[FlaggedClause]:
    """
    Classifies clause using Gemini with ChromaDB retrieved examples as grounding context (English only).
    Retrieves statutory provisions from 'legal_statutes', generates and validates descriptive statutory citations,
    attaches descriptive 'How this is typically written' phrasing from reference_clauses.json with
    prepended mandatory disclaimer, and translates explanations + citation reasons via local IndicTrans2.
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
1. Determine if the clause matches one of these supported clause types:
   - "indemnity"
   - "non_compete"
   - "dispute_resolution"
   - "penalty"
   - "termination"
   - "penal_interest"
   - "acceleration"
   - "foreclosure_charges"
   - "unilateral_interest_change"
   - "guarantor_liability"
   - "set_off_lien"
   - "service_bond"
   - "ip_assignment"
   - "notice_period_garden_leave"
   - "other"
2. Compare the clause to the grounding reference examples:
   - If it resembles the ONE-SIDED examples or creates one-sided obligations, assign classification = "flag-worthy".
   - If it resembles the STANDARD examples or is fair/mutual, assign classification = "standard".
3. If classification is "flag-worthy":
   - Provide a concise, strictly descriptive plain-English explanation of what the clause states (2 sentences max).
   - Explain descriptively why it is one-sided or risky to the individual (2 sentences max).
   - NEVER state that the clause is "unenforceable" or "illegal", and NEVER use prescriptive advice like "you should".
   - Assign severity: "High", "Medium", or "Low".

Return ONLY a JSON object with this exact structure:
{{
  "clause_type": "indemnity|non_compete|dispute_resolution|penalty|termination|penal_interest|acceleration|foreclosure_charges|unilateral_interest_change|guarantor_liability|set_off_lien|service_bond|ip_assignment|notice_period_garden_leave|other",
  "classification": "standard|flag-worthy",
  "explanation": "...",
  "risk_reason": "...",
  "severity": "High|Medium|Low"
}}
"""

    res = call_gemini_json(prompt)
    if not res or res.get("classification") != "flag-worthy":
        return None

    model_used = res.get("_model_used")
    clause_type = res.get("clause_type", "other")
    if clause_type not in CLAUSE_TITLES and clause_type != "other":
        clause_type = "other"

    title = CLAUSE_TITLES.get(clause_type, "Potentially Risky Clause")

    explanation_en = _enforce_descriptive_wording(
        res.get("explanation", "This clause contains terms that create one-sided obligations.")
    )
    risk_reason_en = _enforce_descriptive_wording(
        res.get("risk_reason", "It exposes the individual to disproportionate liability or limits contractual rights.")
    )

    # Translate English output to Hindi and Tamil via local IndicTrans2 (zero Gemini calls)
    explanation_hi, risk_reason_hi, explanation_ta, risk_reason_ta = translate_clause_analysis_multilingual(
        explanation_en, risk_reason_en
    )

    from .vector_store import retrieve_statutes_for_clause, get_standard_alternatives
    statutory_provisions = retrieve_statutes_for_clause(
        clause.text, clause_type=clause_type, top_k=3
    )

    statutory_citations, legal_basis_msg, _, citation_model_used = generate_statutory_citations(
        clause_id=clause.clause_id,
        clause_text=clause.text,
        retrieved_provisions=statutory_provisions,
        translate=True,
    )

    standard_alternatives = get_standard_alternatives(clause_type)

    if legal_basis_msg == LEGAL_BASIS_UNAVAILABLE_MESSAGE:
        msg_hi = LEGAL_BASIS_UNAVAILABLE_MESSAGE_HI
        msg_ta = LEGAL_BASIS_UNAVAILABLE_MESSAGE_TA
    elif legal_basis_msg:
        msg_hi = NO_STATUTE_MESSAGE_HI
        msg_ta = NO_STATUTE_MESSAGE_TA
    else:
        msg_hi = ""
        msg_ta = ""

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
        explanation_ta=explanation_ta,
        risk_reason_ta=risk_reason_ta,
        severity=res.get("severity", "Medium"),
        priority_score=0.0,
        model_used=model_used,
        citation_model_used=citation_model_used,
        grounding_examples=grounding_examples,
        statutory_provisions=statutory_provisions,
        statutory_citations=statutory_citations,
        legal_basis_message=legal_basis_msg,
        legal_basis_message_hi=msg_hi,
        legal_basis_message_ta=msg_ta,
        typical_phrasing_header="How this is typically written",
        typical_phrasing_disclaimer=MANDATORY_DISCLAIMER,
        typical_phrasing_disclaimer_hi=MANDATORY_DISCLAIMER_HI,
        typical_phrasing_disclaimer_ta=MANDATORY_DISCLAIMER_TA,
        standard_alternatives=standard_alternatives,
    )


def generate_document_summary(full_text: str, total_clauses: int, flagged_count: int) -> Tuple[str, str, str]:
    """Generate high-level executive summary of the document in English via call_gemini_json, then translate to Hindi and Tamil via local IndicTrans2."""
    prompt = f"""Synthesize a clear, 3-sentence descriptive executive summary for the following legal document text in English.

DOCUMENT TEXT:
"{full_text[:3000]}"

State descriptively:
1. What type of legal agreement this appears to be.
2. The core purpose and key obligations.
3. A brief summary of risk level based on having {flagged_count} flagged clauses out of {total_clauses} total clauses.
Do NOT use the words "unenforceable", "illegal", or "you should".

Return ONLY a JSON object:
{{
  "summary_en": "..."
}}
"""
    parsed = call_gemini_json(prompt)
    summary_en = _enforce_descriptive_wording(parsed.get("summary_en", ""))
    if not summary_en:
        summary_en = (
            f"This document contains {total_clauses} segmented clauses with {flagged_count} "
            f"flagged risk items requiring review. Please inspect the detailed clause breakdown below."
        )

    summary_hi = translate_text_to_hindi(summary_en)
    summary_ta = translate_text_to_tamil(summary_en)
    return summary_en, summary_hi, summary_ta
