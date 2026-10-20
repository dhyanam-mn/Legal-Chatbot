# Legal Document Chatbot — 10-12 Minute Live Demo Script

This script provides an exact 6-step walkthrough for presenting the Legal Document Chatbot. Every factual claim, clause number, rank, score, flagged count, and citation status in this script is copied directly from `demo_report.md` and `demo_output/`.

---

## Pre-Demo Checklist (Mandatory)

Complete these steps on the demo machine before presenting:
1. **Pre-download both IndicTrans2 models**: Ensure both official AI4Bharat models (`ai4bharat/indictrans2-en-indic-dist-200M` and `ai4bharat/indictrans2-indic-en-dist-200M`) are cached locally in Hugging Face cache so no model weights are downloaded live.
2. **Warm the backend**: Start FastAPI and upload at least one document (`demo_rental_en.pdf` or `demo_rental_hi.pdf`) so ChromaDB embeddings, vector stores, and IndicTrans2 models are resident in memory.
3. **Confirm Gemini API quota/billing**: Check Google AI Studio to confirm that `GEMINI_MODELS[0]` (`gemini-3.8-flash`) has active quota and is not returning `429 RESOURCE_EXHAUSTED`.
4. **Full Dry Run**: Execute a complete dry run of all 6 steps on the demo laptop under the same network conditions.
5. **Offline Fallback Ready**: If the network drops or Gemini API quota is exhausted, switch immediately to presenting the pre-computed dated audit report in `demo_report.md` and JSON files in `demo_output/`.

---

## Latency & Timing Estimates

- **IndicTrans2 Model Initialization (Indic $\rightarrow$ English)**: ~10–12s (one-time on first non-English document upload).
- **Indic $\rightarrow$ English Clause Translation**: ~3.56s per clause on CPU (Hindi), ~3.16s per clause on CPU (Tamil).
- **English $\rightarrow$ Hindi/Tamil Output Translation**: ~2–4s per clause on CPU.
- **Gemini Classification**: ~1.5–3s per clause.
- **Estimated Step Durations (10–12 Minute Slot)**:
  - Step 1: ~1m45s (Upload English Lease, parsing, and classification)
  - Step 2: ~1m15s (Intake profile selection and situational re-ranking)
  - Step 3: ~2m00s (Inspection of ranked English clauses, legal basis, and typical phrasing)
  - Step 4: ~2m30s (Upload Hindi Lease, Indic-to-EN translation, and bilingual view)
  - Step 5: ~2m15s (Upload Tamil Employment Contract, translation, and glossary check)
  - Step 6: ~1m45s (Upload Loan Agreement, unmapped statute discipline)

---

## 6-Step Live Demo Walkthrough (10–12 Minutes)

### Step 1: Upload English High-Risk Contract (~1m45s)
* **What to click**:
  - Click **Upload PDF** and select `sample_pdfs/demo/demo_rental_en.pdf`.
* **What to point out**:
  - Point out the page footer on every page: `"SYNTHETIC DEMO DOCUMENT - NOT A REAL CONTRACT"`.
  - Point out text extraction via `pdfplumber` and clause segmentation: The document is segmented into **6 clauses** using line-start numbered regex rather than arbitrary token windows.
  - Initial classification flags **3 out of 6 clauses** as one-sided against our reference set of standard vs one-sided example clauses (synthetic).
* **Talking point**:
  > *"We start with a synthetic 6-clause residential lease. The system segments the text by numbered clause boundaries and flags 3 high-risk clauses by comparing them against our reference set of standard vs one-sided example clauses (synthetic)."*

---

### Step 2: Set Client Intake Context (~1m15s)
* **What to enter/select**:
  - **Employment Type**: `Salaried`
  - **Has Dependents**: `Yes` (Count: `2`)
  - **Income Bracket**: `Medium`
  - **Document Type**: `Rental Agreement`
* **What to point out**:
  - Explain why intake context matters: forfeiting a 10-month rental deposit threatens immediate housing and living stability for a salaried tenant with 2 dependents.
  - Notice the priority scores:
    - **Clause 2 (Security Deposit)** received a dependent boost of +45.0, resulting in a top priority score of **115.0** (Severity: `High`).
    - **Clause 3 (Unilateral Eviction)** follows with a priority score of **110.0** (Severity: `High`).
    - **Clause 4 (Dispute Resolution)** ranks third with a score of **50.0** (Severity: `Medium`).
