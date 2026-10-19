import sys
import time
import difflib
import pytest
from pathlib import Path

if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

from app.segmenter import detect_document_language, segment_text_into_clauses
from app.translator import (
    translate_text_to_hindi,
    translate_text_to_tamil,
    translate_indic_to_en,
    get_indic_to_en_engine
)


def safe_print(msg: str):
    try:
        print(msg)
    except UnicodeEncodeError:
        print(msg.encode("ascii", errors="backslashreplace").decode("ascii"))


def test_language_detection():
    """Verify script-share language detection for English, Hindi, and Tamil."""
    en_sample = (
        "This Agreement is entered into by and between the Landlord and Tenant. "
        "The Tenant agrees to pay the monthly rent on the first day of each calendar month."
    )
    assert detect_document_language(en_sample) == "en"

    hi_sample = (
        "यह पट्टा समझौता मकान मालिक और किरायेदार के बीच निष्पादित किया गया है। "
        "किरायेदार प्रत्येक कैलेंडर माह के पहले दिन मासिक किराया देने के लिए सहमत है।"
    )
    assert detect_document_language(hi_sample) == "hi"

    ta_sample = (
        "இந்த வாடகை ஒப்பந்தம் நில உரிமையாளர் மற்றும் குத்தகைதாரருக்கு இடையே செய்யப்படுகிறது. "
        "குத்தகைதாரர் ஒவ்வொரு மாதமும் முதல் நாளில் வாடகையை செலுத்த ஒப்புக்கொள்கிறார்."
    )
    assert detect_document_language(ta_sample) == "ta"

    # English with an isolated Hindi/Tamil proper noun
    mixed_en = "Mr. Rajesh Sharma (राजेश शर्मा) residing at Bengaluru hereby enters this Lease Agreement."
    assert detect_document_language(mixed_en) == "en"

    # Empty / whitespace fallback
    assert detect_document_language("") == "en"
    assert detect_document_language("   ") == "en"


def test_segmentation_hindi_sample():
    """Verify segmenter recognizes Hindi clause headers (खंड, धारा, अनुच्छेद, 3.)."""
    hindi_doc = """
खंड 1. पट्टा अवधि
यह पट्टा समझौता 11 महीने की अवधि के लिए प्रभावी होगा।

खंड 2. प्रतिभूति जमा
किरायेदार 100,000 रुपये की ब्याज मुक्त सुरक्षा जमा राशि का भुगतान करेगा।

धारा 3. एकपक्षीय बेदखली
मकान मालिक किसी भी समय 24 घंटे के नोटिस पर परिसर को खाली करा सकता है।

4. विवाद समाधान
सभी विवादों का निपटारा मध्यस्थता द्वारा किया जाएगा।
""".strip()

    clauses = segment_text_into_clauses(hindi_doc)
    assert len(clauses) == 4
    assert clauses[0].clause_id == "खंड 1."
    assert "11 महीने" in clauses[0].text
    assert clauses[1].clause_id == "खंड 2."
    assert "100,000 रुपये" in clauses[1].text
    assert clauses[2].clause_id == "धारा 3."
    assert "24 घंटे" in clauses[2].text
    assert clauses[3].clause_id == "4."
    assert "मध्यस्थता" in clauses[3].text
    assert clauses[0].detected_language == "hi"


def test_segmentation_tamil_sample():
    """Verify segmenter recognizes Tamil clause headers (பிரிவு, சரத்து, உறுப்பு, 3.)."""
    tamil_doc = """
பிரிவு 1. குத்தகை காலம்
இந்த குத்தகை ஒப்பந்தம் 11 மாத காலத்திற்கு செல்லுபடியாகும்.

பிரிவு 2. பிணைய வைப்பு
குத்தகைதாரர் 100,000 ரூபாய் வட்டியற்ற பாதுகாப்பு வைப்புத்தொகையை செலுத்த வேண்டும்.

சரத்து 3. ஒருதலைப்பட்ச வெளியேற்றம்
நில உரிமையாளர் 24 மணி நேர அறிவிப்பில் வளாகத்தை காலி செய்ய கோரலாம்.

4. சர்ச்சை தீர்வு
அனைத்து தகராறுகளும் இசைவுத்தீர்ப்பு மூலம் தீர்க்கப்படும்.
""".strip()

    clauses = segment_text_into_clauses(tamil_doc)
    assert len(clauses) == 4
    assert clauses[0].clause_id == "பிரிவு 1."
    assert "11 மாத" in clauses[0].text
    assert clauses[1].clause_id == "பிரிவு 2."
    assert "100,000 ரூபாய்" in clauses[1].text
    assert clauses[2].clause_id == "சரத்து 3."
    assert "24 மணி நேர" in clauses[2].text
    assert clauses[3].clause_id == "4."
    assert "இசைவுத்தீர்ப்பு" in clauses[3].text
    assert clauses[0].detected_language == "ta"


