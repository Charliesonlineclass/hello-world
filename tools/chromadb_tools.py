"""
SCORPION ChromaDB Tools
=======================

Tools for interacting with ChromaDB vector database.
Handles document storage, retrieval, and semantic search.

Author: SCORPION Commander
Version: 1.0.0 - TESTUDO Formation
"""

import os
import json
import logging
import hashlib
from typing import Dict, List, Optional, Any
from datetime import datetime
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SCORPION-CHROMADB")


class ChromaTools:
    """
    Tools for ChromaDB operations.

    Provides:
    - Connection management
    - Collection CRUD operations
    - Document storage and retrieval
    - Semantic search
    - Statistics and monitoring
    """

    def __init__(
        self,
        host: str = None,
        port: int = None,
        token: str = None
    ):
        self.host = host or os.getenv("CHROMADB_HOST", "localhost")
        self.port = port or int(os.getenv("CHROMADB_PORT", "8000"))
        self.token = token or os.getenv("CHROMADB_TOKEN", "")
        self.base_url = f"http://{self.host}:{self.port}"

        self.headers = {
            "Content-Type": "application/json"
        }
        if self.token:
            self.headers["Authorization"] = f"Bearer {self.token}"

        logger.info(f"ChromaTools initialized: {self.base_url}")

    # -------------------------------------------------------------------------
    # Connection
    # -------------------------------------------------------------------------

    def connect(self) -> bool:
        """Test connection to ChromaDB."""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/heartbeat",
                headers=self.headers,
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Connection failed: {e}")
            return False

    def get_version(self) -> Optional[str]:
        """Get ChromaDB version."""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/version",
                headers=self.headers,
                timeout=5
            )
            if response.status_code == 200:
                return response.text.strip('"')
        except Exception:
            pass
        return None

    # -------------------------------------------------------------------------
    # Collections
    # -------------------------------------------------------------------------

    def list_collections(self) -> List[Dict[str, Any]]:
        """List all collections."""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/collections",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"List collections failed: {e}")
        return []

    def create_collection(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Create a new collection."""
        try:
            payload = {
                "name": name,
                "metadata": metadata or {}
            }

            response = requests.post(
                f"{self.base_url}/api/v1/collections",
                headers=self.headers,
                json=payload,
                timeout=10
            )

            if response.status_code in [200, 201]:
                logger.info(f"Created collection: {name}")
                return response.json()
            else:
                logger.error(f"Create collection failed: {response.status_code}")

        except Exception as e:
            logger.error(f"Create collection failed: {e}")

        return None

    def get_collection(self, name: str) -> Optional[Dict[str, Any]]:
        """Get a collection by name."""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/collections/{name}",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Get collection failed: {e}")
        return None

    def delete_collection(self, name: str) -> bool:
        """Delete a collection."""
        try:
            response = requests.delete(
                f"{self.base_url}/api/v1/collections/{name}",
                headers=self.headers,
                timeout=10
            )
            if response.status_code in [200, 204]:
                logger.info(f"Deleted collection: {name}")
                return True
        except Exception as e:
            logger.error(f"Delete collection failed: {e}")
        return False

    def get_or_create_collection(
        self,
        name: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Dict[str, Any]]:
        """Get a collection or create if it doesn't exist."""
        collection = self.get_collection(name)
        if collection:
            return collection
        return self.create_collection(name, metadata)

    # -------------------------------------------------------------------------
    # Documents
    # -------------------------------------------------------------------------

    def add_documents(
        self,
        collection: str,
        documents: List[str],
        ids: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None,
        embeddings: Optional[List[List[float]]] = None
    ) -> bool:
        """Add documents to a collection."""
        try:
            # Generate IDs if not provided
            if ids is None:
                ids = [
                    hashlib.md5(f"{doc}{datetime.now().isoformat()}".encode()).hexdigest()[:16]
                    for doc in documents
                ]

            payload = {
                "ids": ids,
                "documents": documents
            }

            if metadatas:
                payload["metadatas"] = metadatas

            if embeddings:
                payload["embeddings"] = embeddings

            response = requests.post(
                f"{self.base_url}/api/v1/collections/{collection}/add",
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code in [200, 201]:
                logger.info(f"Added {len(documents)} documents to {collection}")
                return True
            else:
                logger.error(f"Add documents failed: {response.status_code}")

        except Exception as e:
            logger.error(f"Add documents failed: {e}")

        return False

    def get_documents(
        self,
        collection: str,
        ids: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0
    ) -> Dict[str, Any]:
        """Get documents from a collection."""
        try:
            payload = {
                "limit": limit,
                "offset": offset
            }

            if ids:
                payload["ids"] = ids

            response = requests.post(
                f"{self.base_url}/api/v1/collections/{collection}/get",
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()

        except Exception as e:
            logger.error(f"Get documents failed: {e}")

        return {"ids": [], "documents": [], "metadatas": []}

    def update_documents(
        self,
        collection: str,
        ids: List[str],
        documents: Optional[List[str]] = None,
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Update documents in a collection."""
        try:
            payload = {"ids": ids}

            if documents:
                payload["documents"] = documents

            if metadatas:
                payload["metadatas"] = metadatas

            response = requests.post(
                f"{self.base_url}/api/v1/collections/{collection}/update",
                headers=self.headers,
                json=payload,
                timeout=30
            )

            return response.status_code in [200, 201]

        except Exception as e:
            logger.error(f"Update documents failed: {e}")

        return False

    def delete_documents(
        self,
        collection: str,
        ids: List[str]
    ) -> bool:
        """Delete documents from a collection."""
        try:
            payload = {"ids": ids}

            response = requests.post(
                f"{self.base_url}/api/v1/collections/{collection}/delete",
                headers=self.headers,
                json=payload,
                timeout=30
            )

            return response.status_code in [200, 204]

        except Exception as e:
            logger.error(f"Delete documents failed: {e}")

        return False

    # -------------------------------------------------------------------------
    # Search
    # -------------------------------------------------------------------------

    def query(
        self,
        collection: str,
        query_text: str,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        include: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Query a collection for similar documents."""
        try:
            payload = {
                "query_texts": [query_text],
                "n_results": n_results
            }

            if where:
                payload["where"] = where

            if include:
                payload["include"] = include
            else:
                payload["include"] = ["documents", "metadatas", "distances"]

            response = requests.post(
                f"{self.base_url}/api/v1/collections/{collection}/query",
                headers=self.headers,
                json=payload,
                timeout=30
            )

            if response.status_code == 200:
                return response.json()

        except Exception as e:
            logger.error(f"Query failed: {e}")

        return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}

    def search(
        self,
        collection: str,
        query: str,
        n_results: int = 5
    ) -> List[Dict[str, Any]]:
        """Search and return formatted results."""
        result = self.query(collection, query, n_results)

        formatted = []
        if result.get("documents") and result["documents"][0]:
            for i, doc in enumerate(result["documents"][0]):
                item = {
                    "document": doc,
                    "id": result["ids"][0][i] if result.get("ids") else None,
                    "metadata": result["metadatas"][0][i] if result.get("metadatas") else {},
                    "distance": result["distances"][0][i] if result.get("distances") else None
                }
                formatted.append(item)

        return formatted

    # -------------------------------------------------------------------------
    # Statistics
    # -------------------------------------------------------------------------

    def get_stats(self) -> Dict[str, Any]:
        """Get ChromaDB statistics."""
        stats = {
            "connected": self.connect(),
            "version": self.get_version(),
            "collections": []
        }

        collections = self.list_collections()
        for coll in collections:
            coll_name = coll.get("name", "unknown")
            count = self.count(coll_name)
            stats["collections"].append({
                "name": coll_name,
                "count": count,
                "metadata": coll.get("metadata", {})
            })

        stats["total_documents"] = sum(c["count"] for c in stats["collections"])
        stats["total_collections"] = len(stats["collections"])

        return stats

    def count(self, collection: str) -> int:
        """Get document count in a collection."""
        try:
            response = requests.get(
                f"{self.base_url}/api/v1/collections/{collection}/count",
                headers=self.headers,
                timeout=10
            )
            if response.status_code == 200:
                return int(response.text)
        except Exception:
            pass
        return 0

    def print_stats(self):
        """Print statistics to console."""
        stats = self.get_stats()

        print("\n" + "=" * 50)
        print("  CHROMADB STATUS")
        print("=" * 50)
        print(f"  Connected: {'Yes' if stats['connected'] else 'No'}")
        print(f"  Version: {stats['version']}")
        print(f"  Collections: {stats['total_collections']}")
        print(f"  Documents: {stats['total_documents']}")

        if stats['collections']:
            print("\n  Collections:")
            for coll in stats['collections']:
                print(f"    - {coll['name']}: {coll['count']} docs")

        print("=" * 50 + "\n")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run ChromaDB tools from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="SCORPION ChromaDB Tools")
    parser.add_argument("--stats", action="store_true", help="Show stats")
    parser.add_argument("--list", action="store_true", help="List collections")
    parser.add_argument("--create", help="Create collection")
    parser.add_argument("--delete", help="Delete collection")
    parser.add_argument("--search", help="Collection to search")
    parser.add_argument("--query", help="Search query")

    args = parser.parse_args()

    tools = ChromaTools()

    if args.stats:
        tools.print_stats()
    elif args.list:
        collections = tools.list_collections()
        for coll in collections:
            print(f"  - {coll.get('name')}")
    elif args.create:
        tools.create_collection(args.create)
    elif args.delete:
        tools.delete_collection(args.delete)
    elif args.search and args.query:
        results = tools.search(args.search, args.query)
        for r in results:
            print(f"\n{r['document'][:200]}...")
            print(f"  Distance: {r['distance']}")
    else:
        tools.print_stats()


if __name__ == "__main__":
    main()
