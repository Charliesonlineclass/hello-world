"""
SCORPION_BRAIN Universal Algorithms
====================================
Algorithms available to ALL babies.

Algorithms:
- embeddings: Generate vector embeddings for text
- chromadb_search: Search vector database
- tool_call: Execute external tools
"""

import hashlib
import json
import asyncio
import subprocess
from typing import Dict, List, Any, Optional, Callable, Union
from dataclasses import dataclass, field
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


@dataclass
class EmbeddingResult:
    """Result of embedding generation."""
    text: str
    vector: List[float]
    model: str
    dimension: int


@dataclass
class SearchResult:
    """Result from vector search."""
    id: str
    text: str
    score: float
    metadata: Dict = field(default_factory=dict)


@dataclass
class ToolSpec:
    """Specification for a callable tool."""
    name: str
    description: str
    function: Callable
    parameters: Dict[str, type] = field(default_factory=dict)
    required_params: List[str] = field(default_factory=list)
    async_fn: bool = False


# Simple in-memory vector store (placeholder for ChromaDB)
class SimpleVectorStore:
    """
    Simple in-memory vector store for demo purposes.
    Replace with actual ChromaDB in production.
    """

    def __init__(self):
        self.documents: Dict[str, Dict] = {}
        self.vectors: Dict[str, List[float]] = {}

    def add(self, doc_id: str, text: str, vector: List[float], metadata: Dict = None):
        """Add a document to the store."""
        self.documents[doc_id] = {
            "text": text,
            "metadata": metadata or {}
        }
        self.vectors[doc_id] = vector

    def search(self, query_vector: List[float], top_k: int = 5) -> List[SearchResult]:
        """Search for similar documents."""
        if not self.vectors:
            return []

        # Calculate similarities
        results = []
        for doc_id, doc_vector in self.vectors.items():
            score = self._cosine_similarity(query_vector, doc_vector)
            results.append(SearchResult(
                id=doc_id,
                text=self.documents[doc_id]["text"],
                score=score,
                metadata=self.documents[doc_id]["metadata"]
            ))

        # Sort by score (descending)
        results.sort(key=lambda x: x.score, reverse=True)
        return results[:top_k]

    def _cosine_similarity(self, vec_a: List[float], vec_b: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        if len(vec_a) != len(vec_b):
            return 0.0

        dot_product = sum(a * b for a, b in zip(vec_a, vec_b))
        mag_a = sum(a * a for a in vec_a) ** 0.5
        mag_b = sum(b * b for b in vec_b) ** 0.5

        if mag_a == 0 or mag_b == 0:
            return 0.0

        return dot_product / (mag_a * mag_b)

    def delete(self, doc_id: str):
        """Delete a document."""
        if doc_id in self.documents:
            del self.documents[doc_id]
            del self.vectors[doc_id]

    def count(self) -> int:
        """Get document count."""
        return len(self.documents)


# Global vector store instance
_vector_store: Optional[SimpleVectorStore] = None


def get_vector_store() -> SimpleVectorStore:
    """Get or create the vector store."""
    global _vector_store
    if _vector_store is None:
        _vector_store = SimpleVectorStore()
    return _vector_store


# Tool registry
_tool_registry: Dict[str, ToolSpec] = {}


def register_tool(
    name: str,
    description: str,
    function: Callable,
    parameters: Dict[str, type] = None,
    required: List[str] = None
):
    """Register a tool for use by babies."""
    _tool_registry[name] = ToolSpec(
        name=name,
        description=description,
        function=function,
        parameters=parameters or {},
        required_params=required or [],
        async_fn=asyncio.iscoroutinefunction(function)
    )


def generate_embeddings(task: str, context: Dict = None) -> Dict[str, Any]:
    """
    Generate vector embeddings for text.

    In production, this would call an embedding model (e.g., via Ollama).
    For now, uses a simple hash-based embedding for demonstration.

    Args:
        task: Text to embed
        context: Optional settings (model, dimension)

    Returns:
        Dict with embedding vector and metadata
    """
    context = context or {}
    text = context.get('text', task)
    model = context.get('model', 'simple-hash')
    dimension = context.get('dimension', 384)

    # Generate simple hash-based embedding (demo purposes)
    # In production, replace with actual embedding model
    vector = _generate_simple_embedding(text, dimension)

    return {
        "algorithm": "embeddings",
        "text": text[:100],
        "text_length": len(text),
        "model": model,
        "dimension": dimension,
        "vector": vector,
        "vector_norm": sum(v * v for v in vector) ** 0.5
    }


def chromadb_search(task: str, context: Dict = None) -> Dict[str, Any]:
    """
    Search the vector database for similar content.

    Args:
        task: Query text
        context: Should contain 'query' or use task, optional 'top_k'

    Returns:
        Dict with search results
    """
    context = context or {}
    query = context.get('query', task)
    top_k = context.get('top_k', 5)
    collection = context.get('collection', 'default')

    # Get vector store
    store = get_vector_store()

    # Generate query embedding
    query_embedding = generate_embeddings("", {"text": query})
    query_vector = query_embedding["vector"]

    # Search
    results = store.search(query_vector, top_k)

    return {
        "algorithm": "chromadb_search",
        "query": query[:100],
        "collection": collection,
        "results_count": len(results),
        "total_documents": store.count(),
        "results": [
            {
                "id": r.id,
                "text": r.text[:200],
                "score": round(r.score, 4),
                "metadata": r.metadata
            }
            for r in results
        ]
    }


def tool_call(task: str, context: Dict = None) -> Dict[str, Any]:
    """
    Execute a registered tool.

    Args:
        task: Tool name or description
        context: Should contain 'tool' name and 'args' dict

    Returns:
        Dict with tool execution result
    """
    context = context or {}
    tool_name = context.get('tool', task)
    args = context.get('args', {})

    # Find the tool
    if tool_name not in _tool_registry:
        # Try to find by partial match
        matches = [t for t in _tool_registry if tool_name.lower() in t.lower()]
        if matches:
            tool_name = matches[0]
        else:
            return {
                "algorithm": "tool_call",
                "tool": tool_name,
                "status": "error",
                "error": f"Tool not found: {tool_name}",
                "available_tools": list(_tool_registry.keys())
            }

    tool = _tool_registry[tool_name]

    # Validate required parameters
    missing = [p for p in tool.required_params if p not in args]
    if missing:
        return {
            "algorithm": "tool_call",
            "tool": tool_name,
            "status": "error",
            "error": f"Missing required parameters: {missing}",
            "required": tool.required_params
        }

    # Execute the tool
    try:
        if tool.async_fn:
            # Handle async function
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # We're in an async context
                result = asyncio.create_task(tool.function(**args))
            else:
                result = loop.run_until_complete(tool.function(**args))
        else:
            result = tool.function(**args)

        return {
            "algorithm": "tool_call",
            "tool": tool_name,
            "status": "success",
            "result": result,
            "args_used": args
        }

    except Exception as e:
        return {
            "algorithm": "tool_call",
            "tool": tool_name,
            "status": "error",
            "error": str(e),
            "args_used": args
        }


# Helper functions

def _generate_simple_embedding(text: str, dimension: int = 384) -> List[float]:
    """
    Generate a simple hash-based embedding.

    This is a placeholder - in production, use a real embedding model.
    """
    # Create a hash of the text
    text_hash = hashlib.sha256(text.encode()).hexdigest()

    # Convert to pseudo-random floats
    vector = []
    for i in range(dimension):
        # Use different parts of the hash + position for variety
        seed = int(text_hash[(i * 2) % 64:(i * 2 + 2) % 64 + 2], 16)
        # Convert to float in range [-1, 1]
        value = (seed / 255.0) * 2 - 1
        vector.append(value)

    # Normalize the vector
    norm = sum(v * v for v in vector) ** 0.5
    if norm > 0:
        vector = [v / norm for v in vector]

    return vector


# Built-in tools

def _shell_tool(command: str, timeout: int = 30) -> Dict:
    """Execute a shell command safely."""
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "returncode": result.returncode
        }
    except subprocess.TimeoutExpired:
        return {"error": "Command timed out"}
    except Exception as e:
        return {"error": str(e)}


