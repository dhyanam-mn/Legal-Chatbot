import os
import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path

# Enforce strict zero-heuristic fallback
os.environ["ALLOW_HEURISTIC_FALLBACK"] = "false"

# Ensure backend root is on sys.path
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.config import (
    MANDATORY_DISCLAIMER,
    MANDATORY_DISCLAIMER_HI,
    MANDATORY_DISCLAIMER_TA,
)
from app.parser import parse_pdf
from app.segmenter import segment_text_into_clauses
from app.vector_store import get_vector_store
from app.classifier import (
    classify_and_explain_clause,
    generate_document_summary,
    NO_STATUTE_MESSAGE,
    NO_STATUTE_MESSAGE_HI,
    NO_STATUTE_MESSAGE_TA,
)
from app.ranker import rank_flagged_clauses
from app.schemas import ClientIntakeContext


DEMO_DOCUMENTS = [
    {
        "filename": "demo_rental_one_sided.pdf",
        "doc_type": "rental_agreement",
        "title": "Synthetic Residential Lease (One-Sided)",
        "expected_category": "one_sided",
    },
    {
        "filename": "demo_employment_one_sided.pdf",
        "doc_type": "employment_contract",
        "title": "Synthetic Executive Employment Agreement (One-Sided)",
        "expected_category": "one_sided",
    },
    {
        "filename": "demo_loan_one_sided.pdf",
        "doc_type": "loan_agreement",
        "title": "Synthetic Commercial Loan Agreement (One-Sided)",
        "expected_category": "one_sided",
    },
    {
        "filename": "demo_rental_fair.pdf",
        "doc_type": "rental_agreement",
        "title": "Synthetic Residential Lease (Standard / Fair)",
        "expected_category": "fair",
    },
    {
        "filename": "demo_employment_fair.pdf",
        "doc_type": "employment_contract",
        "title": "Synthetic Employment Agreement (Standard / Fair)",
        "expected_category": "fair",
    },
]


def serialize_model(obj):
    """Serialize Pydantic models across versions."""
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    elif hasattr(obj, "dict"):
        return obj.dict()
    return obj


