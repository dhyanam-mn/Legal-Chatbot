import json
from collections import Counter
from app.vector_store import get_vector_store, retrieve_statutes_for_clause, CLAUSE_TYPE_STATUTE_MAP

def main():
    store = get_vector_store()
    print(f"Reference collection '{store.collection_name}' count: {store.collection.count()}")
    print(f"Statutes collection '{store.statutes_collection_name}' count: {store.statutes_collection.count()}")

    # Group ingested provisions by Act
    all_statutes = store.statutes_collection.get()
    act_counts = Counter()
    act_ids = {}
    for meta in all_statutes["metadatas"]:
        act = meta["act"]
        pid = meta["id"]
        act_counts[act] += 1
        act_ids.setdefault(act, []).append(pid)

    print("\n=== Provisions Ingested Per Act ===")
    for act, count in act_counts.items():
        print(f"- {act}: {count} provisions -> {act_ids[act]}")

    sample_clauses = [
        {
            "clause_id": "Clause 4. Non-Compete and Restraint of Trade (employment_agreement.pdf)",
            "clause_type": "non_compete",
            "original_text": (
                "Upon termination or expiration of employment for any reason, the Employee shall be "
                "perpetually restrained and prohibited from engaging in, working for, advising, or "
                "investing in any business or profession in the software, technology, or consulting "
                "sector anywhere in the world for a period of five (5) years."
            )
        },
        {
            "clause_id": "Clause 3. Indemnity (employment_agreement.pdf)",
            "clause_type": "indemnity",
            "original_text": (
                "The Employee agrees to unconditionally indemnify, defend, and hold harmless the Company, "
                "its directors, officers, and affiliates from and against any and all losses, indirect "
                "or consequential damages, lost profits, liabilities, and legal expenses arising out of "
                "or related to the Employee's employment or termination thereof, regardless of whether "
                "such loss was caused by the Company's own negligence or fault."
            )
        },
        {
            "clause_id": "Clause 5. Dispute Resolution & Penalty (employment_agreement.pdf / rental_agreement.pdf)",
            "clause_type": "dispute_resolution",
            "original_text": (
                "In the event of any dispute arising out of this Agreement, the Company shall have the "
                "sole and exclusive right to unilaterally appoint a single arbitrator of its choice. "
                "The seat of arbitration shall be London, UK, and the Employee waives all rights to "
                "approach any civil court or tribunal in India."
            )
        },
        {
            "clause_id": "Clause 3. Late Payment Penalty & Liquidated Damages (rental_agreement.pdf)",
            "clause_type": "penalty",
            "original_text": (
                "If the Tenant delays rent payment by more than two (2) days beyond the due date, "
                "an immediate punitive penalty of Rs. 5,000 per day of delay shall be levied, in "
                "addition to immediate forfeiture of 100% of the Rs. 2,50,000 security deposit as "
                "liquidated damages."
            )
        }
    ]

    print("\n=== Sample Statutory Retrievals (top_k=3 + mapped) ===")
    for sample in sample_clauses:
        retrieved = retrieve_statutes_for_clause(sample, top_k=3)
        print(f"\nClause: {sample['clause_id']} [type={sample['clause_type']}]")
        print(f"Text: {sample['original_text']}")
        print(f"Mapped IDs for '{sample['clause_type']}': {CLAUSE_TYPE_STATUTE_MAP.get(sample['clause_type'], [])}")
        print(f"Retrieved {len(retrieved)} provisions:")
        for r in retrieved:
            dist_str = f"{r.distance:.4f}" if r.distance is not None else "N/A (mapped)"
            print(f"  - [{r.id}] {r.act} | {r.section}: {r.title} (source={r.retrieval_source}, distance={dist_str})")

if __name__ == "__main__":
    main()
