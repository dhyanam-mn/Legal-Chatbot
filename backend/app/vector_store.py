import json
import logging
from typing import List, Dict, Any, Optional, Union
import chromadb
from sentence_transformers import SentenceTransformer
from .config import DATA_DIR, CHROMA_PERSIST_DIR, EMBEDDING_MODEL_NAME
from .schemas import GroundingExample, StatutoryProvision, FlaggedClause

logger = logging.getLogger(__name__)

# Deterministic clause_type -> statute ID mapping to bias statutory retrieval
CLAUSE_TYPE_STATUTE_MAP: Dict[str, List[str]] = {
    "non_compete": ["ICA-1872-s27", "COI-art19"],
    "penalty": ["ICA-1872-s74", "ICA-1872-s73", "CPA-2019-s2-46"],
    "indemnity": ["ICA-1872-s124", "ICA-1872-s125"],
    "dispute_resolution": ["ICA-1872-s28", "ACA-1996-s7", "ACA-1996-s11", "ACA-1996-s12", "ACA-1996-s18", "ACA-1996-s20"],
    "arbitration": ["ICA-1872-s28", "ACA-1996-s7", "ACA-1996-s11", "ACA-1996-s12", "ACA-1996-s18", "ACA-1996-s20"],
    "termination": ["ICA-1872-s39", "ICA-1872-s75", "ICA-1872-s23", "CPA-2019-s2-46"],
    # Loan agreement clause types
    "penal_interest": ["ICA-1872-s74", "CPA-2019-s2-46"],
    "acceleration": [],
    "foreclosure_charges": ["CPA-2019-s2-46"],
    "unilateral_interest_change": ["CPA-2019-s2-46"],
    "guarantor_liability": [],
    "set_off_lien": [],
    # Employment extra clause types
    "service_bond": ["ICA-1872-s74", "ICA-1872-s27"],
    "ip_assignment": [],
    "notice_period_garden_leave": ["ICA-1872-s27", "ICA-1872-s74"],
}


class BGEEmbeddingFunction:
    """Embedding function wrapper using sentence-transformers BAAI/bge-small-en-v1.5"""
    def __init__(self, model_name: str = EMBEDDING_MODEL_NAME):
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)

    def encode_documents(self, texts: List[str]) -> List[List[float]]:
        embeddings = self.model.encode(texts, normalize_embeddings=True)
        return embeddings.tolist()

    def encode_query(self, query: str) -> List[float]:
        embedding = self.model.encode([f"Represent this sentence for searching relevant passages: {query}"], normalize_embeddings=True)
        return embedding[0].tolist()

