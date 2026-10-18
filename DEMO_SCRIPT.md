# Legal Document Chatbot — 5-Minute Live Demo Script

This script guides presenters through a 5-minute live demonstration of the Legal Document Chatbot. It highlights client-intake situational ranking, anti-hallucination statutory grounding, multilingual explanation (Hindi & Tamil), and false-positive resilience.

---

## Pre-Demo Checklist & Setup

1. **Verify Demo Files**: Confirm the 5 synthetic test contracts are available in `sample_pdfs/demo/`:
   - `demo_rental_one_sided.pdf`
   - `demo_employment_one_sided.pdf`
   - `demo_loan_one_sided.pdf`
   - `demo_rental_fair.pdf`
   - `demo_employment_fair.pdf`
2. **Offline Fallback**: Pre-generated demo reports and JSONs are preserved in `demo_output/` and `demo_report.md`. If internet connectivity or LLM quota is unavailable during the presentation, you can present directly from `demo_report.md`.
3. **Environment**: Enforce `ALLOW_HEURISTIC_FALLBACK=false` to prove that all evaluations run through the verified Gemini 2.5 Pro / Flash pipeline and local IndicTrans2 translation models.

---

## 6-Step Live Demo Walkthrough (5 Minutes)

### Step 1: Upload a High-Risk Contract (45 seconds)
* **What to click**:
  - Click **Upload Document** and select `sample_pdfs/demo/demo_rental_one_sided.pdf`.
* **What to point out**:
  - Point out the footer on each page: `"SYNTHETIC DEMO DOCUMENT - NOT A REAL CONTRACT"`.
  - Highlight the structural parser: the system does not break documents into arbitrary token windows; it parses legal clauses hierarchically using regex and heading detection.
  - Notice the fast segmentation: 5 distinct clauses identified immediately.
* **Talking point**:
  > *"Most users sign rental agreements without reading the fine print. Our chatbot automatically parses the document clause-by-clause, comparing each section against a verified vector store of standard and one-sided clauses."*

---

### Step 2: Set Client Intake Context (45 seconds)
* **What to enter/select**:
  - **Employment Type**: `Salaried`
  - **Has Dependents**: `Yes` (Number of dependents: `2`)
  - **Income Bracket**: `Medium`
* **What to point out**:
  - Show the client intake context panel.
  - Explain that legal risk is not one-size-fits-all. A forfeit of 6 months' deposit is an inconvenience for a corporation, but an existential financial crisis for a salaried tenant supporting two dependents.
* **Talking point**:
  > *"Our situational ranker uses the client's financial profile to weight severity. A clause threatening instant forfeiture or immediate eviction is elevated to top priority when the user has dependents who rely on residential stability."*

---

