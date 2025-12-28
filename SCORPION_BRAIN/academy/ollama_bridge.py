"""
SCORPION_BRAIN Ollama Bridge
============================
Connect babies to real Ollama models for inference.

Features:
- Model configuration per baby
- Async inference calls
- Response streaming
- Fallback handling
- Token tracking
"""

import asyncio
import aiohttp
import json
from typing import Dict, List, Optional, Any, AsyncIterator
from dataclasses import dataclass, field
from datetime import datetime
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class ModelConfig:
    """Configuration for an Ollama model."""
    name: str
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    num_predict: int = 512
    stop: List[str] = field(default_factory=list)
    system_prompt: str = ""

    def to_dict(self) -> Dict:
        return {
            "model": self.name,
            "options": {
                "temperature": self.temperature,
                "top_p": self.top_p,
                "top_k": self.top_k,
                "num_predict": self.num_predict,
            },
            "system": self.system_prompt,
        }


@dataclass
class InferenceResult:
    """Result from an Ollama inference call."""
    model: str
    prompt: str
    response: str
    done: bool
    total_duration: Optional[int] = None  # nanoseconds
    load_duration: Optional[int] = None
    prompt_eval_count: Optional[int] = None
    eval_count: Optional[int] = None
    error: Optional[str] = None
    timestamp: datetime = field(default_factory=datetime.now)

    @property
    def tokens_per_second(self) -> Optional[float]:
        """Calculate tokens per second if available."""
        if self.eval_count and self.total_duration:
            seconds = self.total_duration / 1e9
            return self.eval_count / seconds if seconds > 0 else None
        return None


# Default model configurations for each baby
BABY_MODEL_CONFIGS: Dict[str, ModelConfig] = {
    "MARCUS": ModelConfig(
        name="llama3.2",
        temperature=0.3,  # More deterministic for reasoning
        system_prompt="You are MARCUS, a logical and analytical AI. Think step by step and reason carefully."
    ),
    "VULCAN": ModelConfig(
        name="codellama",
        temperature=0.2,  # Very deterministic for code
        system_prompt="You are VULCAN, a precise builder AI. Focus on patterns, structure, and clean implementation."
    ),
    "HERMES": ModelConfig(
        name="llama3.2",
        temperature=0.8,  # More creative for communication
        system_prompt="You are HERMES, an expressive communicator AI. Be clear, engaging, and empathetic."
    ),
    "ATHENA": ModelConfig(
        name="llama3.2",
        temperature=0.5,
        system_prompt="You are ATHENA, a strategic planner AI. Think about the big picture and optimal paths."
    ),
    "PHOENIX": ModelConfig(
        name="llama3.2",
        temperature=0.9,  # Most creative for learning/adaptation
        system_prompt="You are PHOENIX, an adaptive learner AI. Be curious, creative, and open to new ideas."
    ),
}


