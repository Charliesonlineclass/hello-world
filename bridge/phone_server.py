"""
SCORPION Bridge - Phone Server
==============================

FastAPI server that exposes AI babies to mobile devices.
Run this on your Linux server, connect from Termux on Android.

Requirements:
    pip install fastapi uvicorn requests

Usage:
    python phone_server.py
    # Server runs on port 9876
    # Then connect from Termux with termux_client.py
"""

import os
import json
import hashlib
import time
from datetime import datetime
from typing import Optional, Dict, List, Any
from pathlib import Path
import logging
import requests

try:
    from fastapi import FastAPI, HTTPException, Header, Request
    from fastapi.middleware.cors import CORSMiddleware
    from pydantic import BaseModel
    import uvicorn
except ImportError:
    print("FastAPI not installed. Run: pip install fastapi uvicorn")
    FastAPI = None

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("BRIDGE.server")

# Configuration
SERVER_PORT = int(os.environ.get("BRIDGE_PORT", 9876))
API_KEY = os.environ.get("BRIDGE_API_KEY", "scorpion-default-key")
OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
CHROMADB_PATH = os.environ.get("CHROMADB_PATH", "./chromadb_data")

# Baby configurations (model mappings)
BABIES = {
    "marcus": {
        "model": "mistral",
        "description": "Main assistant - balanced and helpful",
        "system_prompt": "You are MARCUS, a helpful AI assistant. Be concise and practical."
    },
    "hermes": {
        "model": "phi",
        "description": "Fast responder - quick answers",
        "system_prompt": "You are HERMES, a fast AI. Give brief, direct answers."
    },
    "athena": {
        "model": "codellama",
        "description": "Code specialist - programming help",
        "system_prompt": "You are ATHENA, a coding expert. Help with programming tasks."
    },
    "apollo": {
        "model": "llama2",
        "description": "Creative writer - content generation",
        "system_prompt": "You are APOLLO, a creative AI. Help with writing and content."
    }
}

# Request/Response models
class AskRequest(BaseModel):
    baby: str = "marcus"
    prompt: str
    context: Optional[str] = None
    max_tokens: int = 500
    temperature: float = 0.7

class QuickRequest(BaseModel):
    prompt: str
    max_tokens: int = 200

class KnowledgeRequest(BaseModel):
    query: str
    n_results: int = 5
    collection: str = "default"

class Response(BaseModel):
    success: bool
    response: Optional[str] = None
    baby: Optional[str] = None
    model: Optional[str] = None
    elapsed: Optional[float] = None
    error: Optional[str] = None