class ReferenceVectorStore:
    def __init__(self):
        self.embedder = BGEEmbeddingFunction()
        self.chroma_client = chromadb.PersistentClient(path=str(CHROMA_PERSIST_DIR))
        self.collection_name = "legal_reference_clauses"
        self.statutes_collection_name = "legal_statutes"
        self.statutes_by_id: Dict[str, Dict[str, Any]] = {}
        self.standard_clauses_by_type: Dict[str, List[str]] = {}
        self._load_standard_clauses_dict()
        self._init_collection()
        self._init_statutes_collection()

    def _load_standard_clauses_dict(self):
        """Load standard_examples from reference_clauses.json for 'How this is typically written'."""
        json_file = DATA_DIR / "reference_clauses.json"
        if not json_file.exists():
            return
        try:
            with open(json_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            for ctype, info in data.items():
                std_list = info.get("standard_examples", [])
                if isinstance(std_list, list):
                    self.standard_clauses_by_type[ctype] = std_list
            if "dispute_resolution" in self.standard_clauses_by_type:
                self.standard_clauses_by_type["arbitration"] = self.standard_clauses_by_type["dispute_resolution"]
        except Exception as e:
            logger.error(f"Error loading standard clauses from {json_file}: {e}")

    def get_standard_alternatives(self, clause_type: str) -> List[str]:
        """Return descriptive 'standard' phrasing examples from reference_clauses.json for a clause type."""
        return list(self.standard_clauses_by_type.get(clause_type, []))

    def _init_collection(self):
        """Create collection and ingest reference JSON dataset if empty."""
        try:
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            
            if self.collection.count() > 0:
                logger.info(f"ChromaDB collection '{self.collection_name}' contains {self.collection.count()} documents.")
                return

            self._load_reference_data()
        except Exception as e:
            logger.error(f"Error initializing ChromaDB collection: {e}")
            raise e


    def _load_reference_data(self):
        """Load reference_clauses.json and insert into ChromaDB."""
        json_file = DATA_DIR / "reference_clauses.json"
        if not json_file.exists():
            logger.error(f"Reference JSON file not found at {json_file}")
            return

        with open(json_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        documents = []
        metadatas = []
        ids = []

        doc_idx = 1
        for clause_type, info in data.items():
            title = info.get("title", clause_type)
            
            for example in info.get("standard_examples", []):
                documents.append(example)
                metadatas.append({
                    "clause_type": clause_type,
                    "category": "standard",
                    "title": title
                })
                ids.append(f"ref_{doc_idx}")
                doc_idx += 1

            for example in info.get("one_sided_examples", []):
                documents.append(example)
                metadatas.append({
                    "clause_type": clause_type,
                    "category": "one_sided",
                    "title": title
                })
                ids.append(f"ref_{doc_idx}")
                doc_idx += 1

        if documents:
            logger.info(f"Ingesting {len(documents)} reference clause examples into ChromaDB...")
            embeddings = self.embedder.encode_documents(documents)
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            logger.info("ChromaDB reference set ingestion complete.")

    def _init_statutes_collection(self):
        """Create separate 'legal_statutes' Chroma collection and ingest provisions (1 chunk = 1 provision)."""
        try:
            self.statutes_collection = self.chroma_client.get_or_create_collection(
                name=self.statutes_collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            self._load_statutes_data()
        except Exception as e:
            logger.error(f"Error initializing ChromaDB statutes collection: {e}")
            raise e

    def _load_statutes_data(self):
        """Load all data/statutes/*.json files and upsert into 'legal_statutes' collection."""
        statutes_dir = DATA_DIR / "statutes"
        if not statutes_dir.exists():
            alt_dir = DATA_DIR.parent.parent / "data" / "statutes"
            if alt_dir.exists():
                statutes_dir = alt_dir
            else:
                logger.warning(f"Statutes directory not found at {statutes_dir}")
                return

        provisions: List[Dict[str, Any]] = []
        for json_file in sorted(statutes_dir.glob("*.json")):
            with open(json_file, "r", encoding="utf-8") as f:
                items = json.load(f)
                if isinstance(items, list):
                    for item in items:
                        if isinstance(item, dict) and "id" in item and "text" in item:
                            provisions.append(item)
                            self.statutes_by_id[item["id"]] = item

        if not provisions:
            logger.warning("No statutory provisions found to ingest.")
            return

        existing_ids = set(self.statutes_collection.get()["ids"] if self.statutes_collection.count() > 0 else [])
        valid_ids = {p["id"] for p in provisions}
        stale_ids = list(existing_ids - valid_ids)
        if stale_ids:
            logger.info(f"Removing {len(stale_ids)} unverified/stale provisions from '{self.statutes_collection_name}': {stale_ids}")
            self.statutes_collection.delete(ids=stale_ids)

        if self.statutes_collection.count() == len(provisions) and not stale_ids:
            logger.info(
                f"ChromaDB collection '{self.statutes_collection_name}' already contains {len(provisions)} statutory provisions."
            )
            return

        documents = []
        metadatas = []
        ids = []

        for prov in provisions:
            # 1 chunk = 1 full statutory provision (never split by token window)
            doc_text = f"{prov.get('act', '')} - {prov.get('section', '')} ({prov.get('title', '')}): {prov['text']}"
            documents.append(doc_text)
            metadatas.append({
                "id": prov["id"],
                "act": prov.get("act", ""),
                "section": prov.get("section", ""),
                "title": prov.get("title", ""),
                "raw_text": prov["text"],
                "source_url": prov.get("source_url", "")
            })
            ids.append(prov["id"])

        logger.info(f"Ingesting {len(documents)} statutory provisions into ChromaDB collection '{self.statutes_collection_name}'...")
        embeddings = self.embedder.encode_documents(documents)
        self.statutes_collection.upsert(
            documents=documents,
            embeddings=embeddings,
            metadatas=metadatas,
            ids=ids
        )
        logger.info(f"ChromaDB '{self.statutes_collection_name}' ingestion complete ({self.statutes_collection.count()} provisions).")


    def query_nearest_references(self, clause_text: str, top_k: int = 4) -> List[GroundingExample]:
        """Embed clause and retrieve nearest reference examples from ChromaDB."""
        if not clause_text or not clause_text.strip():
            return []

        query_embedding = self.embedder.encode_query(clause_text)
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=min(top_k, self.collection.count())
        )

        examples = []
        if results and results.get("documents") and len(results["documents"]) > 0:
            docs = results["documents"][0]
            metas = results["metadatas"][0]
            distances = results.get("distances", [[]])[0]

            for i in range(len(docs)):
                examples.append(GroundingExample(
                    category=metas[i].get("category", "unknown"),
                    clause_type=metas[i].get("clause_type", "unknown"),
                    text=docs[i],
                    distance=float(distances[i]) if i < len(distances) else 0.0
                ))

        return examples

    def retrieve_statutes_for_clause(
        self,
        clause: Union[FlaggedClause, Dict[str, Any], str],
        clause_type: Optional[str] = None,
        top_k: int = 3,
        max_distance: Optional[float] = 0.395,
        exclude_ids: Optional[List[str]] = None
    ) -> List[StatutoryProvision]:
        """
        Given a flagged clause (or clause text + clause_type), return top-k semantic matches
        from 'legal_statutes' using bge-small-en-v1.5 PLUS the mapped statutory provisions
        for that clause_type.
        """
        if isinstance(clause, FlaggedClause):
            clause_text = clause.original_text
            resolved_type = clause_type or clause.clause_type
        elif isinstance(clause, dict):
            clause_text = clause.get("original_text") or clause.get("text") or ""
            resolved_type = clause_type or clause.get("clause_type") or ""
        else:
            clause_text = str(clause)
            resolved_type = clause_type or ""

        if not clause_text or not clause_text.strip():
            return []

        total_statutes = self.statutes_collection.count()
        # If clause_type is explicitly mapped to empty list, no verified statutory provisions apply
        if resolved_type in CLAUSE_TYPE_STATUTE_MAP and len(CLAUSE_TYPE_STATUTE_MAP[resolved_type]) == 0:
            logger.info(
                f"Clause type '{resolved_type}' is explicitly mapped to 0 statutory provisions (no verified statute applies). "
                "Returning empty list."
            )
            return []

        excluded_set = set(exclude_ids or [])

        # 1. Semantic top-k retrieval from "legal_statutes" using bge-small-en-v1.5
        query_embedding = self.embedder.encode_query(clause_text)
        results = self.statutes_collection.query(
            query_embeddings=[query_embedding],
            n_results=min(max(top_k + len(excluded_set), top_k), total_statutes)
        )

        semantic_by_id: Dict[str, StatutoryProvision] = {}
        semantic_order: List[str] = []

        if results and results.get("metadatas") and len(results["metadatas"]) > 0:
            metas = results["metadatas"][0]
            distances = results.get("distances", [[]])[0]
            for i, meta in enumerate(metas):
                pid = meta.get("id", "")
                if pid in excluded_set:
                    continue
                dist = float(distances[i]) if i < len(distances) else None
                if max_distance is not None and dist is not None and dist > max_distance:
                    continue
                prov = StatutoryProvision(
                    id=pid,
                    act=meta.get("act", ""),
                    section=meta.get("section", ""),
                    title=meta.get("title", ""),
                    text=meta.get("raw_text", ""),
                    source_url=meta.get("source_url", ""),
                    distance=dist,
                    retrieval_source="semantic"
                )
                semantic_by_id[pid] = prov
                semantic_order.append(pid)
                if len(semantic_order) >= top_k:
                    break

        # 2. Bias/augment with deterministic clause_type -> statute mapping
        mapped_ids = [mid for mid in CLAUSE_TYPE_STATUTE_MAP.get(resolved_type, []) if mid not in excluded_set]
        combined: List[StatutoryProvision] = []
        seen_ids = set()

        # First include mapped provisions (marking "mapped+semantic" if also in semantic top-k)
        for mid in mapped_ids:
            if mid in seen_ids:
                continue
            if mid in semantic_by_id:
                prov = semantic_by_id[mid]
                prov.retrieval_source = "mapped+semantic"
                combined.append(prov)
                seen_ids.add(mid)
            elif mid in self.statutes_by_id:
                raw = self.statutes_by_id[mid]
                combined.append(StatutoryProvision(
                    id=raw["id"],
                    act=raw.get("act", ""),
                    section=raw.get("section", ""),
                    title=raw.get("title", ""),
                    text=raw.get("text", ""),
                    source_url=raw.get("source_url", ""),
                    distance=None,
                    retrieval_source="mapped"
                ))
                seen_ids.add(mid)

        # Then append any remaining semantic top-k provisions not already in mapped_ids
        for sid in semantic_order:
            if sid not in seen_ids:
                combined.append(semantic_by_id[sid])
                seen_ids.add(sid)

        return combined

_store_instance = None

def get_vector_store() -> ReferenceVectorStore:
    global _store_instance
    if _store_instance is None:
        _store_instance = ReferenceVectorStore()
    return _store_instance

def retrieve_statutes_for_clause(
    clause: Union[FlaggedClause, Dict[str, Any], str],
    clause_type: Optional[str] = None,
    top_k: int = 3,
    max_distance: Optional[float] = 0.395,
    exclude_ids: Optional[List[str]] = None
) -> List[StatutoryProvision]:
    """Convenience function to retrieve top-k + mapped statutory provisions for a flagged clause."""
    return get_vector_store().retrieve_statutes_for_clause(
        clause,
        clause_type=clause_type,
        top_k=top_k,
        max_distance=max_distance,
        exclude_ids=exclude_ids
    )

def get_standard_alternatives(clause_type: str) -> List[str]:
    """Convenience function to get standard phrasing examples from reference_clauses.json."""
    return get_vector_store().get_standard_alternatives(clause_type)