class OllamaBridge:
    """
    Bridge to connect SCORPION_BRAIN babies with Ollama models.

    Usage:
        bridge = OllamaBridge()
        result = await bridge.generate("MARCUS", "Explain quantum computing")
        print(result.response)
    """

    def __init__(
        self,
        base_url: str = "http://localhost:11434",
        timeout: int = 120,
        model_configs: Dict[str, ModelConfig] = None
    ):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.model_configs = model_configs or BABY_MODEL_CONFIGS.copy()
        self._session: Optional[aiohttp.ClientSession] = None
        self._stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_tokens": 0
        }

    async def _get_session(self) -> aiohttp.ClientSession:
        """Get or create aiohttp session."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout)
            )
        return self._session

    async def close(self):
        """Close the HTTP session."""
        if self._session and not self._session.closed:
            await self._session.close()

    def get_config(self, baby_name: str) -> ModelConfig:
        """Get model config for a baby."""
        baby_name = baby_name.upper()
        if baby_name not in self.model_configs:
            # Return default config
            return ModelConfig(name="llama3.2")
        return self.model_configs[baby_name]

    def set_config(self, baby_name: str, config: ModelConfig):
        """Set model config for a baby."""
        self.model_configs[baby_name.upper()] = config

    async def check_health(self) -> bool:
        """Check if Ollama server is running."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/tags") as resp:
                return resp.status == 200
        except Exception as e:
            logger.warning(f"Ollama health check failed: {e}")
            return False

    async def list_models(self) -> List[str]:
        """List available models on Ollama server."""
        try:
            session = await self._get_session()
            async with session.get(f"{self.base_url}/api/tags") as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return [m["name"] for m in data.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
        return []

    async def generate(
        self,
        baby_name: str,
        prompt: str,
        context: Dict = None,
        override_config: Dict = None
    ) -> InferenceResult:
        """
        Generate a response using the baby's configured model.

        Args:
            baby_name: Name of the baby (MARCUS, VULCAN, etc.)
            prompt: The prompt to send
            context: Optional context dict to include
            override_config: Optional config overrides

        Returns:
            InferenceResult with the response
        """
        self._stats["total_calls"] += 1
        config = self.get_config(baby_name)

        # Build the full prompt
        full_prompt = prompt
        if context:
            context_str = json.dumps(context, indent=2)
            full_prompt = f"Context:\n{context_str}\n\nTask:\n{prompt}"

        # Build request payload
        payload = config.to_dict()
        payload["prompt"] = full_prompt
        payload["stream"] = False

        # Apply overrides
        if override_config:
            payload.update(override_config)

        try:
            session = await self._get_session()
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    self._stats["successful_calls"] += 1
                    self._stats["total_tokens"] += data.get("eval_count", 0)

                    return InferenceResult(
                        model=config.name,
                        prompt=prompt,
                        response=data.get("response", ""),
                        done=data.get("done", True),
                        total_duration=data.get("total_duration"),
                        load_duration=data.get("load_duration"),
                        prompt_eval_count=data.get("prompt_eval_count"),
                        eval_count=data.get("eval_count")
                    )
                else:
                    error_text = await resp.text()
                    self._stats["failed_calls"] += 1
                    return InferenceResult(
                        model=config.name,
                        prompt=prompt,
                        response="",
                        done=True,
                        error=f"HTTP {resp.status}: {error_text}"
                    )

        except asyncio.TimeoutError:
            self._stats["failed_calls"] += 1
            return InferenceResult(
                model=config.name,
                prompt=prompt,
                response="",
                done=True,
                error="Request timed out"
            )
        except Exception as e:
            self._stats["failed_calls"] += 1
            return InferenceResult(
                model=config.name,
                prompt=prompt,
                response="",
                done=True,
                error=str(e)
            )

    async def generate_stream(
        self,
        baby_name: str,
        prompt: str,
        context: Dict = None
    ) -> AsyncIterator[str]:
        """
        Stream a response token by token.

        Usage:
            async for token in bridge.generate_stream("MARCUS", "Hello"):
                print(token, end="", flush=True)
        """
        config = self.get_config(baby_name)

        full_prompt = prompt
        if context:
            context_str = json.dumps(context, indent=2)
            full_prompt = f"Context:\n{context_str}\n\nTask:\n{prompt}"

        payload = config.to_dict()
        payload["prompt"] = full_prompt
        payload["stream"] = True

        try:
            session = await self._get_session()
            async with session.post(
                f"{self.base_url}/api/generate",
                json=payload
            ) as resp:
                if resp.status == 200:
                    async for line in resp.content:
                        if line:
                            try:
                                data = json.loads(line)
                                if "response" in data:
                                    yield data["response"]
                                if data.get("done"):
                                    break
                            except json.JSONDecodeError:
                                continue

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"[Error: {e}]"

    async def chat(
        self,
        baby_name: str,
        messages: List[Dict[str, str]],
        context: Dict = None
    ) -> InferenceResult:
        """
        Send a chat-style conversation.

        Args:
            baby_name: Name of the baby
            messages: List of {"role": "user"|"assistant", "content": "..."}
            context: Optional context

        Returns:
            InferenceResult with the response
        """
        config = self.get_config(baby_name)

        # Add system message if not present
        if messages and messages[0].get("role") != "system":
            messages = [{"role": "system", "content": config.system_prompt}] + messages

        payload = {
            "model": config.name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": config.temperature,
                "top_p": config.top_p,
            }
        }

        try:
            session = await self._get_session()
            async with session.post(
                f"{self.base_url}/api/chat",
                json=payload
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    message = data.get("message", {})
                    return InferenceResult(
                        model=config.name,
                        prompt=str(messages),
                        response=message.get("content", ""),
                        done=data.get("done", True),
                        total_duration=data.get("total_duration"),
                        eval_count=data.get("eval_count")
                    )
                else:
                    error_text = await resp.text()
                    return InferenceResult(
                        model=config.name,
                        prompt=str(messages),
                        response="",
                        done=True,
                        error=f"HTTP {resp.status}: {error_text}"
                    )

        except Exception as e:
            return InferenceResult(
                model=config.name,
                prompt=str(messages),
                response="",
                done=True,
                error=str(e)
            )

    async def embed(self, text: str, model: str = "nomic-embed-text") -> Optional[List[float]]:
        """
        Get embeddings for text.

        Args:
            text: Text to embed
            model: Embedding model (default: nomic-embed-text)

        Returns:
            List of floats representing the embedding vector
        """
        try:
            session = await self._get_session()
            async with session.post(
                f"{self.base_url}/api/embeddings",
                json={"model": model, "prompt": text}
            ) as resp:
                if resp.status == 200:
                    data = await resp.json()
                    return data.get("embedding")
        except Exception as e:
            logger.error(f"Embedding error: {e}")
        return None

    def get_stats(self) -> Dict:
        """Get usage statistics."""
        return {
            **self._stats,
            "success_rate": (
                self._stats["successful_calls"] / self._stats["total_calls"]
                if self._stats["total_calls"] > 0 else 0
            )
        }

    def reset_stats(self):
        """Reset usage statistics."""
        self._stats = {
            "total_calls": 0,
            "successful_calls": 0,
            "failed_calls": 0,
            "total_tokens": 0
        }


# Singleton instance
_bridge: Optional[OllamaBridge] = None


def get_ollama_bridge(base_url: str = None) -> OllamaBridge:
    """Get or create the Ollama bridge instance."""
    global _bridge
    if _bridge is None:
        _bridge = OllamaBridge(base_url=base_url or "http://localhost:11434")
    return _bridge


async def quick_generate(baby_name: str, prompt: str) -> str:
    """Quick helper to generate a response."""
    bridge = get_ollama_bridge()
    result = await bridge.generate(baby_name, prompt)
    if result.error:
        return f"Error: {result.error}"
    return result.response


if __name__ == "__main__":
    # Demo
    async def demo():
        bridge = OllamaBridge()

        # Check health
        healthy = await bridge.check_health()
        print(f"Ollama healthy: {healthy}")

        if healthy:
            # List models
            models = await bridge.list_models()
            print(f"Available models: {models}")

            # Generate
            result = await bridge.generate(
                "MARCUS",
                "What is 2 + 2? Explain your reasoning."
            )
            print(f"\nMARCUS says: {result.response}")
            print(f"Tokens/sec: {result.tokens_per_second}")

        await bridge.close()

    asyncio.run(demo())
