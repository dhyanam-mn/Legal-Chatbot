# Legal Document Chatbot — Project Plan

## What you're building
Upload a legal document → chatbot explains it clause-by-clause in plain language, factors in the client's personal situation (income, dependents, etc.), flags risky clauses, cites relevant constitutional/statutory basis, offers alternatives, and does all of this in English, Hindi, or Tamil.

## Scope discipline
Build in this order. Do not start Phase 2 until Phase 1 works end-to-end on real documents.

---

## Phase 1 — MVP (4-6 weeks solo)

**Goal:** Upload doc → clause extraction → plain-English explanation → flag 5 known risky clause types. One language (English only).

### Tech stack
- **Frontend:** React + Tailwind, simple chat UI (upload button + message thread)
- **Backend:** Python (FastAPI)
- **Doc parsing:** `pdfplumber` for text PDFs, `pytesseract` + `pdf2image` for scanned PDFs
- **Chunking:** split by clause/section (regex on numbering patterns like "1.", "Clause 3", "WHEREAS") not fixed token windows — legal docs have structure, use it
- **Embeddings:** `text-embedding-3-small` (OpenAI) or `bge-small-en` (open-source, cheaper) for clause retrieval
- **Vector store:** ChromaDB (local, free, good enough for MVP scale)
- **LLM:** Claude or GPT-4 via API for clause explanation and classification
- **Legal corpus for Phase 1:** just the 5 clause types below — don't build the full Constitution RAG yet

### The 5 clause types to flag first
1. Indemnity clauses
2. Non-compete / restraint of trade
3. Arbitration / dispute resolution (esp. unilateral forum selection)
4. Penalty / liquidated damages
5. Unilateral termination clauses

For each: build a small reference set (3-5 examples of "standard" vs "one-sided" phrasing) to ground the classifier — don't let the model freely judge "is this fair" with no reference.

### Pipeline
```
Upload → OCR/parse → clause segmentation → 
for each clause:
    embed clause → retrieve similar clauses from reference set →
    classify: standard / flag-worthy →
    if flagged: generate plain-language explanation + why it's risky
→ compile output: full doc summary + flagged clause list
```

### Client context intake
Simple structured form before chat starts (not free text dumped into prompt):
- Employment type (salaried/self-employed/business owner)
- Dependents (yes/no, how many)
- Approx income bracket
- Document type (rental agreement / employment contract / loan agreement / etc.)

Use this to filter which flagged clauses get surfaced first (e.g., maintenance/liability clauses ranked higher if dependents = yes).

### Non-negotiable from day 1
Every response includes: "This explains what the clause means. It is not legal advice. Consult a lawyer before acting on this." Get this disclaimer wording reviewed by an actual lawyer before you show this to a single real user — this is the part that creates liability, not the AI accuracy.

### Phase 1 deliverable
Working demo: upload a rental agreement PDF → get flagged clauses with explanations, in English, disclaimer visible.

---

## Phase 2 — Multilingual (2-3 weeks)

- Add Hindi first, using IndicTrans2 (AI4Bharat, open-source) at the **output layer only** — reason in English, translate final explanations
- Build a legal-terms glossary (fixed translations for indemnity, arbitration, jurisdiction, maintenance, etc.) — force consistent use, don't let the model retranslate the same term differently each time
- Add Tamil second, same glossary approach — test translation quality separately, it's weaker than Hindi for legal register
- UI: check Tamil font rendering + account for text expansion breaking your layout

---

## Phase 3 — Constitutional grounding + alternatives (3-4 weeks)

- Build proper RAG over Constitution + relevant Acts (Indian Contract Act, Consumer Protection Act, etc. depending on document types you support)
- Force citation-only-from-retrieved-context — never let the model cite an article/amendment it wasn't given. This is the #1 hallucination risk in legal AI.
- "Suggest alternatives" feature: retrieve standard/fair clause language for the same clause type, present as "here's how this is typically written" rather than "here's what to demand" — keep it descriptive, not advisory, to stay on the right side of unauthorized-practice-of-law concerns

---

## Phase 4 — Polish / expand
- More clause types and document types (employment contracts, loan agreements, etc.)
- More languages if there's demand
- Client history / multiple documents per client

---

## What to do this week
1. Set up FastAPI + React skeleton
2. Get PDF parsing working on 3-4 real sample documents (grab public rental/employment agreement templates)
3. Write clause segmentation logic and manually verify it splits correctly
4. Pick and test one clause type (start with indemnity) end-to-end: extract → classify → explain

Don't touch Hindi/Tamil or Constitution retrieval until this loop works reliably.
