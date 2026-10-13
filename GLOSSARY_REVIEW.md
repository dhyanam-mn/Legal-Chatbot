# Legal Glossary & Mandatory Disclaimer Review (`GLOSSARY_REVIEW.md`)

This document provides the complete human-review reference for the fixed Hindi (`hi`) and Tamil (`ta`) legal glossary ([`backend/data/legal_glossary.json`](file:///c:/Users/dhyan/OneDrive/Desktop/Projects/Legal-Chatbot/backend/data/legal_glossary.json)), the post-processing enforcement rules ([`backend/app/translator.py`](file:///c:/Users/dhyan/OneDrive/Desktop/Projects/Legal-Chatbot/backend/app/translator.py)), and the hardcoded mandatory legal disclaimers ([`backend/app/config.py`](file:///c:/Users/dhyan/OneDrive/Desktop/Projects/Legal-Chatbot/backend/app/config.py)).

---

## 1. Core Contract & Clause Terms (`legal_glossary.json`)

| English Term | Fixed Hindi Term (`hi`) |Fixed Tamil Term (`ta`) | Register & Usage Notes |
|---|---|---|---|
| **indemnity / indemnification** | `क्षतिपूर्ति` | `இழப்பீட்டுப் பொறுப்பு` | Standard formal legal register for contractual indemnity liability. |
| **indemnify** | `क्षतिपूर्ति करना` | `இழப்பீடு வழங்குதல்` | Verb/action form; in Tamil, distinct from `பிரிவினை ஊதியம்` / `பிரிவு இழப்பீட்டுத் தொகை` (severance pay). |
| **arbitration** | `मध्यस्थता` | `இசைவுத்தீர்ப்பு` | Standard statutory Tamil term for arbitration (replaced colloquial `மத்தியஸ்தம்`). |
| **jurisdiction** | `क्षेत्राधिकार` | `அதிகார வரம்பு` | Court or territorial jurisdiction. |
| **forum selection** | `क्षेत्राधिकार चयन` | `நீதிமன்றத் தேர்வு` | Choice of court / dispute forum. |
| **unilateral forum selection** | `एकपक्षीय क्षेत्राधिकार चयन` | `ஒருதலைப்பட்ச நீதிமன்றத் தேர்வு` | One-sided forum selection clause. |
| **maintenance** | `रखरखाव` | `பராமரிப்பு` | Property/premises maintenance in rental agreements. |
| **termination** | `समाप्ति` | `ஒப்பந்த முடிவு` | Contractual termination (replaces employment-only `பணிநீக்கம்`). |
| **unilateral termination** | `एकपक्षीय समाप्ति` | `ஒருதலைப்பட்ச ஒப்பந்த முடிவு` | One-sided termination right. |
| **penalty** | `शास्ति` | `அபராதம்` | Contractual penalty (replaces criminal punishment `दंड` / `தண்டனை`). |
| **liquidated damages** | `परिनिर्धारित क्षतिपूर्ति` | `முன்நிர்ணயிக்கப்பட்ட இழப்பீடு` | Pre-estimated contractual damages (replaces literal "dissolved damages" `परिसमापन नुकसान` / `கலைக்கப்பட்ட சேதங்கள்`). |
| **non-compete** | `गैर-प्रतिस्पर्धा` | `போட்டித் தடை` | Post-employment or contractual non-compete restriction. |
| **restraint of trade** | `व्यापार पर प्रतिबंध` | `வணிகத் தடை` | Statutory phrase under Section 27 of the Indian Contract Act, 1872. |
| **terms** | `शर्तें` | `விதிமுறைகள்` | Contractual terms/conditions (replaces literal "words" `शब्दों` / `சொற்கள்`). |
| **clause** | `खंड` | `பிரிவு` | Contractual clause (replaces transliterated `क्लॉज` or `वाசகம்`). |

---

## 2. Statutory & Legal Basis Terms (`Phase 3`)

| English Statutory Term | Fixed Hindi Term (`hi`) | Fixed Tamil Term (`ta`) | Statutory Context |
|---|---|---|---|
| **void** | `शून्य` | `செல்லாதது` | e.g., Section 27 & Section 28 of the Indian Contract Act, 1872 (replaces literal "vacuum" `வெற்றிட`). |
| **unlawful** | `विधिविरुद्ध` | `சட்டவிரோதமான` | Section 23 of the Indian Contract Act, 1872. |
| **public policy** | `लोक नीति` | `பொதுக் கொள்கை` | Section 23 of the Indian Contract Act, 1872. |
| **breach of contract** | `अनुबंध भंग` | `ஒப்பந்த மீறல்` | Sections 73 & 74 of the Indian Contract Act, 1872. |
| **reasonable compensation** | `उचित क्षतिपूर्ति` | `நியாயமான இழப்பீடு` | Section 74 of the Indian Contract Act, 1872. |
| **contract of indemnity** | `क्षतिपूर्ति की संविदा` | `இழப்பீட்டு ஒப்பந்தம்` | Section 124 of the Indian Contract Act, 1872. |
| **arbitral tribunal** | `मध्यस्थता अधिकरण` | `இசைவுத்தீர்ப்பு தீர்ப்பாயம்` | Arbitration and Conciliation Act, 1996. |
| **arbitration agreement** | `मध्यस्थता समझौता` | `இசைவுத்தீர்ப்பு ஒப்பந்தம்` | Section 7 of the Arbitration and Conciliation Act, 1996. |
| **restraint of legal proceedings** | `विधिक कार्यवाहियों में अवरोध` | `சட்ட நடவடிக்கைகளுக்குத் தடை` | Section 28 of the Indian Contract Act, 1872. |

---

## 3. Untranslated English Statute Identifiers (`hi` & `ta`)

Per Phase 3 specification, all statute IDs, section/article numbers, and Act names are kept **untranslated in English** inside Hindi and Tamil outputs:
- **Act Names**: `Indian Contract Act, 1872`, `Constitution of India`, `Arbitration and Conciliation Act, 1996`, `Consumer Protection Act, 2019`
- **Section / Article Labels**: `Section 10`, `Section 16`, `Section 19A`, `Section 23`, `Section 27`, `Section 28`, `Section 39`, `Section 73`, `Section 74`, `Section 75`, `Section 124`, `Section 125`, `Article 14`, `Article 19`, `Article 21`, `Article 226`, `Article 300A`
- **Provision IDs**: `ICA-1872-s27`, `COI-art19`, `ICA-1872-s74`, `ICA-1872-s124`, `ICA-1872-s125`, `ICA-1872-s28`, etc.

---

## 4. Hardcoded Mandatory Legal Disclaimers (`backend/app/config.py`)

These disclaimers are hardcoded in `backend/app/config.py` and are **never** generated or altered by the LLM or machine translation pipeline:

- **English (`MANDATORY_DISCLAIMER`)**:
  > `"This explains what the clause means. It is not legal advice. Consult a lawyer before acting on this."`
- **Hindi (`MANDATORY_DISCLAIMER_HI`)**:
  > `"यह क्लॉज के अर्थ की व्याख्या करता है। यह कानूनी सलाह नहीं है। इस पर कार्रवाई करने से पहले वकील से परामर्श लें।"`
- **Tamil (`MANDATORY_DISCLAIMER_TA`)**:
  > `"இது இந்தப் பிரிவின் பொருளை விளக்குகிறது. இது சட்ட ஆலோசனை அல்ல. இதன் அடிப்படையில் செயல்படுவதற்கு முன் ஒரு வழக்கறிஞரைக் கலந்தாலோசிக்கவும்."`