* **Talking point**:
  > *"Our ranker personalizes clause severity. Notice how Clause 2 (deposit forfeiture) and Clause 3 (24-hour eviction) are weighted to the top with priority scores of 115.0 and 110.0 because of the client's dependents profile."*

---

### Step 3: Inspect Ranked Flagged Clauses (~2m00s)
* **What to review**:
  - **Rank 1 — Clause 2: Penalty & Liquidated Damages** (Score: 115.0 | High):
    - *Original Text*: 10-month deposit (INR 350,000) irrevocably forfeited upon 48-hour rent delay without requirement to prove actual loss.
    - *Explanation & Risk*: Highlights punitive damages without proof of harm.
    - *Legal Basis*: Shows `"Legal basis unavailable right now"` if Gemini quota was reached, or cites **ICA-1872-s74** with verbatim statutory text audited against official Gazette PDFs with documented cleaning.
    - *Typical Phrasing*: Expand to show balanced alternatives (e.g. standard 5-day grace period, administrative fee of $50, capped damages).
      - *Note on Typical Phrasing*: Example phrasings come from a generic reference set and may use a different currency from the document.
  - **Rank 2 — Clause 3: Unilateral Termination** (Score: 110.0 | High):
    - Landlord right to terminate on 24 hours' notice without cause.
  - **Rank 3 — Clause 4: Arbitration & Dispute Resolution** (Score: 50.0 | Medium):
    - Sole arbitrator appointed exclusively by Landlord with seat in Singapore.
  - **Exact Disclaimer**: Point out the mandatory disclaimer displayed on the card:
    > *"This explains what the clause means. It is not legal advice. Consult a lawyer before acting on this."*

---

### Step 4: Upload Hindi Contract & Cross-Language Consistency (~2m30s)
* **What to click**:
  - Click **Start New Document** and upload `sample_pdfs/demo/demo_rental_hi.pdf`.
* **What to point out**:
  - **Language Detection**: The system calculates Unicode script character shares (`\u0900-\u097F`) and automatically detects document language as **`hi`** (Hindi).
  - **Default Output Language**: The output language toggle automatically switches to **हिंदी (Hindi)**.
  - **Prominent Experimental Notice**:
    > *"Experimental: this document was machine-translated to English before analysis. Errors in translation can affect results."*
  - **Bilingual Clause Card**:
    - Displays the original Hindi text: `खंड 2. प्रतिभूति जमा और पूर्ण जब्ती`.
    - Displays the English machine-translation generated locally on CPU: *"The Tenant shall deposit INR 350,000 (representing ten months' rent) as interest-free security deposit..."*
  - **Actual Consistency Numbers (one synthetic document pair; a demonstration, not an accuracy measure)**:
    - **Rental Consistency (English vs Hindi)**:
      - **3 Matched** (`penalty`, `termination`, `dispute_resolution`)
      - **0 Missed**
      - **0 Extra**
    - Both English and Hindi documents flagged exactly **3 out of 6 clauses** with identical ranking: Rank 1 (`खंड 2.`, score 115.0), Rank 2 (`खंड 3.`, score 110.0), Rank 3 (`खंड 4.`, score 50.0).
  - **Glossary Note**: Point out that legal terms use a defined glossary, pending native-speaker review.
* **Talking point**:
  > *"When we upload the identical rental lease written in Hindi, the local CPU model translates each clause to English for vector grounding and Gemini classification. As verified in our consistency table (one synthetic document pair; a demonstration, not an accuracy measure), 3 out of 3 flagged clause types matched with 0 missed and 0 extra."*

---

### Step 5: Upload Tamil Employment Contract (~2m15s)
* **What to click**:
  - Upload `sample_pdfs/demo/demo_employment_ta.pdf` with intake (`salaried`, `dependents=yes`).
