"""
OmniSynth - Embedding Service
Sentence Transformers + FAISS vector database management
"""
import os
import json
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from app.core.config import settings
from loguru import logger
import asyncio

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.warning("FAISS not available - using mock search")


class EmbeddingService:
    def __init__(self):
        self.model = None
        self.index = None
        self.metadata_store: Dict[str, Any] = {}
        self.index_path = settings.FAISS_INDEX_PATH
        self.dimension = settings.FAISS_DIMENSION
        self._initialized = False
        self._doc_counter = 0

    async def initialize(self):
        """Initialize the embedding model and FAISS index."""
        if self._initialized:
            return
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {settings.HF_EMBEDDING_MODEL}")
            loop = asyncio.get_event_loop()
            self.model = await loop.run_in_executor(
                None, lambda: SentenceTransformer(settings.HF_EMBEDDING_MODEL)
            )
            self.dimension = self.model.get_sentence_embedding_dimension()
            await self._load_or_create_index()
            self._initialized = True
            logger.info(f"Embedding service initialized. Dimension: {self.dimension}")
        except Exception as e:
            logger.error(f"Failed to initialize embedding service: {e}")
            self.dimension = 384
            if FAISS_AVAILABLE:
                await self._load_or_create_index()
            self._initialized = True

    async def _load_or_create_index(self):
        """Load existing FAISS index or create a new one."""
        if not FAISS_AVAILABLE:
            return
        os.makedirs(self.index_path, exist_ok=True)
        index_file = os.path.join(self.index_path, "omnisynth.index")
        metadata_file = os.path.join(self.index_path, "metadata.json")

        if os.path.exists(index_file):
            self.index = faiss.read_index(index_file)
            if os.path.exists(metadata_file):
                with open(metadata_file, "r") as f:
                    self.metadata_store = json.load(f)
            logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
        else:
            base_index = faiss.IndexFlatIP(self.dimension)
            self.index = faiss.IndexIDMap(base_index)
            logger.info("Created new FAISS index")

    async def save_index(self):
        """Persist FAISS index to disk."""
        if not FAISS_AVAILABLE or self.index is None:
            return
        try:
            os.makedirs(self.index_path, exist_ok=True)
            index_file = os.path.join(self.index_path, "omnisynth.index")
            metadata_file = os.path.join(self.index_path, "metadata.json")
            faiss.write_index(self.index, index_file)
            with open(metadata_file, "w") as f:
                json.dump(self.metadata_store, f, indent=2)
            logger.debug("FAISS index saved to disk")
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")

    def _encode(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for a list of texts."""
        if not self.model:
            return np.random.randn(len(texts), self.dimension).astype(np.float32)
        embeddings = self.model.encode(texts, normalize_embeddings=True, show_progress_bar=False)
        return embeddings.astype(np.float32)

    def chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Public method: Split text into overlapping chunks."""
        return self._chunk_text(text, chunk_size, overlap)

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks."""
        words = text.split()
        if len(words) <= chunk_size:
            return [text]
        chunks = []
        for i in range(0, len(words), chunk_size - overlap):
            chunk = " ".join(words[i:i + chunk_size])
            chunks.append(chunk)
        return chunks or [text[:1000]]

    async def add_document(self, doc_id: str, text: str, metadata: Dict[str, Any] = None) -> int:
        """Add a single document to the vector store."""
        await self.initialize()
        try:
            chunks = self._chunk_text(text)
            embeddings = self._encode(chunks)

            if FAISS_AVAILABLE and self.index is not None:
                start_id = self._doc_counter
                ids = np.array([start_id + i for i in range(len(chunks))], dtype=np.int64)
                self.index.add_with_ids(embeddings, ids)

                for i, (chunk, emb_id) in enumerate(zip(chunks, ids)):
                    self.metadata_store[str(emb_id)] = {
                        "doc_id": doc_id,
                        "chunk_index": i,
                        "content": chunk[:500],
                        "metadata": metadata or {},
                    }
                self._doc_counter += len(chunks)
                logger.info(f"Added {len(chunks)} chunks for document {doc_id}")
                return len(chunks)
        except Exception as e:
            logger.error(f"Failed to add document to index: {e}")
        return 0

    async def add_documents(
        self,
        texts: List[str],
        metadatas: List[Dict[str, Any]] = None,
    ) -> List[int]:
        """Add multiple documents/chunks to the vector store. Returns list of IDs."""
        await self.initialize()
        if not texts:
            return []

        try:
            embeddings = self._encode(texts)

            if FAISS_AVAILABLE and self.index is not None:
                start_id = self._doc_counter
                ids = np.array([start_id + i for i in range(len(texts))], dtype=np.int64)
                self.index.add_with_ids(embeddings, ids)

                for i, (text, emb_id) in enumerate(zip(texts, ids)):
                    meta = metadatas[i] if metadatas and i < len(metadatas) else {}
                    self.metadata_store[str(emb_id)] = {
                        "content": text[:500],
                        "metadata": meta,
                    }
                self._doc_counter += len(texts)
                return [int(i) for i in ids]
            else:
                # No FAISS - return mock IDs
                return list(range(len(texts)))
        except Exception as e:
            logger.error(f"Failed to add documents to index: {e}")
            return []

    async def search(self, query: str, top_k: int = 5, threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        await self.initialize()
        if not FAISS_AVAILABLE or self.index is None or self.index.ntotal == 0:
            return self._mock_search_results(query, top_k)

        try:
            query_embedding = self._encode([query])
            scores, indices = self.index.search(query_embedding, min(top_k, self.index.ntotal))
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if idx == -1:
                    continue
                if score < threshold:
                    continue
                meta = self.metadata_store.get(str(idx), {})
                results.append({
                    "doc_id": meta.get("doc_id", ""),
                    "content": meta.get("content", ""),
                    "score": float(score),
                    "metadata": meta.get("metadata", {}),
                })
            return results
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def _mock_search_results(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Return mock results when no documents are indexed."""
        return []

    async def delete_document(self, doc_id: str):
        """Remove document from index (mark as deleted)."""
        to_remove = [k for k, v in self.metadata_store.items() if v.get("doc_id") == doc_id]
        for key in to_remove:
            del self.metadata_store[key]
        logger.info(f"Removed {len(to_remove)} chunks for document {doc_id}")

    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        return {
            "total_vectors": self.index.ntotal if (FAISS_AVAILABLE and self.index) else 0,
            "total_documents": len(set(v.get("doc_id", "") for v in self.metadata_store.values())),
            "dimension": self.dimension,
            "model": settings.HF_EMBEDDING_MODEL,
            "faiss_available": FAISS_AVAILABLE,
        }


embedding_service = EmbeddingService()
