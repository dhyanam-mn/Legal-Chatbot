# Legal Review: Statute Mappings for Phase 4 Clause Types

This document provides the legal review and justification for statutory mappings across the 9 new Phase 4 clause types in accordance with the project's strict statutory provenance discipline: **only provisions whose official gazette / India Code PDFs are verified in `data/statutes_raw/` and ingested into `data/statutes/` may be mapped or cited**. If no verified statutory provision directly applies, the mapping is set to empty (`[]`) so that the UI strictly displays `"No statutory provision retrieved"`.

Case-law references in this document are included strictly for lawyer verification and are prohibited from user-facing application outputs.

---

## Summary Matrix

| # | Clause Type | Document Scope | Verified Provisions Mapped | Verified Supporting Quote & Legal Rationale | UI Display Status |
|---|---|---|---|---|---|
| 1 | `penal_interest` | Loan Agreement | `ICA-1872-s74`, `CPA-2019-s2-46` | **ICA s.74 Explanation**: *"A stipulation for increased interest from the date of default may be a stipulation by way of penalty."*<br>**CPA s.2(46)(ii)**: *"(ii) imposing any penalty on the consumer, for the breach of contract thereof which is wholly disproportionate to the loss occurred due to such breach to the other party to the contract;"* | Validated citations |
| 2 | `acceleration` | Loan Agreement | *None* (`[]`) | Neither ICA s.39, s.73, nor any verified provision governs loan acceleration; regulated under RBI Master Directions (unverified). Removed. | "No statutory provision retrieved" |
| 3 | `foreclosure_charges` | Loan Agreement | `CPA-2019-s2-46` | **CPA s.2(46)(iii)**: *"(iii) refusing to accept early repayment of debts on payment of applicable penalty;"* and **s.2(46)(vi)**: *"(vi) imposing on the consumer any unreasonable charge, obligation or condition which puts such consumer to disadvantage;"* | Validated citations |
| 4 | `unilateral_interest_change` | Loan Agreement | *None* (`[]`) *[pending lawyer review]* | **CPA s.2(46)(vi)** removed pending lawyer review. | "No statutory provision retrieved" |
| 5 | `guarantor_liability` | Loan Agreement | *None* (`[]`) | Guarantee is governed by ICA ss. 126 & 128 (unverified in corpus); indemnity sections (ICA ss. 124–125) are legally distinct and excluded. Removed. | "No statutory provision retrieved" |
| 6 | `set_off_lien` | Loan Agreement | *None* (`[]`) | Banker's general lien is codified under ICA s.171 (unverified in corpus); general consumer terms cannot substitute for governing lien law. Removed. | "No statutory provision retrieved" |
| 7 | `service_bond` | Employment Contract | `ICA-1872-s74`, `ICA-1872-s27` | **ICA s.74**: *"party complaining of the breach is entitled... to receive... reasonable compensation not exceeding the amount so named or... the penalty stipulated for."*<br>**ICA s.27**: *"Every agreement by which any one is restrained from exercising a lawful profession, trade or business of any kind, is to that extent void."* | Validated citations |
| 8 | `ip_assignment` | Employment Contract | *None* (`[]`) | Employee IP rights are governed by Copyright Act 1957 s.17 and Patents Act 1970 s.39 (unverified); general contract sections do not apply. Removed. | "No statutory provision retrieved" |
| 9 | `notice_period_garden_leave` | Employment Contract | `ICA-1872-s74` *[ICA-1872-s27 pending lawyer review]* | **ICA s.74**: *"reasonable compensation not exceeding the amount so named or... the penalty stipulated for."* (ICA s.27 removed pending lawyer review). | Validated citations |

---

## Detailed Legal Analysis per Clause Type

### 1. Penal / Default Interest (`penal_interest`)
- **Verified Mapping**: `["ICA-1872-s74", "CPA-2019-s2-46"]`
- **Exact Quotes from Verified JSON**:
  - **Indian Contract Act, 1872 — Section 74 (Explanation)**:
    > *"Explanation.—A stipulation for increased interest from the date of default may be a stipulation by way of penalty."*
    and main operative text:
    > *"When a contract has been broken, if a sum is named in the contract as the amount to be paid in case of such breach, or if the contract contains any other stipulation by way of penalty, the party complaining of the breach is entitled, whether or not actual damage or loss is proved to have been caused thereby, to receive from the party who has broken the contract reasonable compensation not exceeding the amount so named or, as the case may be, the penalty stipulated for."*
  - **Consumer Protection Act, 2019 — Section 2(46), Sub-clause (ii)**:
    > *"(ii) imposing any penalty on the consumer, for the breach of contract thereof which is wholly disproportionate to the loss occurred due to such breach to the other party to the contract;"*
