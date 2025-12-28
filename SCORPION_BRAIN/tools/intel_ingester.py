"""
SCORPION_BRAIN Intel Ingester
=============================
Feed harvested data into ChromaDB for RAG.

Features:
- Document chunking
- Embedding generation
- ChromaDB storage
- Metadata indexing
- Search capabilities
"""

import hashlib
import json
import re
from typing import Dict, List, Any, Optional, Generator
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Import from our algorithms module
try:
    from ..algorithms.universal import generate_embeddings, get_vector_store
except ImportError:
    # Fallback for direct execution
    def generate_embeddings(task, context=None):
        """Fallback embedding generator."""
        context = context or {}
        text = context.get("text", task)
        # Simple hash-based embedding
        import hashlib
        text_hash = hashlib.sha256(text.encode()).hexdigest()
        vector = []
        for i in range(384):
            seed = int(text_hash[(i * 2) % 64:(i * 2 + 2) % 64 + 2], 16)
            value = (seed / 255.0) * 2 - 1
            vector.append(value)
        return {"vector": vector}

    def get_vector_store():
        return None


@dataclass
class Document:
    """A document to be ingested."""
    id: str
    content: str
    metadata: Dict = field(default_factory=dict)
    source: str = ""
    doc_type: str = "text"


@dataclass
class Chunk:
    """A chunk of a document."""
    id: str
    doc_id: str
    content: str
    index: int
    metadata: Dict = field(default_factory=dict)


@dataclass
class IngestResult:
    """Result from ingestion."""
    documents_processed: int
    chunks_created: int
    embeddings_generated: int
    errors: List[str]
    duration: float


