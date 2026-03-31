"""
ChromaDB vector store setup and querying.
Stores CV best-practice examples and bullet templates.
"""
import logging
from typing import List, Optional
import chromadb
from chromadb.config import Settings

logger = logging.getLogger(__name__)

COLLECTION_NAMES = {
    "bullets": "cv_bullet_examples",        # Best-practice achievement bullets
    "summaries": "cv_summary_examples",     # Professional summary examples
    "templates": "cv_template_metadata",    # Template descriptions
}


def get_chroma_client(persist_dir: str) -> chromadb.ClientAPI:
    """Create a persistent ChromaDB client."""
    client = chromadb.PersistentClient(
        path=persist_dir,
        settings=Settings(anonymized_telemetry=False),
    )
    logger.info(f"ChromaDB client ready at {persist_dir}")
    return client


def get_or_create_collection(client: chromadb.ClientAPI, name: str):
    """Get or create a ChromaDB collection."""
    return client.get_or_create_collection(
        name=name,
        metadata={"hnsw:space": "cosine"},
    )


class CVVectorStore:
    """Wraps ChromaDB collections for CV knowledge retrieval."""

    def __init__(self, persist_dir: str):
        self.client = get_chroma_client(persist_dir)
        self.bullets_col = get_or_create_collection(self.client, COLLECTION_NAMES["bullets"])
        self.summaries_col = get_or_create_collection(self.client, COLLECTION_NAMES["summaries"])
        self.templates_col = get_or_create_collection(self.client, COLLECTION_NAMES["templates"])
        logger.info("CVVectorStore initialised")

    def query_bullets(
        self,
        query: str,
        role: Optional[str] = None,
        industry: Optional[str] = None,
        n_results: int = 5,
    ) -> List[str]:
        """Retrieve best-practice bullet points for a given role/context."""
        where = {}
        if role:
            where["role"] = {"$contains": role.lower()}

        try:
            results = self.bullets_col.query(
                query_texts=[query],
                n_results=n_results,
                where=where if where else None,
            )
            docs = results.get("documents", [[]])[0]
            logger.debug(f"Bullet query returned {len(docs)} results")
            return docs
        except Exception as e:
            logger.warning(f"Bullet query failed: {e}")
            return []

    def query_summaries(self, query: str, n_results: int = 3) -> List[str]:
        """Retrieve professional summary examples."""
        try:
            results = self.summaries_col.query(
                query_texts=[query],
                n_results=n_results,
            )
            return results.get("documents", [[]])[0]
        except Exception as e:
            logger.warning(f"Summary query failed: {e}")
            return []

    def collection_stats(self) -> dict:
        return {
            "bullets": self.bullets_col.count(),
            "summaries": self.summaries_col.count(),
            "templates": self.templates_col.count(),
        }