- **Legal Justification**: Both provisions directly address default interest and penal consequences. The Explanation to Section 74 of the Indian Contract Act expressly categorizes increased interest upon default as a penalty stipulation subject to reasonable compensation, while Section 2(46)(ii) of the Consumer Protection Act defines disproportionate breach penalties on consumers as unfair contracts.

### 2. Loan Acceleration (`acceleration`)
- **Verified Mapping**: `[]` *(Removed)*
- **Statutory Provisions Considered**:
  - *ICA Section 39 (Refusal of party to perform wholly)*: Governs contract rescission upon complete refusal, not loan debt acceleration covenants.
  - *ICA Section 73 (Compensation for loss or damage)*: Relates to unliquidated breach damages, not accelerated maturity of principal debt.
- **Legal Justification**: Loan acceleration upon default is a contractual debt recovery remedy regulated under the Reserve Bank of India (RBI) Fair Practices Code and Master Directions for Lending, rather than codified contract statutes. Because RBI Master Directions are not in the verified statutory database, mapping to ICA sections is ungrounded.
- **Action Taken**: Removed all mappings. System reliably outputs `"No statutory provision retrieved"`.

### 3. Foreclosure / Prepayment Charges (`foreclosure_charges`)
- **Verified Mapping**: `["CPA-2019-s2-46"]`
- **Exact Quotes from Verified JSON**:
  - **Consumer Protection Act, 2019 — Section 2(46), Sub-clauses (iii) & (vi)**:
    > *"(iii) refusing to accept early repayment of debts on payment of applicable penalty;"*
    > *"(vi) imposing on the consumer any unreasonable charge, obligation or condition which puts such consumer to disadvantage;"*
- **Statutory Provisions Excluded**:
  - *ICA Section 74*: Prepayment is an option for early discharge, not a breach of contract; therefore Section 74 is legally inappropriate.
- **Legal Justification**: Section 2(46)(iii) explicitly addresses early repayment of debts, while Section 2(46)(vi) designates the imposition of unreasonable charges or conditions putting the consumer at significant disadvantage as an unfair contract.
- **Action Taken**: Retained solely `CPA-2019-s2-46`.

### 4. Unilateral Interest Rate Change (`unilateral_interest_change`)
- **Verified Mapping**: `[]` *(Removed pending lawyer review)*
- **Statutory Provisions Considered**:
- **Consumer Protection Act, 2019 — Section 2(46), Sub-clause (vi)**:
    > *"(vi) imposing on the consumer any unreasonable charge, obligation or condition which puts such consumer to disadvantage;"*
- **Legal Justification & Status**: While Section 2(46)(vi) characterizes disadvantageous unilateral obligations as unfair contract terms, whether floating benchmark rate adjustment clauses directly fall under consumer unfairness without financial regulatory context is marked **pending lawyer review**. Removed from active mapping; outputs `"No statutory provision retrieved"`.

### 5. Guarantor Liability (`guarantor_liability`)
- **Verified Mapping**: `[]` *(Removed)*
- **Statutory Provisions Considered**:
  - *ICA Sections 124–125*: These sections strictly govern **contracts of indemnity** (where one party promises to save the other from loss caused by the promisor or third party).
  - *ICA Sections 126 & 128*: Guarantee contracts and co-extensive surety liabilities are codified under Section 126 and Section 128. Neither section is present in the verified statutory repository.
- **Legal Justification**: In Indian law, indemnity (s.124) and guarantee (s.126) are distinct instruments with different legal requirements and liabilities. Mapping guarantor liability to indemnity sections is legally inaccurate.
- **Action Taken**: Removed all mappings. System reliably outputs `"No statutory provision retrieved"`.

