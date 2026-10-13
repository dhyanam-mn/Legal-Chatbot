# Legal Document Chatbot

A multilingual AI-assisted legal document analysis system that inspects contracts, identifies one-sided or high-risk clauses, retrieves verified statutory provisions from Indian law, translates explanations and risk rationales into Hindi and Tamil using a local IndicTrans2 model, and provides grounded chat assistance.

---

## Architecture Overview

1. **Document Parsing & Clause Segmentation**:
   - PDF parsing via `pdfplumber` (with OCR fallback capability).
   - Strict structural clause boundary segmentation preserving sentence grammar (e.g. `WHEREAS` handling).
2. **Grounding & Retrieval-Augmented Generation (RAG)**:
   - Vector store powered by ChromaDB with `BAAI/bge-small-en-v1.5` embeddings.
   - Separate ChromaDB collection `legal_statutes` storing verified statutory provisions (1 provision = 1 chunk).
   - Deterministic clause-to-statute mapping to bias retrieval for high-risk clause types.
3. **Statutory Citations**:
   - Pinned strictly to the strongest configured Gemini model (`gemini-3.8-flash`).
   - Generates single-sentence descriptive reasons and attaches verbatim statutory provision text in English.
   - Falls back safely to `"Legal basis unavailable right now"` if the strongest model is unavailable (rotation to lite models is prohibited).
   - Closed-world citation validation: drops and logs any hallucination attempts (no case law or outside sections).
4. **Multilingual Translation Layer**:
   - Local `ai4bharat/indictrans2-en-indic-dist-200M` model runs completely on CPU/CUDA with **zero Gemini API calls**.
   - Language-aware legal glossary enforcement (`hi` and `ta`) preserving statutory identifiers, Section numbers, and Act names in English.
5. **Interactive UI**:
   - React + Tailwind CSS interface with trilingual toggle (**English | हिंदी | தமிழ்**), collapsible "Legal basis" (with verbatim statutory text) and "Typical phrasing" panels, and client intake context personalization.

---

## Supported Document & Clause Types

### Supported Document Types
- `employment_contract`: Employment agreements, appointment letters, service bonds, supplemental agreements.
- `rental_agreement`: Residential leases, commercial tenancy contracts.
- `loan_agreement`: Credit facilities, personal and commercial loan agreements, promissory terms.

### Supported Clause Types (14 Total)
1. **Indemnity & Hold Harmless** (`indemnity`): Unilateral third-party or broad indemnity liabilities.
2. **Non-Compete / Restraint of Trade** (`non_compete`): Post-termination employment or commercial restrictions.
3. **Arbitration & Dispute Resolution** (`dispute_resolution` / `arbitration`): Unilateral forum selection or skewed dispute procedures.
4. **Penalty & Liquidated Damages** (`penalty`): Disproportionate breach damages or deposit forfeitures.
5. **Unilateral Termination** (`termination`): Asymmetric termination notice or termination without cause.
6. **Penal / Default Interest** (`penal_interest`): Retroactive or compounded punitive default interest rates.
7. **Acceleration of Loan** (`acceleration`): Immediate demand for full principal on technical or uncurable default.
8. **Foreclosure / Prepayment Charges** (`foreclosure_charges`): Excessive exit penalties or locks on early loan prepayment.
9. **Unilateral Interest Rate Change** (`unilateral_interest_change`): Floating or discretionary interest rate revisions without benchmark indexing.
10. **Guarantor Liability** (`guarantor_liability`): Unlimited, continuing personal guarantees and asset seizure rights.
11. **Set-Off / Banker Lien** (`set_off_lien`): General lien and set-off across borrower and family accounts without notice.
12. **Service Bond / Mandatory Lock-in** (`service_bond`): Unliquidated damages or certificates retention for leaving before lock-in terms.
13. **IP Assignment / Invention Ownership** (`ip_assignment`): Overbroad assignment of personal inventions, creations, or post-separation output.
14. **Notice Period / Garden Leave Imbalance** (`notice_period_garden_leave`): Extreme notice period disparity or unilateral unpaid garden leave.

### Client Intake Ranking Boosts
- **Dependents Boost (`has_dependents=True`)**:
  - High financial liability clauses threatening family stability receive priority boosts:
    - `indemnity`: **+45.0**
    - `penalty` / Security Deposit Forfeiture: **+45.0**
    - `guarantor_liability` & `acceleration`: **+45.0**
    - `set_off_lien`, `penal_interest`, `foreclosure_charges`: **+35.0**
    - `service_bond`: **+30.0**
    - `termination`: **+15.0**
- **Document Type Prioritization**:
  - `loan_agreement`: Prioritizes `acceleration`, `guarantor_liability`, `penal_interest` (+30.0), `set_off_lien`, `foreclosure_charges`, `unilateral_interest_change` (+25.0).
  - `employment_contract`: Prioritizes `non_compete`, `service_bond` (+25.0), `indemnity`, `ip_assignment`, `notice_period_garden_leave` (+20.0).
  - `rental_agreement`: Prioritizes `termination` (+25.0) and `penalty` / Security Deposit (+20.0).

---

## Known Limitations

1. **Statute Ingestion & Provenance Verification**:
   - Only statutory texts matching official government sources (`indiacode.nic.in` / `legislative.gov.in`) with 100% exact provenance are admitted into `data/statutes/`.
   - Automated fetching from `indiacode.nic.in` is susceptible to `HTTP 504 Gateway Timeout` due to government server rate-limiting/firewalls. In such cases, official PDFs must be manually downloaded and placed in `data/statutes_raw/` (`arbitration_and_conciliation_act_1996.pdf` and `consumer_protection_act_2019.pdf`) for local verification.
2. **Citation Model Pinning & API Free-Tier Quota**:
   - Citation generation requires deep statutory reasoning and is strictly pinned to the strongest Gemini model (`gemini-3.8-flash`). Under Google's free-tier rate limits (20 requests per day per model), if the strongest model's daily quota is exhausted, citation generation safely returns `"Legal basis unavailable right now"` rather than guessing with lightweight models.
3. **Local IndicTrans2 CPU Inference Latency**:
   - IndicTrans2 200M beam search on CPU averages ~5–8 seconds per clause. While translation is fully private and free from LLM API fees, running on CPU introduces noticeable latency compared to GPU acceleration.
4. **Jurisdictional Scope**:
   - Current statutory knowledge base covers federal Indian statutes (Constitution of India, Indian Contract Act 1872). State-specific amendments and foreign legal jurisdictions are outside the current corpus scope.

---

## Quick Start & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- Gemini API Key

### Backend Setup
```bash
# 1. Clone repository and navigate to root
cd Legal-Chatbot

# 2. Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# 3. Install backend dependencies
pip install -r backend/requirements.txt

# 4. Configure environment variables
cp .env.example .env
# Edit .env and supply GEMINI_API_KEY (and optional HF_TOKEN)

# 5. Start FastAPI backend
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Frontend Setup
```bash
cd frontend
npm install
npm run dev
```
Open `http://localhost:5173` in your browser.
