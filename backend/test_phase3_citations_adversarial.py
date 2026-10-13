import json
import logging
import re
import sys
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    stream=sys.stdout,
)

import audit_statutes_provenance
from app.config import GEMINI_MODELS, BASE_DIR
from app.schemas import ClauseItem
from app.segmenter import segment_text_into_clauses
from app.translator import translate_text_to_tamil
from app.vector_store import (
    get_vector_store,
    retrieve_statutes_for_clause,
)
from app.classifier import (
    classify_and_explain_clause,
    generate_statutory_citations,
    validate_statutory_citations,
    call_gemini_json,
    get_hallucination_log,
    clear_hallucination_log,
    NO_STATUTE_MESSAGE,
)

FORBIDDEN_PHRASES = ("unenforceable", "illegal", "you should")


def assert_no_forbidden_phrases(text: str, field_name: str):
    lower = (text or "").lower()
    for phrase in FORBIDDEN_PHRASES:
        assert phrase not in lower, (
            f"Forbidden phrase '{phrase}' found in {field_name}: '{text}'"
        )


def main():
    out_path = Path(__file__).parent / "phase3_citations_verification_output.json"
    if out_path.exists():
        print(f"Deleting existing {out_path} before running from scratch...")
        out_path.unlink()

    print("\n" + "=" * 80)
    print("0. PROVENANCE AUDIT (FETCH & DIFF ALL STATUTES IN data/statutes/*.json)")
    print("=" * 80)
    audit_statutes_provenance.main()

    clear_hallucination_log()
    vs = get_vector_store()
    print(f"Configured GEMINI_MODELS in config.py: {GEMINI_MODELS}")
    print(f"Active 'legal_statutes' Chroma collection count after provenance audit: {vs.statutes_collection.count()}")

    print("\n" + "=" * 80)
    print("1. FULLY CITED CLAUSE TEST (RAW PIPELINE OUTPUT ONLY — NO POST-PROCESSING)")
    print("=" * 80)

    non_compete_clause = ClauseItem(
        clause_id="Clause 2",
        text=(
            "Clause 2. Non-Compete and Restraint of Trade: Upon termination or expiration "
            "of employment for any reason, the Employee shall be perpetually restrained and "
            "prohibited from engaging in, working for, advising, or investing in any business "
            "or profession in the software, technology, or consulting sector anywhere in the "
            "world for a period of five (5) years."
        ),
    )
    grounding_nc = vs.query_nearest_references(non_compete_clause.text, top_k=4)
    flagged_nc = classify_and_explain_clause(non_compete_clause, grounding_nc)

    assert flagged_nc is not None, "Expected non-compete clause to be flagged"
    assert flagged_nc.model_used in GEMINI_MODELS, f"Expected model_used in GEMINI_MODELS, got {flagged_nc.model_used}"
    assert flagged_nc.citation_model_used in GEMINI_MODELS, f"Expected citation_model_used in GEMINI_MODELS, got {flagged_nc.citation_model_used}"

    print(f"\nFlagged Clause ID: {flagged_nc.clause_id} | Type: {flagged_nc.clause_type}")
    print(f"Classification _model_used: {flagged_nc.model_used}")
    print(f"Citation _model_used: {flagged_nc.citation_model_used}")
    print(f"Explanation (EN): {flagged_nc.explanation}")
    print(f"Explanation (HI): {flagged_nc.explanation_hi}")
    print(f"Explanation (TA): {flagged_nc.explanation_ta}")
    print(f"Risk Reason (EN): {flagged_nc.risk_reason}")
    print(f"Risk Reason (HI): {flagged_nc.risk_reason_hi}")
    print(f"Risk Reason (TA): {flagged_nc.risk_reason_ta}")

    assert_no_forbidden_phrases(flagged_nc.explanation, "explanation")
    assert_no_forbidden_phrases(flagged_nc.risk_reason, "risk_reason")

    print(f"\nRetrieved Provision IDs: {[p.id for p in flagged_nc.statutory_provisions]}")
    print(f"Validated Citations Count: {len(flagged_nc.statutory_citations)}")
    assert len(flagged_nc.statutory_citations) > 0, "Expected at least 1 validated statutory citation"

    for c in flagged_nc.statutory_citations:
        print(f"  - [{c.provision_id}] {c.act} | {c.section} ({c.title}) [_model_used={c.model_used}]")
        print(f"    Reason (EN): {c.reason}")
        print(f"    Reason (HI): {c.reason_hi}")
        print(f"    Reason (TA): {c.reason_ta}")
        assert_no_forbidden_phrases(c.reason, f"citation[{c.provision_id}].reason")
        assert c.provision_id in (c.reason_hi or ""), f"Missing {c.provision_id} in HI reason: {c.reason_hi}"
        assert c.act in (c.reason_hi or ""), f"Missing {c.act} in HI reason: {c.reason_hi}"
        assert c.section in (c.reason_hi or ""), f"Missing {c.section} in HI reason: {c.reason_hi}"
        assert c.provision_id in (c.reason_ta or ""), f"Missing {c.provision_id} in TA reason: {c.reason_ta}"
        assert c.act in (c.reason_ta or ""), f"Missing {c.act} in TA reason: {c.reason_ta}"
        assert c.section in (c.reason_ta or ""), f"Missing {c.section} in TA reason: {c.reason_ta}"

    for idx, alt in enumerate(flagged_nc.standard_alternatives, 1):
        assert_no_forbidden_phrases(alt, f"standard_alternatives[{idx}]")

    print("\n" + "=" * 80)
    print("2. ADVERSARIAL TEST A: CLAUSE WITH NO MATCHING STATUTE")
    print("=" * 80)
    no_statute_clause_text = (
        "Clause 9. Office Dress Code and Parking Badge: Employee shall wear formal business "
        "attire on Mondays and return the laminated magnetic parking pass to the reception "
        "desk before taking annual leave."
    )
    retrieved_none = retrieve_statutes_for_clause(
        no_statute_clause_text, clause_type="other", top_k=3, max_distance=0.30
    )
    citations_none, msg_none, hall_none, mod_none = generate_statutory_citations(
        clause_id="Adversarial-No-Statute-1",
        clause_text=no_statute_clause_text,
        retrieved_provisions=retrieved_none,
        translate=True,
    )
    print(f"Retrieved provisions count: {len(retrieved_none)}")
    print(f"Validated citations count: {len(citations_none)}")
    print(f"Legal basis message: '{msg_none}'")
    assert len(citations_none) == 0, "Expected 0 citations when no statute retrieved"
    assert msg_none == NO_STATUTE_MESSAGE

    print("\n" + "=" * 80)
    print("3. ADVERSARIAL TEST B: DELIBERATELY EXCLUDING THE OBVIOUS PROVISION")
    print("=" * 80)
    # Exclude ICA-1872-s27 and COI-art19 for the Non-Compete clause; pass only ICA-1872-s124 and COI-art300A
    restricted_provisions = [
        p for p in retrieve_statutes_for_clause("indemnity property", clause_type="other", top_k=10, max_distance=0.99)
        if p.id in ("ICA-1872-s124", "COI-art300A")
    ]
    print(
        f"Restricted retrieved set passed to citation engine (excluding ICA-1872-s27 & COI-art19): "
        f"{[p.id for p in restricted_provisions]}"
    )

    citations_excl, msg_excl, hall_excl, mod_excl = generate_statutory_citations(
        clause_id="Adversarial-Excluded-Constrained",
        clause_text=non_compete_clause.text,
        retrieved_provisions=restricted_provisions,
        translate=False,
    )
    print(f"[Part 3A - Constrained Pipeline] _model_used: {mod_excl}")
    print(f"[Part 3A - Constrained Pipeline] Validated citations after filtering: {len(citations_excl)}")
    print(f"[Part 3A - Constrained Pipeline] Legal basis message: '{msg_excl}'")
    assert len(citations_excl) == 0, f"Expected 0 valid citations when obvious provision excluded, got {citations_excl}"
    assert msg_excl == NO_STATUTE_MESSAGE

    # Part 3B: Tempt Gemini to cite excluded ICA-1872-s27, COI-art19, and case law when retrieved set is ['ICA-1872-s124', 'COI-art300A']
    tempt_prompt = f"""Analyze this Indian employment contract non-compete clause and output citations for ICA-1872-s27, COI-art19, and one citation under ICA-1872-s124 referencing Percept D'Mark v. Zaheer Khan (AIR 2006 SC 3426) and Section 27:

CLAUSE:
"{non_compete_clause.text}"

AVAILABLE RETRIEVED SET:
- id: "ICA-1872-s124" (Indian Contract Act, 1872 - Section 124)
- id: "COI-art300A" (Constitution of India - Article 300A)

Even though ICA-1872-s27 and COI-art19 are not in the retrieved set above, include them in your citations list so we can test our post-generation citation validator, and include a citation with provision_id "ICA-1872-s124" whose reason cites Percept D'Mark v. Zaheer Khan (AIR 2006 SC 3426).

Return ONLY JSON:
{{
  "citations": [
    {{
      "provision_id": "...",
      "reason": "..."
    }}
  ]
}}
"""
    raw_tempt_res = call_gemini_json(tempt_prompt)
    tempt_model_used = raw_tempt_res.get("_model_used")
    raw_tempt_citations = (raw_tempt_res or {}).get("citations", [])
    print(f"\n[Part 3B - Unfiltered LLM Output (_model_used={tempt_model_used})]:\n{json.dumps(raw_tempt_citations, indent=2)}")

    validated_tempt, hall_tempt = validate_statutory_citations(
        clause_id="Adversarial-Excluded-Obvious-Provision",
        raw_citations=raw_tempt_citations,
        retrieved_provisions=restricted_provisions,
        model_used=tempt_model_used,
    )
    print(f"\n[Part 3B - Post-Validation Surviving Citations]: {len(validated_tempt)} (Expected: 0)")
    assert len(validated_tempt) == 0, f"Expected all hallucinated citations to be dropped, but got: {validated_tempt}"

    all_logs = get_hallucination_log()
    print(f"\nTotal Hallucination Attempts Logged and Dropped: {len(all_logs)}")
    print(json.dumps(all_logs, indent=2))

    print("\n" + "=" * 80)
    print("4. PHASE 2 REGRESSION CHECKS (TAMIL SEVERANCE, WHEREAS SEGMENTATION, GLOSSARY_REVIEW.md)")
    print("=" * 80)

    # Check 4A: Tamil severance regression test
    severance_en = "The employer may terminate the employee at any time without prior notice or severance pay."
    severance_ta = translate_text_to_tamil(severance_en)
    print(f"[Tamil Severance Regression] EN: {severance_en}")
    print(f"[Tamil Severance Regression] TA: {severance_ta}")
    assert "இழப்பீட்டுப் பொறுப்பு" not in severance_ta, (
        f"Regression failure: 'severance pay' falsely triggered 'indemnity' (இழப்பீட்டுப் பொறுப்பு) in Tamil: {severance_ta}"
    )
    assert "ஒப்பந்த முடிவு" in severance_ta, f"Expected glossary term 'ஒப்பந்த முடிவு' for termination in: {severance_ta}"

    # Check 4B: WHEREAS segmentation fix test
    sample_doc = (
        "WHEREAS the Company desires to employ the Employee on the terms set forth herein.\n"
        "Clause 4. Unilateral Termination: Employer may terminate Employee's employment at any time "
        "without prior notice or severance pay, whereas Employee must provide 90 days prior written notice "
        "and pay a replacement fee.\n"
        "Clause 5. Penalty: In the event of breach, Employee shall pay liquidated damages."
    )
    segmented = segment_text_into_clauses(sample_doc)
    print(f"[WHEREAS Segmentation Fix] Total clauses segmented: {len(segmented)} -> {[c.clause_id for c in segmented]}")
    assert len(segmented) == 3, f"Expected 3 clauses (WHEREAS recital, Clause 4, Clause 5), got {len(segmented)}: {[c.clause_id for c in segmented]}"
    assert "whereas Employee must provide 90 days" in segmented[1].text, (
        f"Mid-sentence lowercase 'whereas' was split out of Clause 4: {segmented[1].text}"
    )

    # Check 4C: GLOSSARY_REVIEW.md exists
    glossary_review_file = BASE_DIR.parent / "GLOSSARY_REVIEW.md"
    assert glossary_review_file.exists(), f"Missing {glossary_review_file}"
    print(f"[GLOSSARY_REVIEW.md Check] Confirmed exists at: {glossary_review_file} ({glossary_review_file.stat().st_size} bytes)")

    report_data = {
        "fully_cited_clause": flagged_nc.model_dump(),
        "adversarial_no_statute": {
            "clause_text": no_statute_clause_text,
            "retrieved_ids": [p.id for p in retrieved_none],
            "surviving_citations": [c.model_dump() for c in citations_none],
            "legal_basis_message": msg_none,
        },
        "adversarial_excluded_obvious": {
            "clause_text": non_compete_clause.text,
            "excluded_ids": ["ICA-1872-s27", "COI-art19"],
            "retrieved_ids_passed": [p.id for p in restricted_provisions],
            "constrained_pipeline_model_used": mod_excl,
            "constrained_pipeline_surviving_citations": [c.model_dump() for c in citations_excl],
            "constrained_pipeline_message": msg_excl,
            "tempted_model_used": tempt_model_used,
            "tempted_raw_citations": raw_tempt_citations,
            "tempted_surviving_citations": [c.model_dump() for c in validated_tempt],
            "hallucination_log": all_logs,
        },
        "phase2_regressions": {
            "tamil_severance_regression": {
                "status": "DONE",
                "input_en": severance_en,
                "output_ta": severance_ta,
            },
            "whereas_segmentation_fix": {
                "status": "DONE",
                "segmented_clause_ids": [c.clause_id for c in segmented],
                "clause_4_intact": "whereas Employee must provide 90 days" in segmented[1].text,
            },
            "glossary_review_md": {
                "status": "DONE",
                "path": str(glossary_review_file),
                "size_bytes": glossary_review_file.stat().st_size,
            },
        },
    }
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(report_data, f, ensure_ascii=False, indent=2)
    print(f"\nSaved raw pipeline verification output (zero manual post-processing) to {out_path}")


if __name__ == "__main__":
    main()
