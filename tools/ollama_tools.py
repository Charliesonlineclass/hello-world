"""
SCORPION Ollama Tools
=====================

Tools for interacting with Ollama AI service.
Handles model management, completions, and embeddings.

Author: SCORPION Commander
Version: 1.0.0 - TESTUDO Formation
"""

import os
import json
import logging
import time
from typing import Dict, List, Optional, Any, Generator
import requests

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("SCORPION-OLLAMA")


class OllamaTools:
    """
    Tools for Ollama operations.

    Provides:
    - Model listing and management
    - Text generation
    - Chat completions
    - Embeddings generation
    - Streaming support
    """

    def __init__(
        self,
        host: str = None,
        port: int = None
    ):
        self.host = host or os.getenv("OLLAMA_HOST", "localhost")
        self.port = port or int(os.getenv("OLLAMA_PORT", "11434"))
        self.base_url = f"http://{self.host}:{self.port}"

        logger.info(f"OllamaTools initialized: {self.base_url}")

    # -------------------------------------------------------------------------
    # Connection
    # -------------------------------------------------------------------------

    def is_running(self) -> bool:
        """Check if Ollama is running."""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=5
            )
            return response.status_code == 200
        except Exception:
            return False

    # -------------------------------------------------------------------------
    # Model Management
    # -------------------------------------------------------------------------

    def list_models(self) -> List[Dict[str, Any]]:
        """List all available models."""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                return data.get("models", [])
        except Exception as e:
            logger.error(f"List models failed: {e}")
        return []

    def get_model_names(self) -> List[str]:
        """Get just the model names."""
        models = self.list_models()
        return [m["name"].split(":")[0] for m in models]

    def has_model(self, name: str) -> bool:
        """Check if a model is installed."""
        names = self.get_model_names()
        return name in names or any(name in n for n in names)

    def pull_model(self, name: str, stream: bool = True) -> bool:
        """Download a model."""
        try:
            logger.info(f"Pulling model: {name}")

            response = requests.post(
                f"{self.base_url}/api/pull",
                json={"name": name, "stream": stream},
                timeout=None,  # No timeout for large downloads
                stream=stream
            )

            if stream:
                for line in response.iter_lines():
                    if line:
                        data = json.loads(line)
                        status = data.get("status", "")
                        if "pulling" in status:
                            print(f"  {status}", end="\r")
                        elif "success" in status:
                            print(f"\n  Model {name} pulled successfully")
                            return True
            else:
                return response.status_code == 200

        except Exception as e:
            logger.error(f"Pull model failed: {e}")

        return False

    def delete_model(self, name: str) -> bool:
        """Delete a model."""
        try:
            response = requests.delete(
                f"{self.base_url}/api/delete",
                json={"name": name},
                timeout=30
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Delete model failed: {e}")
        return False

    def model_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get detailed model information."""
        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": name},
                timeout=10
            )
            if response.status_code == 200:
                return response.json()
        except Exception as e:
            logger.error(f"Model info failed: {e}")
        return None

    # -------------------------------------------------------------------------
    # Generation
    # -------------------------------------------------------------------------

    def generate(
        self,
        model: str,
        prompt: str,
        system: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
        **options
    ) -> Dict[str, Any]:
        """Generate a completion."""
        try:
            start_time = time.time()

            payload = {
                "model": model,
                "prompt": prompt,
                "stream": stream,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    **options
                }
            }

            if system:
                payload["system"] = system

            if stream:
                return self._generate_stream(payload, start_time)

            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120
            )

            elapsed_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "response": data.get("response", ""),
                    "elapsed_ms": elapsed_ms,
                    "eval_count": data.get("eval_count", 0),
                    "eval_duration": data.get("eval_duration", 0),
                    "tokens_per_second": self._calc_tps(data)
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "elapsed_ms": elapsed_ms
                }

        except requests.exceptions.Timeout:
            return {"success": False, "error": "Timeout"}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def _generate_stream(
        self,
        payload: Dict,
        start_time: float
    ) -> Generator[str, None, None]:
        """Generate with streaming response."""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json=payload,
                timeout=120,
                stream=True
            )

            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]
                    if data.get("done"):
                        break

        except Exception as e:
            yield f"\n[Error: {e}]"

    def _calc_tps(self, data: Dict) -> float:
        """Calculate tokens per second."""
        eval_count = data.get("eval_count", 0)
        eval_duration = data.get("eval_duration", 0)
        if eval_duration > 0:
            return eval_count / (eval_duration / 1e9)
        return 0.0

    # -------------------------------------------------------------------------
    # Chat
    # -------------------------------------------------------------------------

    def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
        **options
    ) -> Dict[str, Any]:
        """Chat completion with message history."""
        try:
            start_time = time.time()

            payload = {
                "model": model,
                "messages": messages,
                "stream": stream,
                "options": {
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    **options
                }
            }

            response = requests.post(
                f"{self.base_url}/api/chat",
                json=payload,
                timeout=120
            )

            elapsed_ms = (time.time() - start_time) * 1000

            if response.status_code == 200:
                data = response.json()
                return {
                    "success": True,
                    "message": data.get("message", {}),
                    "response": data.get("message", {}).get("content", ""),
                    "elapsed_ms": elapsed_ms,
                    "eval_count": data.get("eval_count", 0)
                }
            else:
                return {
                    "success": False,
                    "error": f"HTTP {response.status_code}",
                    "elapsed_ms": elapsed_ms
                }

        except Exception as e:
            return {"success": False, "error": str(e)}

    # -------------------------------------------------------------------------
    # Embeddings
    # -------------------------------------------------------------------------

    def embeddings(
        self,
        model: str,
        text: str
    ) -> Optional[List[float]]:
        """Generate embeddings for text."""
        try:
            response = requests.post(
                f"{self.base_url}/api/embeddings",
                json={
                    "model": model,
                    "prompt": text
                },
                timeout=30
            )

            if response.status_code == 200:
                data = response.json()
                return data.get("embedding", [])

        except Exception as e:
            logger.error(f"Embeddings failed: {e}")

        return None

    def batch_embeddings(
        self,
        model: str,
        texts: List[str]
    ) -> List[Optional[List[float]]]:
        """Generate embeddings for multiple texts."""
        return [self.embeddings(model, text) for text in texts]

    # -------------------------------------------------------------------------
    # Utilities
    # -------------------------------------------------------------------------

    def test_model(self, model: str, prompt: str = "Say hello.") -> Dict[str, Any]:
        """Quick test of a model."""
        return self.generate(model, prompt, max_tokens=50)

    def benchmark_model(
        self,
        model: str,
        prompt: str = "Write a short paragraph about technology.",
        iterations: int = 3
    ) -> Dict[str, Any]:
        """Benchmark model performance."""
        times = []
        tps_values = []

        for i in range(iterations):
            result = self.generate(model, prompt)
            if result.get("success"):
                times.append(result["elapsed_ms"])
                tps_values.append(result.get("tokens_per_second", 0))

        if times:
            return {
                "model": model,
                "iterations": iterations,
                "avg_time_ms": sum(times) / len(times),
                "min_time_ms": min(times),
                "max_time_ms": max(times),
                "avg_tps": sum(tps_values) / len(tps_values) if tps_values else 0
            }

        return {"model": model, "error": "All iterations failed"}

    def print_status(self):
        """Print Ollama status to console."""
        print("\n" + "=" * 50)
        print("  OLLAMA STATUS")
        print("=" * 50)
        print(f"  URL: {self.base_url}")
        print(f"  Running: {'Yes' if self.is_running() else 'No'}")

        models = self.list_models()
        print(f"  Models: {len(models)}")

        if models:
            print("\n  Installed models:")
            for m in models:
                name = m.get("name", "unknown")
                size = m.get("size", 0) / (1024**3)  # GB
                print(f"    - {name} ({size:.1f} GB)")

        print("=" * 50 + "\n")


# =============================================================================
# MAIN
# =============================================================================

def main():
    """Run Ollama tools from command line."""
    import argparse

    parser = argparse.ArgumentParser(description="SCORPION Ollama Tools")
    parser.add_argument("--status", action="store_true", help="Show status")
    parser.add_argument("--list", action="store_true", help="List models")
    parser.add_argument("--pull", help="Pull a model")
    parser.add_argument("--test", help="Test a model")
    parser.add_argument("--benchmark", help="Benchmark a model")
    parser.add_argument("--generate", help="Model for generation")
    parser.add_argument("--prompt", help="Prompt for generation")

    args = parser.parse_args()

    tools = OllamaTools()

    if args.status:
        tools.print_status()
    elif args.list:
        for name in tools.get_model_names():
            print(f"  - {name}")
    elif args.pull:
        tools.pull_model(args.pull)
    elif args.test:
        result = tools.test_model(args.test)
        if result.get("success"):
            print(f"Response: {result['response']}")
            print(f"Time: {result['elapsed_ms']:.0f}ms")
        else:
            print(f"Error: {result.get('error')}")
    elif args.benchmark:
        result = tools.benchmark_model(args.benchmark)
        print(f"Model: {result['model']}")
        print(f"Avg time: {result.get('avg_time_ms', 0):.0f}ms")
        print(f"Tokens/sec: {result.get('avg_tps', 0):.1f}")
    elif args.generate and args.prompt:
        result = tools.generate(args.generate, args.prompt)
        if result.get("success"):
            print(result["response"])
        else:
            print(f"Error: {result.get('error')}")
    else:
        tools.print_status()


if __name__ == "__main__":
    main()
