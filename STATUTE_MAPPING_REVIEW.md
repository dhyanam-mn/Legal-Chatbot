# Legal Review: Statute Mappings for Phase 4 Clause Types

This document provides the legal review and justification for statutory mappings across the 9 new Phase 4 clause types in accordance with the project's strict statutory provenance discipline: **only provisions whose official gazette / India Code PDFs are verified in `data/statutes_raw/` and ingested into `data/statutes/` may be mapped or cited**. If no verified statutory provision directly applies, the mapping is set to empty (`[]`) so that the UI strictly displays `"No statutory provision retrieved"`.

---

## Summary Matrix

| # | Clause Type | Document Scope | Verified Provisions Mapped | Legal Justification & Rationale | UI Display Status |
|---|---|---|---|---|---|
| 1 | `penal_interest` | Loan Agreement | `ICA-1872-s74`, `CPA-2019-s2-46` | ICA s.74 Explanation explicitly classifies enhanced default interest as a penalty limiting recovery to reasonable compensation; CPA s.2(46)(iii) prohibits disproportionate breach penalties. | Validated citations |
| 2 | `acceleration` | Loan Agreement | *None* (`[]`) | Governed by contractual acceleration covenants and RBI Master Directions; neither ICA s.39 nor s.73 establishes a governing acceleration standard. | "No statutory provision retrieved" |
| 3 | `foreclosure_charges` | Loan Agreement | `CPA-2019-s2-46` | Prepayment is an early-performance option rather than a breach under ICA s.74, but CPA s.2(46)(vi) prohibits unreasonable charges/conditions putting consumers at significant disadvantage. | Validated citations |
| 4 | `unilateral_interest_change` | Loan Agreement | `CPA-2019-s2-46` | CPA s.2(46)(ii) explicitly defines any term entitling one party to alter the terms of the contract unilaterally without the concurrence of the other party as an unfair contract. | Validated citations |
| 5 | `guarantor_liability` | Loan Agreement | *None* (`[]`) | Contracts of guarantee and co-extensive surety liabilities are codified under ICA ss. 126, 128, and 129, which are not in the verified corpus; indemnity sections (ICA ss. 124–125) are legally distinct and excluded. | "No statutory provision retrieved" |
| 6 | `set_off_lien` | Loan Agreement | *None* (`[]`) | Banker's general lien is codified under Section 171 of the Indian Contract Act, 1872, which is unverified; citing general consumer provisions without the substantive lien statute would be ungrounded. | "No statutory provision retrieved" |
| 7 | `service_bond` | Employment Contract | `ICA-1872-s74`, `ICA-1872-s27` | ICA s.74 restricts employer bond recovery to actual, reasonable training expenses proved, while ICA s.27 invalidates any bond term acting as a post-employment restraint on trade. | Validated citations |
| 8 | `ip_assignment` | Employment Contract | *None* (`[]`) | Employee intellectual property rights are governed by Copyright Act, 1957 (s.17) and Patents Act, 1970 (s.39), neither of which is verified; applying generic contract restraint provisions is legally tenuous. | "No statutory provision retrieved" |
| 9 | `notice_period_garden_leave` | Employment Contract | `ICA-1872-s27`, `ICA-1872-s74` | ICA s.27 voids post-termination garden leave extending beyond employment as a restraint of trade, while ICA s.74 governs unilateral pay-in-lieu forfeiture penalties. | Validated citations |

---

## Detailed Legal Analysis per Clause Type

### 1. Penal / Default Interest (`penal_interest`)
- **Verified Mapping**: `["ICA-1872-s74", "CPA-2019-s2-46"]`
- **Statutory Provisions**:
  - **Indian Contract Act, 1872 — Section 74 (Explanation)**: *"A stipulation for increased interest from the date of default may be a stipulation by way of penalty."* The court will only award reasonable compensation not exceeding the penalty stipulated.
  - **Consumer Protection Act, 2019 — Section 2(46)(iii)**: Unfair contract includes *"imposing on the consumer any penalty for the breach of contract thereof which is wholly disproportionate to the loss occurred due to such breach to the other party to the contract."*
- **Legal Justification**: Direct and codified statutory alignment. Both provisions specifically control excessive and default-triggered interest surcharges in standard and consumer lending contracts.

### 2. Loan Acceleration (`acceleration`)
- **Verified Mapping**: `[]` *(Removed)*
- **Statutory Provisions Considered**:
  - *ICA Section 39 (Refusal of party to perform wholly)*: Does not govern loan acceleration; acceleration enforces full debt maturity rather than contract rescission.
  - *ICA Section 73 (Compensation for loss or damage)*: Relates to unliquidated damages for breach, not accelerated principal debt recovery.
- **Legal Justification**: Loan acceleration upon default is a contractual debt recovery remedy regulated in India under the Reserve Bank of India (RBI) Fair Practices Code and Master Directions for Lending, rather than statutory contract law. Because RBI directions are not part of the verified statutory corpus, mapping to ICA sections would be legally ungrounded.
- **Action Taken**: Removed all mappings. System reliably outputs `"No statutory provision retrieved"`.

### 3. Foreclosure / Prepayment Charges (`foreclosure_charges`)
- **Verified Mapping**: `["CPA-2019-s2-46"]`
- **Statutory Provisions Considered**:
  - *ICA Section 74*: Prepayment is the borrower exercising an option for early payoff, not a breach of contract; therefore, Section 74 is legally inappropriate.
  - *CPA Section 2(46)(vi)*: Covers *"imposing on the consumer any unreasonable charge, obligation or condition which puts such consumer to significant disadvantage."*
