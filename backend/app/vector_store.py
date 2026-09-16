import json
import logging
from typing import List, Dict, Any
import chromadb
from sentence_transformers import SentenceTransformer
from .config import DATA_DIR, CHROMA_PERSIST_DIR, EMBEDDING_MODEL_NAME
from .schemas import GroundingExample

logger = logging.getLogger(__name__)

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
        self._init_collection()

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

_store_instance = None

def get_vector_store() -> ReferenceVectorStore:
    global _store_instance
    if _store_instance is None:
        _store_instance = ReferenceVectorStore()
    return _store_instance