### Step 3: Inspect Ranked Flagged Clauses (60 seconds)
* **What to click/expand**:
  - Review the ranked flagged clauses list.
  - Expand **Clause 2: Security Deposit Non-Refundability & Forfeiture** (Ranked #1).
  - Expand **Clause 3: Unilateral Eviction Without Notice** (Ranked #2).
  - Expand **Clause 4: Dispute Resolution & Singapore Arbitration** (Ranked #3).
* **What to point out**:
  - **Severity & Boost**: Note how Clause 2 received a high situational boost due to dependent vulnerability and deposit loss risk.
  - **Plain-Language Explanation**: Explains what the clause actually means in simple terms.
  - **Why It's Risky**: Explains the exact danger (e.g., forfeiting 6 months' deposit upon mere 2-day rent delay without judicial recourse).
  - **Alternative Standard Phrasing**: Provides realistic, balanced clauses the user can copy-paste to negotiate with the landlord.
* **Talking point**:
  > *"The chatbot doesn't just warn you; it equips you with balanced compromise language that landlords commonly accept, empowering the tenant during lease negotiations."*

---

### Step 4: Multilingual Toggle — Hindi & Tamil (60 seconds)
* **What to click**:
  - Switch the language toggle to **हिंदी (Hindi)**.
  - Then switch the language toggle to **தமிழ் (Tamil)**.
* **What to point out**:
  - **Localized Explanations & Risks**: The explanations, risk descriptions, and alternatives flip seamlessly into natural, fluent Hindi and Tamil via local IndicTrans2 models.
  - **Glossary Enforcement**: Critical legal terminology (such as *security deposit* $\rightarrow$ `जमानत राशि` / `பிணைய வைப்புத் தொகை`, and *dispute resolution* $\rightarrow$ `विवाद समाधान` / `சர்ச்சை தீர்வு`) strictly complies with pre-reviewed glossaries.
  - **Verbatim English Statute Integrity**: The statutory text citation remains strictly in official English text to preserve legal certainty, while the explanatory statutory reasoning is translated.
  - **Prominent Disclaimers**: Disclaimers are displayed prominently in all three languages.
* **Talking point**:
  > *"Over 80% of Indian citizens do not read English fluently. By delivering accurate regional translations powered by self-hosted AI models, we make justice and contract comprehension accessible across linguistic boundaries."*

---

### Step 5: False-Positive Resilience Check (45 seconds)
* **What to click**:
  - Click **Upload Document** and select `sample_pdfs/demo/demo_rental_fair.pdf` (or `demo_employment_fair.pdf`).
* **What to point out**:
  - Look at the summary result: **0 flagged clauses** (or near-zero).
  - Show the clauses: Standard 2-month deposit, mutual 30-day notice, standard jurisdictional forum.
* **Talking point**:
  > *"A common failure of automated legal tools is alarmism — flagging every standard termination or indemnity clause as a threat. Here you see our classifier correctly recognizes a fair, balanced contract, returning zero false alarms."*

---

### Step 6: Loan Agreement — Statutory Grounding & Anti-Hallucination (45 seconds)
* **What to click**:
  - Upload `sample_pdfs/demo/demo_loan_one_sided.pdf`.
  - Review the flagged results:
    1. **Clause 1 (Penal Interest at 36% p.a.)**: Cites **ICA-1872-s74** (compensation for breach of contract / liquidated damages vs. penalty) and **CPA-2019-s2-46** (unfair contract terms).
    2. **Clause 2 (Acceleration on Technical Default)**: Cites **CPA-2019-s2-46**.
    3. **Clause 5 (Continuing Unlimited Personal Guarantee)**: Ranked prominently due to dependents context.
* **What to point out**:
  - Notice the **Statute Citation Box**: Displays the exact section title and verbatim gazetted text.
  - Point out **Disciplined Citation**: For clauses where no verified statute in our gazetted corpus directly applies, the system strictly outputs `"No statutory provision retrieved"` rather than hallucinating fake sections or non-existent judicial precedents.
* **Talking point**:
  > *"Every statute citation is checked against our verified, byte-level provenance store of official Legislative Department PDFs. If an LLM attempts to invent an unverified section number, our citation validator drops it instantly."*

---

## Q&A Handling: Accuracy, Liability, and Architecture

| Expected Question | Authoritative Answer |
| :--- | :--- |
| **"How do you prevent the AI from hallucinating fake laws?"** | *"We use a zero-tolerance dual validator: First, statutory retrieval is restricted to our provenanced corpus of official Gazette PDFs. Second, our post-generation validator verifies every citation ID, provision title, and verbatim excerpt against local JSON records. Any ungrounded citation is dropped and logged as a hallucination attempt."* |
| **"Can this be considered unauthorized practice of law?"** | *"No. The system is an educational contract analysis assistant. Every screen, printout, and export includes a mandatory statutory disclaimer in English, Hindi, and Tamil explicitly stating that the output does not constitute legal advice and recommends consulting an advocate enrolled with the Bar Council of India."* |
| **"How are Hindi and Tamil translations verified?"** | *"Translations run through IndicTrans2 with an automated glossary enforcement engine that checks lemmas and prevents term corruption. Translations are periodically audited against our `GLOSSARY_REVIEW.md` checklist."* |
| **"Why not just use ChatGPT or Claude directly?"** | *"General-purpose LLMs hallucinate Indian statutory sections (e.g. citing non-existent sub-sections or repealed acts), fail to apply situational financial risk ranking, lack verified Gazette grounding, and cannot guarantee deterministic provenance. Our architecture wraps curated legal grounding around the LLM."* |
| **"What if the user is completely offline?"** | *"The PDF parser, regex clause segmenter, ChromaDB vector store, IndicTrans2 translation models, and pre-computed demo reports run 100% locally on-device without external cloud dependencies."* |