def _file_read_tool(path: str) -> Dict:
    """Read a file."""
    try:
        with open(path, 'r') as f:
            content = f.read()
        return {"content": content, "length": len(content)}
    except Exception as e:
        return {"error": str(e)}


def _file_write_tool(path: str, content: str) -> Dict:
    """Write to a file."""
    try:
        Path(path).parent.mkdir(parents=True, exist_ok=True)
        with open(path, 'w') as f:
            f.write(content)
        return {"success": True, "path": path, "bytes_written": len(content)}
    except Exception as e:
        return {"error": str(e)}


def _http_get_tool(url: str) -> Dict:
    """Make an HTTP GET request."""
    try:
        import urllib.request
        with urllib.request.urlopen(url, timeout=10) as response:
            content = response.read().decode('utf-8')
            return {
                "status": response.status,
                "content": content[:10000],  # Limit size
                "truncated": len(content) > 10000
            }
    except Exception as e:
        return {"error": str(e)}


def _json_parse_tool(json_str: str) -> Dict:
    """Parse JSON string."""
    try:
        data = json.loads(json_str)
        return {"success": True, "data": data}
    except json.JSONDecodeError as e:
        return {"error": f"Invalid JSON: {e}"}


# Register built-in tools
register_tool(
    "shell",
    "Execute a shell command",
    _shell_tool,
    {"command": str, "timeout": int},
    ["command"]
)

