# Legal Document Chatbot — 5-Minute Live Demo Script

This script provides an exact 6-step walkthrough for demonstrating the Legal Document Chatbot, featuring cross-language contract analysis (English, Hindi, and Tamil), client-intake situational ranking, anti-hallucination statutory grounding, and bilingual clause inspection.

---

## Pre-Demo Checklist

1. **Verify Demo Contracts** in `sample_pdfs/demo/`:
   - `demo_rental_en.pdf` (English Residential Lease — One-Sided)
   - `demo_rental_hi.pdf` (Hindi Residential Lease — One-Sided)
   - `demo_employment_en.pdf` (English Executive Employment Agreement — One-Sided)
   - `demo_employment_ta.pdf` (Tamil Employment Agreement — One-Sided)
   - `demo_loan_en.pdf` (English Commercial Loan Agreement — One-Sided)
   *(All files contain the mandatory footer: `"SYNTHETIC DEMO DOCUMENT - NOT A REAL CONTRACT"`)*
2. **Offline Fallback Ready**: If internet or Gemini API quota is unavailable during presentation, present from the committed dated audit reports in `demo_report.md` and `demo_output/`.
3. **Environment**: Enforce `ALLOW_HEURISTIC_FALLBACK=false` to prove that all evaluations run through the genuine LLM pipeline and local neural translation models.

---

## 6-Step Live Demo Walkthrough (5 Minutes)

### Step 1: Upload English High-Risk Contract (45 seconds)
* **What to click**:
  - Click **Upload PDF** and select `sample_pdfs/demo/demo_rental_en.pdf`.
* **What to point out**:
  - Point out the page footer: `"SYNTHETIC DEMO DOCUMENT - NOT A REAL CONTRACT"`.
  - Highlight the structural parser: `pdfplumber` extracts text while preserving legal structure; regex boundary segmentation splits clauses by numbering rather than arbitrary token chunks.
* **Talking point**:
  > *"Most consumers sign standard form contracts without reading the fine print. Our tool automatically segments the document into discrete legal clauses and compares each section against a verified vector store of standard and one-sided clauses."*

---

### Step 2: Set Client Intake Context (45 seconds)
* **What to enter/select**:
  - **Employment Type**: `Salaried`
  - **Has Dependents**: `Yes` (Number of dependents: `2`)
  - **Income Bracket**: `Medium`
  - **Document Type**: `Rental Agreement`
* **What to point out**:
  - Show the intake profile panel.
  - Explain why legal risk is situational: losing a 10-month rental deposit is inconvenient for a corporation, but financially catastrophic for a salaried tenant with 2 dependents.
* **Talking point**:
  > *"Our situational ranker weights severity based on client vulnerability. Notice how deposit forfeiture and immediate 24-hour eviction jump to the top of the risk ranking because of the dependent profile."*

---