def test_segmentation_english_regression():
    """Verify that English document segmentation behavior is completely preserved without regression."""
    english_doc = """
WHEREAS the Employer wishes to engage the Employee;
IN WITNESS WHEREOF the parties execute this Agreement.

Clause 1. Employment and Duties
The Employee shall devote whole time and attention to Company business.

Clause 2. Security Deposit and Absolute Forfeiture
The Tenant shall deposit ten months rent which shall be forfeited on any default.

SECTION 3. Governing Law and Arbitration
Any dispute shall be referred to arbitration in accordance with the Arbitration and Conciliation Act, 1996.

4. Confidentiality Obligations
All proprietary information shall remain strictly confidential.
""".strip()

    clauses = segment_text_into_clauses(english_doc)
    assert len(clauses) >= 4
    clause_ids = [c.clause_id for c in clauses]
    assert any("Clause 1" in cid for cid in clause_ids)
    assert any("Clause 2" in cid for cid in clause_ids)
    assert any("SECTION 3" in cid or "3" in cid for cid in clause_ids)
    assert any("4." in cid or "Clause 4" in cid for cid in clause_ids)
    assert all(c.detected_language == "en" for c in clauses)


def test_round_trip_sanity_and_latency():
    """
    Round-trip sanity:
    Translate 3 English clauses to hi/ta with existing model, then back with the new Indic-to-EN model on CPU.
    Measure and report latency per clause and sequence similarity.
    """
    engine = get_indic_to_en_engine()
    assert engine.device == "cpu"

    test_clauses = [
        "The Employee agrees to indemnify and hold harmless the Company against all liabilities and damages.",
        "The Employee shall not engage in any competing commercial activity for a period of twenty-four months.",
        "In the event of default, the entire security deposit shall be immediately forfeited to the Landlord as liquidated damages."
    ]

    hi_latencies = []
    ta_latencies = []
    hi_similarities = []
    ta_similarities = []

    safe_print("\n" + "=" * 60)
    safe_print(f"ROUND-TRIP TEST: Model={engine.model_name} | Device={engine.device}")
    safe_print("=" * 60)

    for i, orig in enumerate(test_clauses, 1):
        # 1. Hindi Round-Trip
        hi_trans = translate_text_to_hindi(orig)
        t0 = time.time()
        en_from_hi = translate_indic_to_en(hi_trans, src_lang="hi")
        dt_hi = time.time() - t0
        hi_latencies.append(dt_hi)
        sim_hi = difflib.SequenceMatcher(None, orig.lower(), en_from_hi.lower()).ratio()
        hi_similarities.append(sim_hi)

        # 2. Tamil Round-Trip
        ta_trans = translate_text_to_tamil(orig)
        t0 = time.time()
        en_from_ta = translate_indic_to_en(ta_trans, src_lang="ta")
        dt_ta = time.time() - t0
        ta_latencies.append(dt_ta)
        sim_ta = difflib.SequenceMatcher(None, orig.lower(), en_from_ta.lower()).ratio()
        ta_similarities.append(sim_ta)

        safe_print(f"\n[Clause {i}]")
        safe_print(f"  ORIGINAL (EN):     {orig}")
        safe_print(f"  HINDI:             {hi_trans}")
        safe_print(f"  HI -> EN ROUNDTRIP:{en_from_hi} (sim={sim_hi:.2f}, latency={dt_hi:.2f}s)")
        safe_print(f"  TAMIL:             {ta_trans}")
        safe_print(f"  TA -> EN ROUNDTRIP:{en_from_ta} (sim={sim_ta:.2f}, latency={dt_ta:.2f}s)")

        # Verify sanity threshold (round-trip captures core legal semantics)
        assert len(en_from_hi) > 20
        assert len(en_from_ta) > 20
        assert sim_hi >= 0.40  # Meaningful lexical overlap after neural round-trip
        assert sim_ta >= 0.40

    avg_hi_lat = sum(hi_latencies) / len(hi_latencies)
    avg_ta_lat = sum(ta_latencies) / len(ta_latencies)
    avg_hi_sim = sum(hi_similarities) / len(hi_similarities)
    avg_ta_sim = sum(ta_similarities) / len(ta_similarities)

    safe_print("\n" + "-" * 60)
    safe_print(f"SUMMARY METRICS:")
    safe_print(f"  Average Hindi -> English Latency: {avg_hi_lat:.2f}s / clause (Similarity: {avg_hi_sim:.2f})")
    safe_print(f"  Average Tamil -> English Latency: {avg_ta_lat:.2f}s / clause (Similarity: {avg_ta_sim:.2f})")
    safe_print("-" * 60)