class ScorpionAPI:
    """
    Core API class for SCORPION Bridge.
    Can be used standalone or with FastAPI.
    """

    def __init__(self, ollama_host: str = OLLAMA_HOST):
        self.ollama_host = ollama_host
        self._chroma_client = None
        self.request_count = 0
        self.start_time = datetime.now()

    def check_ollama(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=5)
            return response.status_code == 200
        except:
            return False

    def list_models(self) -> List[str]:
        """List available Ollama models."""
        try:
            response = requests.get(f"{self.ollama_host}/api/tags", timeout=10)
            if response.status_code == 200:
                models = response.json().get("models", [])
                return [m["name"] for m in models]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
        return []

    def ask_baby(
        self,
        baby: str,
        prompt: str,
        context: Optional[str] = None,
        max_tokens: int = 500,
        temperature: float = 0.7
    ) -> Dict:
        """
        Ask a specific baby (AI model) a question.

        Args:
            baby: Baby name (marcus, hermes, athena, apollo)
            prompt: User prompt
            context: Optional context to include
            max_tokens: Maximum response tokens
            temperature: Response creativity (0-1)

        Returns:
            Response dictionary
        """
        start = time.time()
        self.request_count += 1

        # Get baby config
        baby_config = BABIES.get(baby.lower())
        if not baby_config:
            return {
                "success": False,
                "error": f"Unknown baby: {baby}. Available: {list(BABIES.keys())}"
            }

        # Build prompt with system prompt
        full_prompt = baby_config["system_prompt"]
        if context:
            full_prompt += f"\n\nContext: {context}"
        full_prompt += f"\n\nUser: {prompt}\n\nAssistant:"

        # Call Ollama
        try:
            response = requests.post(
                f"{self.ollama_host}/api/generate",
                json={
                    "model": baby_config["model"],
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "num_predict": max_tokens,
                        "temperature": temperature
                    }
                },
                timeout=120
            )

            if response.status_code == 200:
                result = response.json()
                elapsed = time.time() - start

                return {
                    "success": True,
                    "response": result.get("response", "").strip(),
                    "baby": baby,
                    "model": baby_config["model"],
                    "elapsed": round(elapsed, 2)
                }
            else:
                return {
                    "success": False,
                    "error": f"Ollama error: {response.status_code}"
                }

        except requests.exceptions.ConnectionError:
            return {
                "success": False,
                "error": f"Cannot connect to Ollama at {self.ollama_host}"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def quick_ask(self, prompt: str, max_tokens: int = 200) -> Dict:
        """
        Quick ask using fastest baby (HERMES).
        For simple queries that need fast responses.
        """
        return self.ask_baby("hermes", prompt, max_tokens=max_tokens, temperature=0.3)

    def search_knowledge(
        self,
        query: str,
        n_results: int = 5,
        collection: str = "default"
    ) -> Dict:
        """
        Search ChromaDB knowledge base.

        Args:
            query: Search query
            n_results: Number of results
            collection: ChromaDB collection name

        Returns:
            Search results
        """
        try:
            import chromadb
            from chromadb.config import Settings

            if self._chroma_client is None:
                self._chroma_client = chromadb.Client(Settings(
                    chroma_db_impl="duckdb+parquet",
                    persist_directory=CHROMADB_PATH,
                    anonymized_telemetry=False
                ))

            try:
                coll = self._chroma_client.get_collection(collection)
            except:
                return {
                    "success": False,
                    "error": f"Collection '{collection}' not found"
                }

            results = coll.query(
                query_texts=[query],
                n_results=n_results
            )

            return {
                "success": True,
                "results": [
                    {
                        "id": results["ids"][0][i],
                        "document": results["documents"][0][i] if results.get("documents") else None,
                        "metadata": results["metadatas"][0][i] if results.get("metadatas") else None,
                        "distance": results["distances"][0][i] if results.get("distances") else None
                    }
                    for i in range(len(results["ids"][0]))
                ]
            }

        except ImportError:
            return {
                "success": False,
                "error": "ChromaDB not installed"
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def get_status(self) -> Dict:
        """Get server status and available babies."""
        uptime = (datetime.now() - self.start_time).total_seconds()
        available_models = self.list_models()

        babies_status = {}
        for name, config in BABIES.items():
            babies_status[name] = {
                "model": config["model"],
                "description": config["description"],
                "available": config["model"] in available_models or any(
                    config["model"] in m for m in available_models
                )
            }

        return {
            "status": "online",
            "ollama": self.check_ollama(),
            "uptime_seconds": round(uptime, 1),
            "requests_served": self.request_count,
            "babies": babies_status,
            "available_models": available_models
        }


# Create FastAPI app
if FastAPI:
    app = FastAPI(
        title="SCORPION Bridge",
        description="Phone to Linux AI Bridge - Query your babies from anywhere",
        version="1.0.0"
    )

    # CORS for mobile access
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    # API instance
    api = ScorpionAPI()

    def verify_api_key(x_api_key: str = Header(None)):
        """Verify API key from header."""
        if API_KEY != "scorpion-default-key" and x_api_key != API_KEY:
            raise HTTPException(status_code=401, detail="Invalid API key")
        return True

    @app.get("/")
    async def root():
        """Welcome endpoint."""
        return {
            "message": "SCORPION Bridge Online",
            "docs": "/docs",
            "status": "/status"
        }

    @app.get("/status")
    async def status():
        """Get server status and available babies."""
        return api.get_status()

    @app.post("/ask", response_model=Response)
    async def ask(request: AskRequest, x_api_key: str = Header(None)):
        """
        Ask a specific baby a question.

        - **baby**: Which AI to use (marcus, hermes, athena, apollo)
        - **prompt**: Your question
        - **context**: Optional context to include
        - **max_tokens**: Maximum response length
        - **temperature**: Creativity (0-1)
        """
        verify_api_key(x_api_key)

        result = api.ask_baby(
            baby=request.baby,
            prompt=request.prompt,
            context=request.context,
            max_tokens=request.max_tokens,
            temperature=request.temperature
        )
        return Response(**result)

    @app.post("/quick", response_model=Response)
    async def quick(request: QuickRequest, x_api_key: str = Header(None)):
        """
        Quick ask using HERMES (fastest baby).

        - **prompt**: Your question
        - **max_tokens**: Maximum response length
        """
        verify_api_key(x_api_key)

        result = api.quick_ask(
            prompt=request.prompt,
            max_tokens=request.max_tokens
        )
        return Response(**result)

    @app.post("/knowledge")
    async def knowledge(request: KnowledgeRequest, x_api_key: str = Header(None)):
        """
        Search ChromaDB knowledge base.

        - **query**: Search query
        - **n_results**: Number of results
        - **collection**: ChromaDB collection name
        """
        verify_api_key(x_api_key)

        return api.search_knowledge(
            query=request.query,
            n_results=request.n_results,
            collection=request.collection
        )

    @app.get("/babies")
    async def list_babies():
        """List all available babies and their capabilities."""
        return BABIES

    @app.get("/health")
    async def health():
        """Health check endpoint."""
        return {"status": "healthy", "ollama": api.check_ollama()}

else:
    app = None


def start_server(host: str = "0.0.0.0", port: int = SERVER_PORT):
    """
    Start the SCORPION Bridge server.

    Args:
        host: Host to bind to (0.0.0.0 for all interfaces)
        port: Port to run on
    """
    if app is None:
        print("FastAPI not available. Install with: pip install fastapi uvicorn")
        return

    print(f"""
╔══════════════════════════════════════════════════════════════╗
║                   SCORPION BRIDGE SERVER                      ║
╠══════════════════════════════════════════════════════════════╣
║  Server: http://{host}:{port}                              ║
║  Docs:   http://{host}:{port}/docs                         ║
║  Status: http://{host}:{port}/status                       ║
╠══════════════════════════════════════════════════════════════╣
║  Available Babies:                                            ║
║    - MARCUS  (mistral)   - Main assistant                    ║
║    - HERMES  (phi)       - Fast responses                    ║
║    - ATHENA  (codellama) - Code specialist                   ║
║    - APOLLO  (llama2)    - Creative writer                   ║
╠══════════════════════════════════════════════════════════════╣
║  API Key: {API_KEY[:20]}...                         ║
╚══════════════════════════════════════════════════════════════╝
    """)

    uvicorn.run(app, host=host, port=port)


if __name__ == "__main__":
    import sys

    port = SERVER_PORT
    if len(sys.argv) > 1:
        try:
            port = int(sys.argv[1])
        except ValueError:
            pass

    start_server(port=port)