### 6. Set-Off / Banker's Lien (`set_off_lien`)
- **Verified Mapping**: `[]` *(Removed)*
- **Statutory Provisions Considered**:
  - *ICA Section 171 (General lien of bankers)*: The substantive statutory provision codifying banker's lien in India is Section 171, which is not verified or ingested in the database.
- **Legal Justification**: Substantive law governing banker's lien resides in ICA s.171. Applying general consumer unfairness provisions without the governing lien statute represents ungrounded statutory proxying.
- **Action Taken**: Removed all mappings. System reliably outputs `"No statutory provision retrieved"`.

### 7. Service Bond / Mandatory Lock-in (`service_bond`)
- **Verified Mapping**: `["ICA-1872-s74", "ICA-1872-s27"]`
- **Exact Quotes from Verified JSON**:
  - **Indian Contract Act, 1872 — Section 74**:
    > *"When a contract has been broken, if a sum is named in the contract as the amount to be paid in case of such breach, or if the contract contains any other stipulation by way of penalty, the party complaining of the breach is entitled, whether or not actual damage or loss is proved to have been caused thereby, to receive from the party who has broken the contract reasonable compensation not exceeding the amount so named or, as the case may be, the penalty stipulated for."*
  - **Indian Contract Act, 1872 — Section 27**:
    > *"Every agreement by which any one is restrained from exercising a lawful profession, trade or business of any kind, is to that extent void."*
- **Legal Justification**:
  - Under Section 74, employer recovery under employment bonds is capped strictly to actual reasonable expenses proved to have been incurred in specialized employee training rather than forfeiture of the stipulated penal sum. *(For lawyer verification only: Toshiba Anand Lamps v. Chandra; Sicpa India v. Manas Pratim Deb. Strictly excluded from user-facing output).*
  - Under Section 27, any service bond condition attempting to restrain an employee from joining a competitor or exercising their profession post-resignation is void to that extent.

### 8. IP Assignment / Overbroad Ownership (`ip_assignment`)
- **Verified Mapping**: `[]` *(Removed)*
- **Statutory Provisions Considered**:
  - *Copyright Act, 1957 — Section 17(c)*: First ownership of copyright in works created under employment contract of service (unverified).
  - *Patents Act, 1970 — Section 39 / Inventions Law*: Regulates employee patent assignments (unverified).
- **Legal Justification**: Specialized intellectual property enactments govern ownership boundaries. Applying generic contract restraint provisions (ICA s.27) to standard or overbroad IP assignments without verified IP statutes is legally tenuous.
- **Action Taken**: Removed all mappings. System reliably outputs `"No statutory provision retrieved"`.

### 9. Notice Period / Garden Leave Imbalance (`notice_period_garden_leave`)
- **Verified Mapping**: `["ICA-1872-s74"]` *(ICA-1872-s27 removed pending lawyer review)*
- **Exact Quotes from Verified JSON**:
  - **Indian Contract Act, 1872 — Section 74**:
    > *"When a contract has been broken, if a sum is named in the contract as the amount to be paid in case of such breach, or if the contract contains any other stipulation by way of penalty, the party complaining of the breach is entitled, whether or not actual damage or loss is proved to have been caused thereby, to receive from the party who has broken the contract reasonable compensation not exceeding the amount so named or, as the case may be, the penalty stipulated for."*
- **Provisions Under Review**:
  - *Indian Contract Act, 1872 — Section 27*: Application of Section 27 (restraint of trade) to notice-period garden leave prior to contract termination vs post-employment covenants is marked **pending lawyer review** and removed from active mappings.
- **Legal Justification**:
  - Section 74 limits employer liquidated damages or notice-pay forfeiture demands for early employee resignation strictly to reasonable compensation. Validated citations cite Section 74.

---

## Recommendation for Future Statute Additions (Requires Official PDF Ingestion)
To safely enable verified statutory citations for the 4 unmapped types, the following official Acts must be downloaded to `data/statutes_raw/`, verified via provenance diff, and ingested:
1. **Indian Contract Act, 1872**: Ingest Sections 126, 128, and 129 (Guarantees) and Section 171 (Banker's Lien).
2. **Copyright Act, 1957**: Ingest Section 17 (First owner of copyright in employment).
3. **Patents Act, 1970**: Ingest Section 39 / employee invention assignment provisions.