class IntelIngester:
    """
    Ingest harvested data into ChromaDB.

    Usage:
        ingester = IntelIngester()
        ingester.ingest_document(doc)
        results = ingester.search("query")
    """

    def __init__(
        self,
        collection_name: str = "scorpion_intel",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        data_dir: str = "/tmp/scorpion_intel"
    ):
        self.collection_name = collection_name
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)

        # Try to use ChromaDB
        self.db = None
        self.collection = None
        self._init_chromadb()

        # Fallback: simple file-based storage
        self.documents: Dict[str, Document] = {}
        self.chunks: Dict[str, Chunk] = {}
        self.embeddings: Dict[str, List[float]] = {}

    def _init_chromadb(self):
        """Initialize ChromaDB if available."""
        try:
            import chromadb
            from chromadb.config import Settings

            self.db = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=str(self.data_dir / "chromadb"),
                anonymized_telemetry=False
            ))

            self.collection = self.db.get_or_create_collection(
                name=self.collection_name,
                metadata={"hnsw:space": "cosine"}
            )

            logger.info(f"ChromaDB initialized: {self.collection_name}")

        except ImportError:
            logger.warning("ChromaDB not available, using fallback storage")
            self.db = None

        except Exception as e:
            logger.error(f"ChromaDB init failed: {e}")
            self.db = None

    def chunk_text(self, text: str, doc_id: str) -> Generator[Chunk, None, None]:
        """
        Split text into overlapping chunks.

        Args:
            text: Text to chunk
            doc_id: Document ID

        Yields:
            Chunk objects
        """
        # Clean text
        text = re.sub(r'\s+', ' ', text).strip()

        if len(text) <= self.chunk_size:
            yield Chunk(
                id=f"{doc_id}_0",
                doc_id=doc_id,
                content=text,
                index=0
            )
            return

        # Split into sentences for better chunks
        sentences = re.split(r'(?<=[.!?])\s+', text)

        current_chunk = ""
        chunk_index = 0

        for sentence in sentences:
            if len(current_chunk) + len(sentence) <= self.chunk_size:
                current_chunk += " " + sentence if current_chunk else sentence
            else:
                if current_chunk:
                    yield Chunk(
                        id=f"{doc_id}_{chunk_index}",
                        doc_id=doc_id,
                        content=current_chunk.strip(),
                        index=chunk_index
                    )
                    chunk_index += 1

                    # Keep overlap
                    overlap_text = current_chunk[-self.chunk_overlap:] if len(current_chunk) > self.chunk_overlap else ""
                    current_chunk = overlap_text + " " + sentence
                else:
                    current_chunk = sentence

        # Emit last chunk
        if current_chunk.strip():
            yield Chunk(
                id=f"{doc_id}_{chunk_index}",
                doc_id=doc_id,
                content=current_chunk.strip(),
                index=chunk_index
            )

    def ingest_document(self, document: Document) -> bool:
        """
        Ingest a single document.

        Args:
            document: Document to ingest

        Returns:
            True if successful
        """
        try:
            # Store document
            self.documents[document.id] = document

            # Chunk the content
            chunks = list(self.chunk_text(document.content, document.id))

            for chunk in chunks:
                # Add document metadata to chunk
                chunk.metadata = {
                    **document.metadata,
                    "doc_id": document.id,
                    "source": document.source,
                    "doc_type": document.doc_type,
                    "chunk_index": chunk.index
                }

                # Generate embedding
                result = generate_embeddings("", {"text": chunk.content})
                embedding = result.get("vector", [])

                # Store in ChromaDB or fallback
                if self.collection is not None:
                    self.collection.add(
                        ids=[chunk.id],
                        embeddings=[embedding],
                        documents=[chunk.content],
                        metadatas=[chunk.metadata]
                    )
                else:
                    self.chunks[chunk.id] = chunk
                    self.embeddings[chunk.id] = embedding

            return True

        except Exception as e:
            logger.error(f"Ingest failed: {e}")
            return False

    def ingest_batch(self, documents: List[Document]) -> IngestResult:
        """
        Ingest multiple documents.

        Args:
            documents: List of documents

        Returns:
            IngestResult with statistics
        """
        start_time = datetime.now()
        errors = []
        chunks_created = 0
        embeddings_generated = 0

        for doc in documents:
            try:
                # Count chunks
                chunks = list(self.chunk_text(doc.content, doc.id))
                chunks_created += len(chunks)
                embeddings_generated += len(chunks)

                # Ingest
                success = self.ingest_document(doc)
                if not success:
                    errors.append(f"Failed to ingest: {doc.id}")

            except Exception as e:
                errors.append(f"Error with {doc.id}: {str(e)}")

        duration = (datetime.now() - start_time).total_seconds()

        return IngestResult(
            documents_processed=len(documents),
            chunks_created=chunks_created,
            embeddings_generated=embeddings_generated,
            errors=errors,
            duration=duration
        )

    def search(
        self,
        query: str,
        top_k: int = 5,
        filters: Dict = None
    ) -> List[Dict]:
        """
        Search for relevant content.

        Args:
            query: Search query
            top_k: Number of results
            filters: Metadata filters

        Returns:
            List of search results
        """
        try:
            # Generate query embedding
            result = generate_embeddings("", {"text": query})
            query_embedding = result.get("vector", [])

            if self.collection is not None:
                # Search ChromaDB
                results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where=filters
                )

                search_results = []
                for i, doc_id in enumerate(results["ids"][0]):
                    search_results.append({
                        "id": doc_id,
                        "content": results["documents"][0][i] if results["documents"] else "",
                        "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                        "distance": results["distances"][0][i] if results.get("distances") else 0
                    })

                return search_results

            else:
                # Fallback search
                return self._fallback_search(query_embedding, top_k)

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def _fallback_search(self, query_embedding: List[float], top_k: int) -> List[Dict]:
        """Fallback search using simple vector similarity."""
        results = []

        for chunk_id, embedding in self.embeddings.items():
            # Calculate cosine similarity
            similarity = self._cosine_similarity(query_embedding, embedding)
            chunk = self.chunks.get(chunk_id)

            if chunk:
                results.append({
                    "id": chunk_id,
                    "content": chunk.content,
                    "metadata": chunk.metadata,
                    "score": similarity
                })

        # Sort by similarity
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:top_k]

    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Calculate cosine similarity."""
        if len(vec_a) != len(vec_b):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        mag_a = sum(a * a for a in vec_a) ** 0.5
        mag_b = sum(b * b for b in vec_b) ** 0.5

        if mag_a == 0 or mag_b == 0:
            return 0.0

        return dot_product / (mag_a * mag_b)

    def delete_document(self, doc_id: str) -> bool:
        """
        Delete a document and its chunks.

        Args:
            doc_id: Document ID

        Returns:
            True if successful
        """
        try:
            if self.collection is not None:
                # Get all chunks for this document
                results = self.collection.get(
                    where={"doc_id": doc_id}
                )
                if results["ids"]:
                    self.collection.delete(ids=results["ids"])

            # Remove from local storage
            if doc_id in self.documents:
                del self.documents[doc_id]

            # Remove related chunks
            chunks_to_delete = [
                cid for cid, chunk in self.chunks.items()
                if chunk.doc_id == doc_id
            ]
            for cid in chunks_to_delete:
                del self.chunks[cid]
                if cid in self.embeddings:
                    del self.embeddings[cid]

            return True

        except Exception as e:
            logger.error(f"Delete failed: {e}")
            return False

    def get_stats(self) -> Dict:
        """Get ingestion statistics."""
        if self.collection is not None:
            count = self.collection.count()
        else:
            count = len(self.chunks)

        return {
            "collection": self.collection_name,
            "documents": len(self.documents),
            "chunks": count,
            "chunk_size": self.chunk_size,
            "using_chromadb": self.collection is not None
        }

    def save_to_disk(self):
        """Save fallback storage to disk."""
        data = {
            "documents": {
                doc_id: {
                    "id": doc.id,
                    "content": doc.content[:1000],  # Truncate for storage
                    "metadata": doc.metadata,
                    "source": doc.source,
                    "doc_type": doc.doc_type
                }
                for doc_id, doc in self.documents.items()
            },
            "chunks": {
                chunk_id: {
                    "id": chunk.id,
                    "doc_id": chunk.doc_id,
                    "content": chunk.content,
                    "index": chunk.index,
                    "metadata": chunk.metadata
                }
                for chunk_id, chunk in self.chunks.items()
            }
        }

        with open(self.data_dir / "intel_store.json", "w") as f:
            json.dump(data, f, indent=2)

    def load_from_disk(self):
        """Load fallback storage from disk."""
        store_path = self.data_dir / "intel_store.json"
        if not store_path.exists():
            return

        with open(store_path, "r") as f:
            data = json.load(f)

        for doc_id, doc_data in data.get("documents", {}).items():
            self.documents[doc_id] = Document(**doc_data)

        for chunk_id, chunk_data in data.get("chunks", {}).items():
            self.chunks[chunk_id] = Chunk(**chunk_data)


def ingest_documents(
    documents: List[Dict],
    collection: str = "scorpion_intel"
) -> IngestResult:
    """
    Quick function to ingest documents.

    Args:
        documents: List of document dicts with 'id', 'content', 'metadata'
        collection: Collection name

    Returns:
        IngestResult
    """
    ingester = IntelIngester(collection_name=collection)

    docs = [
        Document(
            id=doc.get("id", hashlib.md5(doc["content"].encode()).hexdigest()),
            content=doc["content"],
            metadata=doc.get("metadata", {}),
            source=doc.get("source", ""),
            doc_type=doc.get("type", "text")
        )
        for doc in documents
    ]

    return ingester.ingest_batch(docs)


if __name__ == "__main__":
    # Demo
    ingester = IntelIngester()

    print("=== Ingesting Documents ===")

    # Create test documents
    docs = [
        Document(
            id="doc1",
            content="Python is a programming language that is widely used for web development, data science, and automation. It has a simple syntax and extensive libraries.",
            metadata={"topic": "programming"},
            source="test",
            doc_type="text"
        ),
        Document(
            id="doc2",
            content="Machine learning is a subset of artificial intelligence that enables computers to learn from data. Deep learning uses neural networks for complex tasks.",
            metadata={"topic": "ai"},
            source="test",
            doc_type="text"
        ),
    ]

    result = ingester.ingest_batch(docs)
    print(f"Documents: {result.documents_processed}")
    print(f"Chunks: {result.chunks_created}")
    print(f"Duration: {result.duration:.2f}s")

    print("\n=== Search ===")
    results = ingester.search("programming languages")
    for r in results:
        print(f"  [{r.get('score', r.get('distance', 0)):.3f}] {r['content'][:50]}...")

    print("\n=== Stats ===")
    stats = ingester.get_stats()
    print(f"Documents: {stats['documents']}")
    print(f"Chunks: {stats['chunks']}")
    print(f"Using ChromaDB: {stats['using_chromadb']}")