register_tool(
    "file_read",
    "Read contents of a file",
    _file_read_tool,
    {"path": str},
    ["path"]
)

register_tool(
    "file_write",
    "Write content to a file",
    _file_write_tool,
    {"path": str, "content": str},
    ["path", "content"]
)

register_tool(
    "http_get",
    "Make HTTP GET request",
    _http_get_tool,
    {"url": str},
    ["url"]
)

register_tool(
    "json_parse",
    "Parse a JSON string",
    _json_parse_tool,
    {"json_str": str},
    ["json_str"]
)


class UniversalEngine:
    """
    High-level interface for universal algorithms.

    Usage:
        engine = UniversalEngine()
        embedding = engine.embed("Hello world")
        results = engine.search("query", top_k=5)
        output = engine.call_tool("shell", command="echo hello")
    """

    def __init__(self):
        self.vector_store = get_vector_store()
        self.embedding_cache: Dict[str, List[float]] = {}

    def embed(self, text: str, use_cache: bool = True) -> List[float]:
        """Generate embedding for text."""
        if use_cache and text in self.embedding_cache:
            return self.embedding_cache[text]

        result = generate_embeddings("", {"text": text})
        vector = result["vector"]

        if use_cache:
            self.embedding_cache[text] = vector

        return vector

    def add_document(self, doc_id: str, text: str, metadata: Dict = None):
        """Add a document to the vector store."""
        vector = self.embed(text)
        self.vector_store.add(doc_id, text, vector, metadata)

    def search(self, query: str, top_k: int = 5) -> List[SearchResult]:
        """Search for similar documents."""
        query_vector = self.embed(query)
        return self.vector_store.search(query_vector, top_k)

    def call_tool(self, tool_name: str, **kwargs) -> Any:
        """Call a registered tool."""
        result = tool_call("", {"tool": tool_name, "args": kwargs})
        if result["status"] == "error":
            raise RuntimeError(result.get("error", "Tool call failed"))
        return result.get("result")

    def list_tools(self) -> List[Dict]:
        """List all available tools."""
        return [
            {
                "name": spec.name,
                "description": spec.description,
                "parameters": {k: v.__name__ for k, v in spec.parameters.items()},
                "required": spec.required_params
            }
            for spec in _tool_registry.values()
        ]

    def clear_cache(self):
        """Clear the embedding cache."""
        self.embedding_cache.clear()


# Convenience functions

def quick_embed(text: str) -> List[float]:
    """Quick helper to generate embedding."""
    result = generate_embeddings("", {"text": text})
    return result["vector"]


def quick_search(query: str, top_k: int = 5) -> List[Dict]:
    """Quick helper to search vector store."""
    result = chromadb_search("", {"query": query, "top_k": top_k})
    return result.get("results", [])


def quick_tool(tool_name: str, **kwargs) -> Any:
    """Quick helper to call a tool."""
    result = tool_call("", {"tool": tool_name, "args": kwargs})
    if result["status"] == "success":
        return result["result"]
    raise RuntimeError(result.get("error"))


if __name__ == "__main__":
    # Demo
    engine = UniversalEngine()

    # Embeddings
    print("=== Embeddings ===")
    vec1 = engine.embed("Hello, world!")
    vec2 = engine.embed("Hi there, universe!")
    print(f"Vector dimension: {len(vec1)}")
    print(f"First 5 values: {vec1[:5]}")

    # Add documents
    print("\n=== Vector Store ===")
    engine.add_document("doc1", "Python is a programming language", {"type": "tech"})
    engine.add_document("doc2", "JavaScript runs in browsers", {"type": "tech"})
    engine.add_document("doc3", "Cats are furry animals", {"type": "nature"})

    results = engine.search("programming languages")
    print(f"Search results for 'programming languages':")
    for r in results:
        print(f"  [{r.score:.3f}] {r.text}")

    # Tools
    print("\n=== Tools ===")
    print("Available tools:")
    for tool in engine.list_tools():
        print(f"  - {tool['name']}: {tool['description']}")

    # Call a tool
    result = engine.call_tool("json_parse", json_str='{"name": "test", "value": 42}')
    print(f"\nJSON parse result: {result}")
