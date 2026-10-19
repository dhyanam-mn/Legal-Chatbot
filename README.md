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
3. **Statutory Citations & Model Hierarchy**:
   - Pinned strictly to the strongest configured Gemini model (`GEMINI_MODELS[0]`), which is verified to be a stable GA model (`gemini-3.8-flash`, not preview/experimental).
   - Full ordered model hierarchy for classification quota rotation:
     1. `gemini-3.8-flash` (Stable GA) — Citation engine pinned here
     2. `gemini-3.7-flash` (Stable GA)
     3. `gemini-3.6-flash` (Stable GA)
     4. `gemini-3.5-flash` (Stable GA)
     5. `gemini-3.5-flash-lite` (Stable GA)
     6. `gemini-3.1-flash-lite` (Stable GA)
   - Generates single-sentence descriptive reasons and attaches verbatim statutory provision text in English.
   - Falls back safely to `"Legal basis unavailable right now"` if the strongest model is unavailable (rotation to lite models is prohibited).
   - Closed-world citation validation: drops and logs any hallucination attempts (no case law or outside sections).
4. **Multilingual Translation Layer (Bidirectional)**:
   - **English -> Hindi/Tamil**: Local `ai4bharat/indictrans2-en-indic-dist-200M` model runs completely on CPU/CUDA with **zero Gemini API calls**.
   - Language-aware legal glossary enforcement (`hi` and `ta`) preserving statutory identifiers, Section numbers, and Act names in English.
   - **Indic -> English (Phase 5 Input Layer)**: Lazy CPU engine powered by `ai4bharat/indictrans2-indic-en-dist-200M` (`benfranklinms/indictrans2-indic-en-dist-200M`) translating Hindi and Tamil documents into English for semantic vector grounding and classification, with hash-based caching and zero Gemini calls.
5. **Interactive UI**:
   - React + Tailwind CSS interface with trilingual toggle (**English | हिंदी | தமிழ்**), collapsible "Legal basis" (with verbatim statutory text) and "Typical phrasing" panels, client intake personalization, and experimental machine-translation notice banners for Indic input documents.

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
   - Only statutory texts matching official government sources (`indiacode.nic.in` / `legislative.gov.in` or official PDFs in `data/statutes_raw/`) with 100% exact provenance are admitted into `data/statutes/`.
   - The verified statutory corpus consists of 24 provisions across 4 central Acts:
     - **Constitution of India**: Articles 14, 19, 21, 226, 300A
     - **Indian Contract Act, 1872**: Sections 10, 16, 19A, 23, 27, 28, 39, 73, 74, 75, 124, 125
     - **Arbitration and Conciliation Act, 1996**: Sections 7, 11, 12, 18, 20, 34
     - **Consumer Protection Act, 2019**: Section 2(46) ("unfair contract")
2. **Citation Model Pinning & API Free-Tier Quota**:
   - Citation generation requires deep statutory reasoning and is strictly pinned to the strongest configured Gemini model (`GEMINI_MODELS[0]`). Under Google's free-tier rate limits (20 requests per day per model), if the strongest model's daily quota is exhausted, citation generation safely returns `"Legal basis unavailable right now"` rather than guessing with lightweight models.
3. **Local IndicTrans2 CPU Inference Latency**:
   - `ai4bharat/indictrans2-en-indic-dist-200M` (English -> Hindi/Tamil): ~5–8 seconds per clause on CPU.
   - `ai4bharat/indictrans2-indic-en-dist-200M` / `benfranklinms/indictrans2-indic-en-dist-200M` (Indic -> English):
     - **Hindi -> English**: ~3.56s per clause on CPU (Round-trip similarity: **0.92**)
     - **Tamil -> English**: ~3.16s per clause on CPU (Round-trip similarity: **0.84**)
   - Both models run 100% locally on CPU without external API calls or token fees, and are cached in-memory by SHA-256 text hash.
4. **Jurisdictional Scope**:
   - Current statutory knowledge base covers central Indian statutes (Constitution of India, Indian Contract Act 1872, Arbitration and Conciliation Act 1996, Consumer Protection Act 2019). State-specific amendments and foreign legal jurisdictions are outside the current corpus scope.
5. **Hindi & Tamil Synthetic Contract Wording**:
   - The Hindi (`demo_rental_hi.pdf`) and Tamil (`demo_employment_ta.pdf`) demo contract wording, as well as model output translations, are machine-generated via local IndicTrans2 neural translation and enforced via dictionary glossary rules. The Hindi and Tamil wording has **not been reviewed by a native speaker** or certified by legal counsel.

---

## Quick Start & Installation

### Prerequisites
- Python 3.10+
- Node.js 18+
- Gemini API Key
- *(Optional for Scanned Indic PDFs)* Tesseract OCR with Hindi and Tamil language packs:
  - **Linux (Ubuntu/Debian)**:
    ```bash
    sudo apt-get update
    sudo apt-get install tesseract-ocr tesseract-ocr-hin tesseract-ocr-tam
    ```
  - **macOS (Homebrew)**:
    ```bash
    brew install tesseract tesseract-lang
    ```
  - **Windows**:
    1. Download the installer from the [UB-Mannheim Tesseract repository](https://github.com/UB-Mannheim/tesseract/wiki).
    2. During installation, expand **Additional language data (download)** and check **Hindi** (`hin`) and **Tamil** (`tam`).
    3. Ensure Tesseract installation path (`C:\Program Files\Tesseract-OCR`) is added to the system `PATH` environment variable.

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