* **What to point out**:
  - **Language Detection**: Detects Tamil Unicode script (`\u0B80-\u0BFF`) $\rightarrow$ sets language to **`ta`** (Tamil).
  - **Default Tamil UI**: UI defaults to **தமிழ்**.
  - **Flagged Count**: **4 out of 6 clauses** flagged.
  - **Actual Consistency Numbers (English vs Tamil) (one synthetic document pair; a demonstration, not an accuracy measure)**:
    - **4 Matched** (`service_bond`, `indemnity`, `non_compete`, `notice_period_garden_leave`)
    - **0 Missed**
    - **0 Extra**
  - **Ranked Clauses in Tamil**:
    - Rank 1: `பிரிவு 4.` (`service_bond`, Score: 130.0 | High)
    - Rank 2: `பிரிவு 3.` (`indemnity`, Score: 115.0 | High)
    - Rank 3: `பிரிவு 2.` (`non_compete`, Score: 100.0 | High)
    - Rank 4: `பிரிவு 5.` (`notice_period_garden_leave`, Score: 90.0 | High)
  - **Glossary Wording**: Notice Tamil terminology like `போட்டித் தடை` (non-compete) and `இழப்பீட்டுப் பொறுப்பு` (indemnity), drawn from a defined glossary, pending native-speaker review.

---

### Step 6: Loan Agreement & Unmapped Statutory Discipline (~1m45s)
* **What to click**:
  - Upload `sample_pdfs/demo/demo_loan_en.pdf` with intake (`salaried`, `dependents=yes`).
* **What to point out**:
  - **Flagged Count**: **5 out of 7 clauses** flagged.
  - **Exact Ranks and Scores from Report**:
    - Rank 1: `Clause 3.` (`acceleration`, Score: **125.0** | High)
    - Rank 2: `Clause 6.` (`guarantor_liability`, Score: **125.0** | High)
    - Rank 3: `Clause 2.` (`penal_interest`, Score: **115.0** | High)
    - Rank 4: `Clause 4.` (`foreclosure_charges`, Score: **110.0** | High)
    - Rank 5: `Clause 5.` (`unilateral_interest_change`, Score: **75.0** | High)
  - **Disciplined Statutory Citations**:
    - Look at the Legal Basis box for **Clause 3 (Acceleration)**: Displays `"No statutory provision retrieved"`.
    - Look at the Legal Basis box for **Clause 6 (Guarantor Liability)**: Displays `"No statutory provision retrieved"`.
    - Look at the Legal Basis box for **Clause 5 (Unilateral Interest Rate Change)**: Displays `"No statutory provision retrieved"`.
    - *(Similarly, set-off/lien and IP assignment show "No statutory provision retrieved" because they have no verified provisions mapped in our verified gazetted corpus).*
* **Talking point**:
  > *"Look at Clause 3 (Acceleration), Clause 6 (Guarantor Liability), and Clause 5 (Unilateral Interest Change). Instead of hallucinating non-existent RBI circulars or sections, the system displays 'No statutory provision retrieved'. Every statute citation in our database is audited against official Gazette PDFs with documented cleaning."*

---

## Known Issues I'll Mention Proactively

Be upfront during the presentation by proactively mentioning these known limitations documented in `demo_report.md`:
1. **Notice Period Ranking Inconsistency (EN vs TA)**: In `demo_employment_en.pdf`, `Clause 5.` (`notice_period_garden_leave`) ranked **#1 with a score of 135.0**, whereas in `demo_employment_ta.pdf` (`பிரிவு 5.`), it ranked **#4 with a score of 90.0**. The 45.0-point score difference is caused by the ranker applying a dependents boost (+45.0) via an English keyword substring match on `"forfeiture"` in the original text of the English contract (`"Clause 5. Asymmetric Notice Period and Forfeiture"`); in the Tamil contract, the original text is in Tamil (`"பிரிவு 5..."`) and the ranker checks `original_text` rather than `english_translation`, so the keyword check fails and the clause receives its standard salaried employment score of 90.0. Both versions correctly flagged the clause.
2. **Quota Exhaustion Showing "Legal basis unavailable right now"**: Under the Gemini API free-tier limit (20 requests/day per model), when `GEMINI_MODELS[0]` exhausts its quota, citation generation safely returns `"Legal basis unavailable right now"` rather than guessing with lightweight models.
3. **Parser Reporting `pdfplumber (partial)` on Indic PDFs**: `demo_rental_hi.pdf` and `demo_employment_ta.pdf` show parse method `pdfplumber (partial)` because font spacing ratios in complex Indic scripts triggered the parser's partial check, even though full text was extracted.
4. **Machine Translation Nuances**: IndicTrans2 translation from Tamil translated "liquidated damages" literally as "dissolved damages" (*கலைக்கப்பட்ட சேதங்கள்*), illustrating why machine translation without native-speaker legal review remains experimental. Next step: protect glossary terms before translation.