def run_demo():
    generation_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
    print(f"\n=======================================================")
    print(f"STARTING LEGAL CHATBOT DEMO RUNNER — {generation_date}")
    print(f"ALLOW_HEURISTIC_FALLBACK={os.getenv('ALLOW_HEURISTIC_FALLBACK')}")
    print(f"=======================================================\n")

    store = get_vector_store()
    demo_dir = BASE_DIR / "sample_pdfs" / "demo"
    output_dir = BASE_DIR / "demo_output"
    output_dir.mkdir(parents=True, exist_ok=True)

    summary_table_rows = []
    all_demo_results = {}

    for doc_meta in DEMO_DOCUMENTS:
        fname = doc_meta["filename"]
        pdf_path = demo_dir / fname
        doc_type = doc_meta["doc_type"]
        title = doc_meta["title"]
        expected_cat = doc_meta["expected_category"]

        print(f"\n>>> Processing {fname} ({title}) ...")
        if not pdf_path.exists():
            raise FileNotFoundError(f"Missing demo PDF: {pdf_path}")

        pdf_bytes = pdf_path.read_bytes()
        raw_text, parse_method = parse_pdf(pdf_bytes)
        clauses = segment_text_into_clauses(raw_text)
        print(f"    Segmented {len(clauses)} clauses (method: {parse_method})")

        flagged_clauses = []
        for idx, clause in enumerate(clauses, start=1):
            print(f"    Evaluating Clause {idx}/{len(clauses)}: {clause.clause_id} ...")
            grounding = store.query_nearest_references(clause.text, top_k=4)
            flagged = classify_and_explain_clause(clause, grounding)
            if flagged:
                flagged_clauses.append(flagged)
                print(f"      -> FLAGGED: {flagged.clause_type} ({flagged.title}) [Severity: {flagged.severity}]")
            else:
                print(f"      -> STANDARD: Not flagged")
            time.sleep(1.0)  # gentle pacing against free-tier rate limits

        # Client Intake: Salaried, Dependents=Yes, Medium Income
        intake = ClientIntakeContext(
            employment_type="salaried",
            has_dependents=True,
            dependents_count=2,
            income_bracket="medium",
            document_type=doc_type,
        )

        ranked_clauses = rank_flagged_clauses(flagged_clauses, intake)

        print(f"    Generating document executive summary...")
        summary_en, summary_hi, summary_ta = generate_document_summary(
            raw_text, len(clauses), len(ranked_clauses)
        )

        doc_result = {
            "generation_date": generation_date,
            "filename": fname,
            "document_type": doc_type,
            "title": title,
            "expected_category": expected_cat,
            "parse_method": parse_method,
            "total_clauses": len(clauses),
            "flagged_count": len(ranked_clauses),
            "summary_en": summary_en,
            "summary_hi": summary_hi,
            "summary_ta": summary_ta,
            "client_intake": serialize_model(intake),
            "flagged_clauses": [serialize_model(c) for c in ranked_clauses],
        }

        all_demo_results[fname] = doc_result

        # Save individual JSON
        json_out_path = output_dir / f"{Path(fname).stem}.json"
        with open(json_out_path, "w", encoding="utf-8") as f:
            json.dump(doc_result, f, indent=2, ensure_ascii=False)
        print(f"    Saved individual document output to: {json_out_path}")

        # Summary Table entry
        false_positive_status = "N/A (One-sided)"
        if expected_cat == "fair":
            false_positive_status = f"PASS (0 flags)" if len(ranked_clauses) == 0 else f"{len(ranked_clauses)} flags (check)"

        summary_table_rows.append({
            "document": fname,
            "title": title,
            "clauses": len(clauses),
            "flagged": len(ranked_clauses),
            "fp_check": false_positive_status,
        })

    # Save aggregated summary JSON
    summary_json_path = output_dir / "demo_results_summary.json"
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generation_date": generation_date,
                "summary_table": summary_table_rows,
                "documents": all_demo_results,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"\nSaved aggregated demo summary to: {summary_json_path}")

    # Build Markdown Report
    md_lines = []
    md_lines.append(f"# Legal Document Chatbot — Demonstration Audit Report")
    md_lines.append(f"**Generated:** {generation_date}")
    md_lines.append(f"**Configuration:** `ALLOW_HEURISTIC_FALLBACK=false` | Client Intake: `salaried`, `has_dependents=True (count=2)`, `income_bracket=medium`\n")

    md_lines.append(f"## 1. Summary Matrix & False-Positive Audit")
    md_lines.append(f"| Document | Title | Total Clauses | Flagged Clauses | False-Positive Check (Fair Docs) |")
    md_lines.append(f"| :--- | :--- | :---: | :---: | :---: |")
    for row in summary_table_rows:
        md_lines.append(f"| `{row['document']}` | {row['title']} | {row['clauses']} | **{row['flagged']}** | {row['fp_check']} |")
    md_lines.append("\n---\n")

    md_lines.append(f"## 2. Document-by-Document Detailed Findings\n")

    for doc_meta in DEMO_DOCUMENTS:
        fname = doc_meta["filename"]
        res = all_demo_results[fname]
        md_lines.append(f"### {res['title']} (`{fname}`)")
        md_lines.append(f"- **Document Type:** `{res['document_type']}` | **Clauses Segmented:** {res['total_clauses']} | **Risk Items Flagged:** {res['flagged_count']}")
        md_lines.append(f"\n#### Executive Summary")
        md_lines.append(f"- **English:** {res['summary_en']}")
        md_lines.append(f"- **Hindi (हिंदी):** {res['summary_hi']}")
        md_lines.append(f"- **Tamil (தமிழ்):** {res['summary_ta']}\n")

        if not res["flagged_clauses"]:
            md_lines.append(f"> [!NOTE]\n> **Balanced / Fair Contract Result:** Zero clauses flagged. The agreement contains standard, mutual, and non-exploitative covenants. All covenants adhere to typical balanced standards.\n")
        else:
            md_lines.append(f"#### Ranked Flagged Clauses ({len(res['flagged_clauses'])} items)")
            for idx, c in enumerate(res["flagged_clauses"], start=1):
                md_lines.append(f"##### {idx}. [{c['clause_id']}] {c['title']} — Severity: `{c['severity']}` (Priority Score: {c['priority_score']:.1f})")
                md_lines.append(f"**Original Clause Text:**")
                md_lines.append(f"> *\"{c['original_text']}\"*\n")

                md_lines.append(f"**Plain-Language Explanation & Risk Reason:**")
                md_lines.append(f"- **English Explanation:** {c['explanation']}")
                md_lines.append(f"- **English Risk Reason:** {c['risk_reason']}")
                md_lines.append(f"- **Hindi Explanation (हिंदी व्याख्या):** {c.get('explanation_hi', '')}")
                md_lines.append(f"- **Hindi Risk Reason (हिंदी जोखिम कारण):** {c.get('risk_reason_hi', '')}")
                md_lines.append(f"- **Tamil Explanation (தமிழ் விளக்கம்):** {c.get('explanation_ta', '')}")
                md_lines.append(f"- **Tamil Risk Reason (தமிழ் ஆபத்து காரணம்):** {c.get('risk_reason_ta', '')}\n")

                md_lines.append(f"**Legal Basis:**")
                cits = c.get("statutory_citations", [])
                if cits:
                    for cit in cits:
                        md_lines.append(f"- **[{cit['provision_id']}] {cit['act']} — {cit['section']} ({cit['title']})**")
                        md_lines.append(f"  - *Reason (EN):* {cit['reason']}")
                        if cit.get("reason_hi"):
                            md_lines.append(f"  - *Reason (HI):* {cit['reason_hi']}")
                        if cit.get("reason_ta"):
                            md_lines.append(f"  - *Reason (TA):* {cit['reason_ta']}")
                        if cit.get("statutory_text"):
                            md_lines.append(f"  - *Verbatim Statutory Text (English):*")
                            md_lines.append(f"    > \"{cit['statutory_text'][:380]}...\"")
                else:
                    msg = c.get("legal_basis_message") or NO_STATUTE_MESSAGE
                    msg_hi = c.get("legal_basis_message_hi") or NO_STATUTE_MESSAGE_HI
                    msg_ta = c.get("legal_basis_message_ta") or NO_STATUTE_MESSAGE_TA
                    md_lines.append(f"- **Status:** {msg}")
                    md_lines.append(f"- *Hindi (हिंदी):* {msg_hi}")
                    md_lines.append(f"- *Tamil (தமிழ்):* {msg_ta}\n")

                alts = c.get("standard_alternatives", [])
                if alts:
                    md_lines.append(f"**How this is typically written (Typical Balanced Phrasing):**")
                    for a_idx, alt in enumerate(alts, start=1):
                        md_lines.append(f"{a_idx}. \"{alt}\"")
                    md_lines.append("")

                md_lines.append(f"**Mandatory Legal Disclaimer:**")
                md_lines.append(f"- **EN:** {c.get('typical_phrasing_disclaimer') or MANDATORY_DISCLAIMER}")
                md_lines.append(f"- **HI:** {c.get('typical_phrasing_disclaimer_hi') or MANDATORY_DISCLAIMER_HI}")
                md_lines.append(f"- **TA:** {c.get('typical_phrasing_disclaimer_ta') or MANDATORY_DISCLAIMER_TA}\n")

        md_lines.append("\n---\n")

    md_lines.append(f"## 3. Limitations & Disclaimers")
    md_lines.append(f"- **Synthetic Test Documents:** The analyzed documents are synthetic demonstrative contracts crafted for automated testing and software demonstration; they do not represent real-world legal agreements or actual persons.")
    md_lines.append(f"- **English Input Only:** The document parsing, segmentation, and semantic grounding pipeline accepts and processes contracts written in English.")
    md_lines.append(f"- **Automated Translations (Hindi and Tamil):** Explanations, risk reasons, summaries, and citations in Hindi and Tamil are generated using local neural machine translation (IndicTrans2) and reviewed solely by automated glossary rules. They are intended for linguistic accessibility and have not undergone individual manual native-speaker legal certification.")
    md_lines.append(f"- **Not Legal Advice:** The explanations, risk ratings, priority scores, and statutory references provided by this software are for educational and informational purposes only. This tool does not constitute legal advice and cannot substitute for qualified legal counsel.")

    full_md_report = "\n".join(md_lines)

    # Save to demo_output/demo_report.md
    report_out_path = output_dir / "demo_report.md"
    report_out_path.write_text(full_md_report, encoding="utf-8")
    print(f"Saved demo report to: {report_out_path}")

    # Also save a copy at project root for direct convenience
    root_report_path = BASE_DIR / "demo_report.md"
    root_report_path.write_text(full_md_report, encoding="utf-8")
    print(f"Saved demo report to: {root_report_path}")

    print("\n=======================================================")
    print("DEMO EXECUTION COMPLETE!")
    print("=======================================================\n")
    return all_demo_results


if __name__ == "__main__":
    run_demo()