- **Legal Justification**: Prepayment penalties on floating rate loans have been prohibited by RBI regulatory policy; under statutory consumer protection law, imposing exit penalties on consumers seeking to switch lenders or prepay constitutes an unreasonable charge under CPA s.2(46)(vi).
- **Action Taken**: Removed ICA s.74; retained `CPA-2019-s2-46`.

### 4. Unilateral Interest Rate Change (`unilateral_interest_change`)
- **Verified Mapping**: `["CPA-2019-s2-46"]`
- **Statutory Provisions Considered**:
  - *ICA Section 10 & 16*: Generic contract formation and undue influence; do not directly regulate unilateral modification terms during contract execution.
  - *CPA Section 2(46)(ii)*: Covers *"entitling one party to the contract to terminate such contract unilaterally without reasonable cause, or to alter the terms thereof unilaterally without the concurrence of the other party."*
- **Legal Justification**: CPA s.2(46)(ii) is a direct, explicit statutory prohibition against unilateral alteration of terms without the counterparty's concurrence.
- **Action Taken**: Retained solely `CPA-2019-s2-46`.

### 5. Guarantor Liability (`guarantor_liability`)
- **Verified Mapping**: `[]` *(Removed)*
- **Statutory Provisions Considered**:
  - *ICA Sections 124–125*: These sections strictly govern **contracts of indemnity** (where one party promises to save the other from loss caused by the conduct of the promisor or third party).
  - *ICA Sections 126 & 128*: Guarantee contracts and co-extensive surety liabilities are defined under Section 126 and Section 128. Neither section is in the verified statutory repository.
- **Legal Justification**: In Indian jurisprudence, an indemnity contract (ICA s.124) and a guarantee contract (ICA s.126) are distinct legal instruments with different causes of action and limitation periods. Mapping guarantor liability to indemnity sections is legally inaccurate.
- **Action Taken**: Removed all mappings. System reliably outputs `"No statutory provision retrieved"`.

### 6. Set-Off / Banker's Lien (`set_off_lien`)
- **Verified Mapping**: `[]` *(Removed)*
- **Statutory Provisions Considered**:
  - *ICA Section 171 (General lien of bankers)*: The substantive statutory provision codifying banker's lien in India is Section 171, which is not currently verified or ingested.
  - *CPA Section 2(46)*: While an overly broad set-off clause can put consumers at a disadvantage, citing consumer unfairness without the governing lien statute represents weak grounding.
- **Legal Justification**: Substantive law governing banker's lien resides in ICA s.171. In the absence of s.171 in the verified corpus, maintaining an unverified proxy mapping would violate strict provenance rules.
- **Action Taken**: Removed all mappings. System reliably outputs `"No statutory provision retrieved"`.

### 7. Service Bond / Mandatory Lock-in (`service_bond`)
- **Verified Mapping**: `["ICA-1872-s74", "ICA-1872-s27"]`
- **Statutory Provisions**:
  - **Indian Contract Act, 1872 — Section 74**: In Indian employment jurisprudence (*Toshiba Anand Lamps v. Chandra*, *Sicpa India v. Manas Pratim Deb*), employment bond penalties are treated under Section 74, capping employer recovery strictly to actual, reasonable expenses incurred in specialized training.
  - **Indian Contract Act, 1872 — Section 27**: Voids any bond stipulation that attempts to prevent the employee from taking up alternative employment after separation.
- **Legal Justification**: Both provisions directly articulate the statutory boundaries governing employment bonds and training cost recovery in India.

### 8. IP Assignment / Overbroad Ownership (`ip_assignment`)
- **Verified Mapping**: `[]` *(Removed)*
- **Statutory Provisions Considered**:
  - *Copyright Act, 1957 — Section 17(c)*: First ownership of copyright in works made in the course of employment under a contract of service.
  - *Patents Act, 1970 — Section 39 / General Inventions Law*: Regulates employee patent assignments.
  - *ICA Sections 23 & 27*: Restraint of trade or unconscionability; general assignment of inventions during employment does not constitute a restraint of trade.
- **Legal Justification**: Specialized intellectual property statutes govern assignment boundaries. Applying ICA s.23 or s.27 to standard or overbroad IP clauses without verified IP statutes is legally tenuous.
- **Action Taken**: Removed all mappings. System reliably outputs `"No statutory provision retrieved"`.

### 9. Notice Period / Garden Leave Imbalance (`notice_period_garden_leave`)
- **Verified Mapping**: `["ICA-1872-s27", "ICA-1872-s74"]`
- **Statutory Provisions**:
  - **Indian Contract Act, 1872 — Section 27**: Under settled Supreme Court precedent (*Percept D'Mark v. Zaheer Khan*), post-termination garden leave extending past the effective cessation of employment operates as a void post-service restraint of trade.
  - **Indian Contract Act, 1872 — Section 74**: Applies to disproportionate notice pay forfeitures and liquidated damages demanded from employees.
- **Legal Justification**: Direct statutory applicability for post-employment garden leave restraints (s.27) and unconscionable pay-in-lieu forfeiture penalties (s.74).

---

## Recommendation for Future Statute Additions (Requires Official PDF Ingestion)
To safely enable verified statutory citations for the 4 removed types, the following official Acts must be downloaded to `data/statutes_raw/`, checked via provenance diff, and ingested:
1. **Indian Contract Act, 1872**: Ingest Sections 126, 128, and 129 (Guarantees) and Section 171 (Banker's Lien).
2. **Copyright Act, 1957**: Ingest Section 17 (First owner of copyright in employment).
3. **Patents Act, 1970**: Ingest Section 39 / assignment provisions.