### Step 3: Inspect Ranked Flagged Clauses (60 seconds)
* **What to point out**:
  - **Clause 2 (Security Deposit Absolute Forfeiture — Ranked #1)**:
    - High priority score (115.0) driven by dependent context boost (+45.0).
    - Clear explanation and risk warning.
    - Statutory citation: Cites **ICA-1872-s74** (compensation for breach of contract / liquidated damages vs. penalty) with verbatim statutory text from the official Gazette.
  - **Clause 3 (Unilateral 24-Hour Eviction — Ranked #2)**:
    - Deprivation of property rights without judicial due process (cites **COI-art300A**).
  - **Clause 4 (Singapore Arbitration Seat & Forum Selection — Ranked #3)**:
    - Procedural unreasonableness for a residential tenant in Bengaluru.
  - **Balanced Alternatives**: Expand *"How this is typically written"* to show copy-pasteable fair compromise clauses for negotiations.

---

### Step 4: Upload Hindi Contract & Cross-Language Consistency (60 seconds)
* **What to click**:
  - Click **Start New Document** (or reset).
  - Upload `sample_pdfs/demo/demo_rental_hi.pdf`.
* **What to point out**:
  - **Automatic Language Detection**: System detects Devanagari script share $\rightarrow$ sets document language to `HI`.
  - **Default Output Language**: The UI automatically sets the output language toggle to **हिंदी (Hindi)**.
  - **Visible Experimental Notice**:
    > *"Experimental: this document was machine-translated to English before analysis. Errors in translation can affect results."*
  - **Bilingual Clause Display**: Show the card displaying the original Devanagari text (`खंड 2. प्रतिभूति जमा और पूर्ण जब्ती`) alongside the English machine-translation analyzed by the AI.
  - **Consistency**: Show that the exact same 4 clauses are flagged in Hindi as in the English contract (`demo_rental_en.pdf`).
* **Talking point**:
  > *"Citizens who receive agreements in regional languages are often at an information disadvantage. Here, our Indic input layer translates Devanagari clauses into English on CPU without external API calls, classifies them consistently, and renders the explanation back in Hindi."*

---

### Step 5: Upload Tamil Employment Contract (45 seconds)
* **What to click**:
  - Upload `sample_pdfs/demo/demo_employment_ta.pdf`.
* **What to point out**:
  - **Language Detection**: Automatically identifies Tamil script $\rightarrow$ sets document language to `TA`.
  - **Default Tamil UI**: Interface flips to **தமிழ்**.
  - **Bilingual Inspection**:
    - `பிரிவு 2. போட்டித் தடை` (3-year perpetual non-compete) $\rightarrow$ Cites **ICA-1872-s27** (agreements in restraint of trade void).
    - `பிரிவு 3. வரம்பற்ற இழப்பீட்டுப் பொறுப்பு` (Unlimited indemnity).
    - `பிரிவு 4. கட்டாயப் பணிப் பத்திரம்` (Service bond with INR 10L penalty) $\rightarrow$ Cites **ICA-1872-s74**.
    - `பிரிவு 5. சமச்சீரற்ற அறிவிப்புக் காலம்` (6 months vs 0 days notice period disparity).
* **Talking point**:
  > *"Notice how the Tamil legal terms—like 'வணிகத் தடை' for restraint of trade and 'இழப்பீட்டுப் பொறுப்பு' for indemnity—strictly conform to reviewed legal glossaries, ensuring terminological consistency."*

---

### Step 6: Loan Agreement & Strict Anti-Hallucination Discipline (45 seconds)
* **What to click**:
  - Upload `sample_pdfs/demo/demo_loan_en.pdf` with intake (`salaried`, `dependents=yes`).
* **What to point out**:
  - **Clause 1 (Penal Interest at 36% p.a.)**: Cites **ICA-1872-s74** and **CPA-2019-s2-46** (unfair contract).
  - **Clause 2 (Acceleration Without Notice)**: Cites **CPA-2019-s2-46**.
  - **Clause 6 (Unlimited Continuing Personal Guarantee)**: Elevated in rank due to dependents.
  - **Clause 5 (Unilateral Discretionary Rate Change)**:
    - Look at the Legal Basis box: Strictly displays `"No statutory provision retrieved"`.
    - Point out that because no provision in our verified Gazette corpus covers floating rate discretion, the system admits this rather than inventing non-existent RBI circulars or hallucinating fake sections.
* **Talking point**:
  > *"Unlike generic LLMs that invent convincing-sounding citations, our architecture uses strict closed-world statutory grounding. If a statute isn't verified in our official gazetted database, the system cleanly displays 'No statutory provision retrieved'."*

---

## What to Say If Asked About Limitations & Accuracy

| Topic | Defense / Clarification |
| :--- | :--- |
| **"Are the Hindi and Tamil texts legally certified?"** | *"No. The Hindi and Tamil contracts and output translations are machine-generated via local IndicTrans2 models and verified against dictionary glossary rules. They have not undergone individual manual certification by native legal counsel, which is explicitly noted in our limitations notice."* |
| **"How do you ensure zero hallucination in statute citations?"** | *"Every citation must pass a byte-level provenance audit against official Gazette PDFs published by the Legislative Department of India. If an LLM attempts to reference unretrieved section IDs, the citation validator drops it instantly."* |
| **"Is this providing legal advice?"** | *"No. LexGuard is an educational contract comprehension tool. Every screen and export includes a prominent statutory disclaimer stating that this does not constitute legal advice and recommending consultation with an advocate enrolled with the Bar Council of India."* |
| **"What happens when cloud LLM quota runs out?"** | *"The local parser, segmenter, ChromaDB vector store, IndicTrans2 translation models, and all pre-computed audit reports in `demo_output/` run 100% locally on-device without cloud API dependencies."* |
