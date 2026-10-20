import os
import sys
import json
import time
from datetime import datetime, timezone
from pathlib import Path

# Configure utf-8 stdout/stderr for Windows console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

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
from app.segmenter import segment_text_into_clauses, detect_document_language
from app.vector_store import get_vector_store
from app.classifier import (
    classify_and_explain_clause,
    generate_document_summary,
    NO_STATUTE_MESSAGE,
    NO_STATUTE_MESSAGE_HI,
    NO_STATUTE_MESSAGE_TA,
)
from app.ranker import rank_flagged_clauses
from app.schemas import ClientIntakeContext, ClauseItem, FlaggedClause
from app.translator import translate_indic_to_en


DEMO_DOCUMENTS = [
    {
        "filename": "demo_rental_en.pdf",
        "doc_type": "rental_agreement",
        "title": "Synthetic Residential Lease (English - One-Sided)",
        "pair_role": "en_rental",
    },
    {
        "filename": "demo_rental_hi.pdf",
        "doc_type": "rental_agreement",
        "title": "आवासीय पट्टा समझौता (Hindi - One-Sided Residential Lease)",
        "pair_role": "hi_rental",
    },
    {
        "filename": "demo_employment_en.pdf",
        "doc_type": "employment_contract",
        "title": "Synthetic Executive Employment Agreement (English - One-Sided)",
        "pair_role": "en_employment",
    },
    {
        "filename": "demo_employment_ta.pdf",
        "doc_type": "employment_contract",
        "title": "நிர்வாக வேலைவாய்ப்பு ஒப்பந்தம் (Tamil - One-Sided Employment Agreement)",
        "pair_role": "ta_employment",
    },
    {
        "filename": "demo_loan_en.pdf",
        "doc_type": "loan_agreement",
        "title": "Synthetic Commercial Loan Agreement (English - One-Sided)",
        "pair_role": "en_loan",
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

    all_demo_results = {}

    for doc_meta in DEMO_DOCUMENTS:
        fname = doc_meta["filename"]
        pdf_path = demo_dir / fname
        doc_type = doc_meta["doc_type"]
        title = doc_meta["title"]
        pair_role = doc_meta["pair_role"]

        print(f"\n>>> Processing {fname} ({title}) ...")
        json_out_path = output_dir / f"{Path(fname).stem}.json"
        if json_out_path.exists():
            try:
                with open(json_out_path, "r", encoding="utf-8") as f:
                    saved_doc = json.load(f)
                    if saved_doc.get("flagged_clauses"):
                        print(f"    [CACHED] Re-ranking completed document output from: {json_out_path}")
                        intake = ClientIntakeContext(
                            employment_type="salaried",
                            has_dependents=True,
                            dependents_count=2,
                            income_bracket="medium",
                            document_type=doc_type,
                        )
                        raw_flagged = [FlaggedClause(**c) for c in saved_doc["flagged_clauses"]]
                        ranked_clauses = rank_flagged_clauses(raw_flagged, intake)
                        saved_doc["flagged_clauses"] = [serialize_model(c) for c in ranked_clauses]
                        saved_doc["generation_date"] = generation_date
                        with open(json_out_path, "w", encoding="utf-8") as fw:
                            json.dump(saved_doc, fw, indent=2, ensure_ascii=False)
                        all_demo_results[fname] = saved_doc
                        continue
            except Exception as e:
                print(f"    Cache re-ranking error: {e}")

        if not pdf_path.exists():
            raise FileNotFoundError(f"Missing demo PDF: {pdf_path}")

        pdf_bytes = pdf_path.read_bytes()
        raw_text, parse_method = parse_pdf(pdf_bytes)
        doc_lang = detect_document_language(raw_text)
        print(f"    Detected Document Language: '{doc_lang}' (Parse Method: {parse_method})")

        clauses = segment_text_into_clauses(raw_text, detected_language=doc_lang)
        print(f"    Segmented {len(clauses)} clauses")

        # Non-English documents: machine translate each clause to English for analysis
        if doc_lang != "en":
            print(f"    Machine-translating {len(clauses)} {doc_lang.upper()} clauses to English...")
            src_code = "tam_Taml" if doc_lang == "ta" else "hin_Deva"
            for c in clauses:
                c.english_translation = translate_indic_to_en(c.text, src_lang=src_code)
                c.detected_language = doc_lang

        flagged_clauses = []
        for idx, clause in enumerate(clauses, start=1):
            analysis_text = clause.english_translation if (doc_lang != "en" and clause.english_translation) else clause.text
            print(f"    Evaluating Clause {idx}/{len(clauses)}: {clause.clause_id} ...")

            clause_for_classifier = ClauseItem(
                clause_id=clause.clause_id,
                text=analysis_text,
                english_translation=clause.english_translation,
                detected_language=doc_lang,
            )

            grounding = store.query_nearest_references(analysis_text, top_k=4)
            flagged = classify_and_explain_clause(clause_for_classifier, grounding)
            if flagged:
                flagged.original_text = clause.text  # Preserve original Indic / English text
                flagged.english_translation = clause.english_translation
                flagged.detected_language = doc_lang
                flagged_clauses.append(flagged)
                print(f"      -> FLAGGED: {flagged.clause_type} ({flagged.title}) [Severity: {flagged.severity}]")
            else:
                print(f"      -> STANDARD: Not flagged")
            time.sleep(1.0)  # Gentle pacing against rate limits

        # Client Intake: Salaried, Dependents=Yes (count=2), Medium Income
        intake = ClientIntakeContext(
            employment_type="salaried",
            has_dependents=True,
            dependents_count=2,
            income_bracket="medium",
            document_type=doc_type,
        )

        ranked_clauses = rank_flagged_clauses(flagged_clauses, intake)

        print(f"    Generating document executive summary...")
        summary_input = "\n\n".join(
            (c.english_translation if (doc_lang != "en" and c.english_translation) else c.text)
            for c in clauses
        )
        summary_en, summary_hi, summary_ta = generate_document_summary(
            summary_input, len(clauses), len(ranked_clauses)
        )

        doc_result = {
            "generation_date": generation_date,
            "filename": fname,
            "document_type": doc_type,
            "document_language": doc_lang,
            "title": title,
            "pair_role": pair_role,
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

    # Build Cross-Language Consistency Matrix
    consistency_rows = []

    # 1. Rental: demo_rental_en.pdf vs demo_rental_hi.pdf
    rental_en = all_demo_results.get("demo_rental_en.pdf")
    rental_hi = all_demo_results.get("demo_rental_hi.pdf")
    if rental_en and rental_hi:
        en_types = set(c["clause_type"] for c in rental_en["flagged_clauses"])
        hi_types = set(c["clause_type"] for c in rental_hi["flagged_clauses"])
        all_rental_types = sorted(list(en_types | hi_types))
        for ct in all_rental_types:
            in_en = ct in en_types
            in_hi = ct in hi_types
            status = "MATCHED" if (in_en and in_hi) else ("MISSED in Hindi" if in_en else "EXTRA in Hindi")
            consistency_rows.append({
                "pair": "Rental (EN vs HI)",
                "clause_type": ct,
                "in_en": "Yes" if in_en else "No",
                "in_indic": "Yes" if in_hi else "No",
                "status": status
            })

    # 2. Employment: demo_employment_en.pdf vs demo_employment_ta.pdf
    emp_en = all_demo_results.get("demo_employment_en.pdf")
    emp_ta = all_demo_results.get("demo_employment_ta.pdf")
    if emp_en and emp_ta:
        en_types = set(c["clause_type"] for c in emp_en["flagged_clauses"])
        ta_types = set(c["clause_type"] for c in emp_ta["flagged_clauses"])
        all_emp_types = sorted(list(en_types | ta_types))
        for ct in all_emp_types:
            in_en = ct in en_types
            in_ta = ct in ta_types
            status = "MATCHED" if (in_en and in_ta) else ("MISSED in Tamil" if in_en else "EXTRA in Tamil")
            consistency_rows.append({
                "pair": "Employment (EN vs TA)",
                "clause_type": ct,
                "in_en": "Yes" if in_en else "No",
                "in_indic": "Yes" if in_ta else "No",
                "status": status
            })

    # Save aggregated summary JSON
    summary_json_path = output_dir / "demo_results_summary.json"
    with open(summary_json_path, "w", encoding="utf-8") as f:
        json.dump(
            {
                "generation_date": generation_date,
                "documents": all_demo_results,
                "cross_language_consistency": consistency_rows,
            },
            f,
            indent=2,
            ensure_ascii=False,
        )
    print(f"\nSaved aggregated demo summary to: {summary_json_path}")

    # Build Markdown Report
    md_lines = [
        f"# Legal Document Chatbot — Multilingual Demonstration & Audit Report",
        f"**Generated:** {generation_date}",
        f"**Configuration:** `ALLOW_HEURISTIC_FALLBACK=false` | Client Intake: `salaried`, `has_dependents=True (count=2)`, `income_bracket=medium`\n",
        f"## 1. Document Execution Summary Matrix",
        f"| Document | Language | Title | Total Clauses | Flagged Clauses | Parse Method |",
        f"| :--- | :---: | :--- | :---: | :---: | :---: |",
    ]

    for fname, d in all_demo_results.items():
        lang_str = d["document_language"].upper()
        md_lines.append(
            f"| `{fname}` | **{lang_str}** | {d['title']} | {d['total_clauses']} | **{d['flagged_count']}** | {d['parse_method']} |"
        )

    md_lines.extend([
        "",
        "---",
        "",
        "## 2. Cross-Language Consistency Audit Matrix",
        "This table evaluates consistency in clause flagging when the exact same underlying contract is submitted in English versus Hindi or Tamil:",
        "",
        "| Document Pair | Clause Type | English Flagged? | Indic Flagged? | Consistency Status |",
        "| :--- | :--- | :---: | :---: | :---: |",
    ])

    for row in consistency_rows:
        status_badge = f"**{row['status']}**" if "MATCHED" in row['status'] else f"*{row['status']}*"
        md_lines.append(
            f"| {row['pair']} | `{row['clause_type']}` | {row['in_en']} | {row['in_indic']} | {status_badge} |"
        )

    md_lines.extend([
        "",
        "---",
        "",
        "## 3. Document-by-Document Detailed Findings",
        "",
    ])

    for fname, d in all_demo_results.items():
        doc_lang = d["document_language"]
        md_lines.extend([
            f"### {d['title']} (`{fname}`)",
            f"- **Document Language:** `{doc_lang.upper()}` | **Document Type:** `{d['document_type']}` | **Clauses Segmented:** {d['total_clauses']} | **Risk Items Flagged:** {d['flagged_count']}",
            "",
            f"#### Executive Summary",
            f"- **English:** {d['summary_en']}",
            f"- **Hindi (हिंदी):** {d['summary_hi']}",
            f"- **Tamil (தமிழ்):** {d['summary_ta']}",
            "",
        ])

        flagged_items = d["flagged_clauses"]
        if not flagged_items:
            md_lines.extend([
                "> [!NOTE]",
                "> **Balanced Contract Result:** Zero clauses flagged. The agreement contains standard, mutual, and non-exploitative covenants.",
                "",
                "---",
                "",
            ])
            continue

        md_lines.append(f"#### Ranked Flagged Clauses ({len(flagged_items)} items)")
        for idx, fc in enumerate(flagged_items, start=1):
            c_type = fc.get("clause_type", "Unknown")
            c_title = fc.get("title", c_type)
            cid = fc.get("clause_id", f"Clause {idx}")
            sev = fc.get("severity", "Medium")
            score = fc.get("priority_score", 0.0)

            orig_text = (fc.get("original_text") or "").strip()
            en_trans = (fc.get("english_translation") or "").strip()

            md_lines.extend([
                f"##### {idx}. [{cid}] {c_title} — Severity: `{sev}` (Priority Score: {score:.1f})",
                f"**Original Clause Text ({doc_lang.upper()}):**",
                f"> *\"{orig_text}\"*",
                "",
            ])

            if doc_lang != "en" and en_trans:
                md_lines.extend([
                    f"**English Translation (Machine-Translated for Analysis):**",
                    f"> *\"{en_trans}\"*",
                    "",
                ])

            md_lines.extend([
                f"**Plain-Language Explanation & Risk Reason:**",
                f"- **English Explanation:** {fc.get('explanation', '')}",
                f"- **English Risk Reason:** {fc.get('risk_reason', '')}",
                f"- **Hindi Explanation (हिंदी व्याख्या):** {fc.get('explanation_hi', '')}",
                f"- **Hindi Risk Reason (हिंदी जोखिम कारण):** {fc.get('risk_reason_hi', '')}",
                f"- **Tamil Explanation (தமிழ் விளக்கம்):** {fc.get('explanation_ta', '')}",
                f"- **Tamil Risk Reason (தமிழ் ஆபத்து காரணம்):** {fc.get('risk_reason_ta', '')}",
                "",
                f"**Legal Basis:**",
            ])

            citations = fc.get("statutory_citations", [])
            if not citations:
                lb_msg = fc.get("legal_basis_message") or NO_STATUTE_MESSAGE
                lb_msg_hi = fc.get("legal_basis_message_hi") or NO_STATUTE_MESSAGE_HI
                lb_msg_ta = fc.get("legal_basis_message_ta") or NO_STATUTE_MESSAGE_TA
                md_lines.extend([
                    f"- **Status:** {lb_msg}",
                    f"- *Hindi (हिंदी):* {lb_msg_hi}",
                    f"- *Tamil (தமிழ்):* {lb_msg_ta}",
                    "",
                ])
            else:
                for cit in citations:
                    pid = cit.get("provision_id", "")
                    act = cit.get("act", "")
                    sec = cit.get("section", "")
                    title_part = f" ({cit.get('title')})" if cit.get("title") else ""
                    reason_en = cit.get("reason", "")
                    reason_hi = cit.get("reason_hi") or reason_en
                    reason_ta = cit.get("reason_ta") or reason_en
                    stat_text = cit.get("statutory_text", "").strip()

                    md_lines.extend([
                        f"- **[{pid}] {act} — {sec}{title_part}**",
                        f"  - *Reason (EN):* {reason_en}",
                        f"- *Reason (HI):* {reason_hi}",
                        f"- *Reason (TA):* {reason_ta}",
                    ])
                    if stat_text:
                        short_stat = (stat_text[:350] + "...") if len(stat_text) > 350 else stat_text
                        md_lines.extend([
                            f"  - *Verbatim Statutory Text (English):*",
                            f"    > \"{short_stat}\"",
                        ])
                md_lines.append("")

            alts = fc.get("standard_alternatives", [])
            md_lines.append(f"**How this is typically written (Typical Balanced Phrasing):**")
            if alts:
                for a_idx, alt in enumerate(alts, start=1):
                    md_lines.append(f"{a_idx}. \"{alt}\"")
            else:
                md_lines.append("*(No standard reference phrasing available)*")
            md_lines.append("")

            md_lines.extend([
                f"**Mandatory Legal Disclaimer:**",
                f"- **EN:** {MANDATORY_DISCLAIMER}",
                f"- **HI:** {MANDATORY_DISCLAIMER_HI}",
                f"- **TA:** {MANDATORY_DISCLAIMER_TA}",
                "",
            ])

        md_lines.extend(["", "---", ""])

    md_lines.extend([
        "## 4. Limitations & Disclaimers",
        "- **Synthetic Test Documents:** The analyzed documents are synthetic demonstrative contracts crafted for automated testing and software demonstration; they do not represent real-world legal agreements or actual persons.",
        "- **Experimental Indic Input Layer:** Hindi and Tamil document analysis is experimental. Documents are machine-translated to English via local IndicTrans2 models prior to vector grounding and clause classification. Nuances, idioms, or errors in machine translation can affect classification.",
        "- **Translations Not Native-Reviewed:** Hindi and Tamil contract texts and output translations are generated by automated neural machine translation and enforced via dictionary glossary rules; they have not undergone individual manual certification by native legal counsel.",
        "- **Not Legal Advice:** The explanations, risk ratings, priority scores, and statutory references provided by this software are for educational and informational purposes only. This tool does not constitute legal advice and cannot substitute for qualified legal counsel enrolled with the Bar Council of India.",
        "",
    ])

    report_content = "\n".join(md_lines)
    report_path = output_dir / "demo_report.md"
    root_report_path = BASE_DIR / "demo_report.md"

    with open(report_path, "w", encoding="utf-8") as f:
        f.write(report_content)
    with open(root_report_path, "w", encoding="utf-8") as f:
        f.write(report_content)

    print(f"Saved demo report to: {report_path}")
    print(f"Saved demo report to: {root_report_path}")
    print(f"\n=======================================================")
    print(f"DEMO EXECUTION COMPLETE!")
    print(f"=======================================================\n")


if __name__ == "__main__":
    run_demo()
