import unittest
import sys
from pathlib import Path
from collections import Counter

# Ensure backend root is on sys.path
backend_dir = Path(__file__).resolve().parent.parent
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))

from app.vector_store import get_vector_store, retrieve_statutes_for_clause, CLAUSE_TYPE_STATUTE_MAP


class TestStatuteRAG(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.store = get_vector_store()

    def test_chroma_collection_counts(self):
        """Verify collection counts in ChromaDB."""
        ref_count = self.store.collection.count()
        statutes_count = self.store.statutes_collection.count()
        self.assertGreaterEqual(ref_count, 112, f"Expected at least 112 reference clauses, got {ref_count}")
        self.assertEqual(statutes_count, 24, f"Expected exactly 24 verified statutes, got {statutes_count}")

    def test_provisions_ingested_per_act(self):
        """Verify all 4 verified acts are ingested with correct provision counts."""
        all_statutes = self.store.statutes_collection.get()
        act_counts = Counter()
        for meta in all_statutes["metadatas"]:
            act_counts[meta["act"]] += 1

        self.assertEqual(act_counts["Arbitration and Conciliation Act, 1996"], 6)
        self.assertEqual(act_counts["Constitution of India"], 5)
        self.assertEqual(act_counts["Consumer Protection Act, 2019"], 1)
        self.assertEqual(act_counts["Indian Contract Act, 1872"], 12)

    def test_sample_statutory_retrievals(self):
        """Verify statutory retrieval for standard clause types."""
        # 1. Non-compete
        nc_text = "Upon termination, the Employee shall not work for any competitor for 5 years."
        retrieved_nc = retrieve_statutes_for_clause(nc_text, clause_type="non_compete", top_k=3)
        retrieved_nc_ids = [p.id for p in retrieved_nc]
        self.assertIn("ICA-1872-s27", retrieved_nc_ids)

        # 2. Indemnity
        ind_text = "The Employee agrees to unconditionally indemnify and hold harmless the Company."
        retrieved_ind = retrieve_statutes_for_clause(ind_text, clause_type="indemnity", top_k=3)
        retrieved_ind_ids = [p.id for p in retrieved_ind]
        self.assertTrue(any(pid in retrieved_ind_ids for pid in ["ICA-1872-s124", "ICA-1872-s125"]))

        # 3. Dispute resolution
        dr_text = "The Company shall have the sole right to appoint an arbitrator in London."
        retrieved_dr = retrieve_statutes_for_clause(dr_text, clause_type="dispute_resolution", top_k=3)
        retrieved_dr_ids = [p.id for p in retrieved_dr]
        self.assertIn("ICA-1872-s28", retrieved_dr_ids)
        self.assertTrue(any(pid.startswith("ACA-") for pid in retrieved_dr_ids))

        # 4. Penalty
        pen_text = "Late payment shall incur a punitive penalty of Rs 5000 per day."
        retrieved_pen = retrieve_statutes_for_clause(pen_text, clause_type="penalty", top_k=3)
        retrieved_pen_ids = [p.id for p in retrieved_pen]
        self.assertIn("ICA-1872-s74", retrieved_pen_ids)


if __name__ == "__main__":
    unittest.main()