---

## Limitations & Architecture Defense

| Topic | Transparent Answer |
| :--- | :--- |
| **API vs Local Architecture** | *Classification, plain-language explanation, and statutory citations call the Google Gemini API (document clause text is transmitted to Google servers). Document text parsing (`pdfplumber`), semantic vector retrieval (`ChromaDB`), and IndicTrans2 neural translations run 100% locally on-device. Without API quota, the demo presents pre-computed outputs from `demo_output/`.* |
| **Native Speaker Review** | *The Hindi and Tamil demo contract texts and output translations are machine-generated under automated glossary rules from a defined glossary, pending native-speaker review. They have not been reviewed by a native speaker or certified by legal counsel.* |
| **Vector Grounding Source** | *Semantic retrieval matches clauses against a reference set of standard vs one-sided example clauses (synthetic), not a comprehensive commercial repository.* |
| **Statute Provenance** | *Statutory provisions are audited against official Gazette PDFs with documented cleaning (removing OCR footnote artifacts and watermarks). If no verified provision applies, the system strictly outputs "No statutory provision retrieved".* |
| **Legal Disclaimer** | *Exact text displayed across all screens and cards:*<br>• **EN**: *"This explains what the clause means. It is not legal advice. Consult a lawyer before acting on this."*<br>• **HI**: *"यह क्लॉज के अर्थ की व्याख्या करता है। यह कानूनी सलाह नहीं है। इस पर कार्रवाई करने से पहले वकील से परामर्श लें।"*<br>• **TA**: *"இது இந்தப் பிரிவின் பொருளை விளக்குகிறது. இது சட்ட ஆலோசனை அல்ல. இதன் அடிப்படையில் செயல்படுவதற்கு முன் ஒரு வழக்கறிஞரைக் கலந்தாலோசிக்கவும்."* |

---

## Limitations & Architecture Defense

| Topic | Transparent Answer |
| :--- | :--- |
| **API vs Local Architecture** | *Classification, plain-language explanation, and statutory citations call the Google Gemini API (document clause text is transmitted to Google servers). Document text parsing (`pdfplumber`), semantic vector retrieval (`ChromaDB`), and IndicTrans2 neural translations run 100% locally on-device. Without API quota, the demo presents pre-computed outputs from `demo_output/`.* |
| **Native Speaker Review** | *The Hindi and Tamil demo contract texts and output translations are machine-generated under automated glossary rules from a defined glossary, pending native-speaker review. They have not been reviewed by a native speaker or certified by legal counsel.* |
| **Vector Grounding Source** | *Semantic retrieval matches clauses against a reference set of standard vs one-sided example clauses (synthetic), not a comprehensive commercial repository.* |
| **Statute Provenance** | *Statutory provisions are audited against official Gazette PDFs with documented cleaning (removing OCR footnote artifacts and watermarks). If no verified provision applies, the system strictly outputs "No statutory provision retrieved".* |
| **Legal Disclaimer** | *Exact text displayed across all screens and cards:*<br>• **EN**: *"This explains what the clause means. It is not legal advice. Consult a lawyer before acting on this."*<br>• **HI**: *"यह क्लॉज के अर्थ की व्याख्या करता है। यह कानूनी सलाह नहीं है। इस पर कार्रवाई करने से पहले वकील से परामर्श लें।"*<br>• **TA**: *"இது இந்தப் பிரிவின் பொருளை விளக்குகிறது. இது சட்ட ஆலோசனை அல்ல. இதன் அடிப்படையில் செயல்படுவதற்கு முன் ஒரு வழக்கறிஞரைக் கலந்தாலோசிக்கவும்."* |
