"""
Helper LLM — Lightweight wrapper for the scratch pad model.

Talks to a second llama-server instance running a small model
(Gemma 3 2B, SmolLM2 1.7B, Phi-4-mini, etc.) via OpenAI-compat API.

Optimizations baked in:
  - Aggressive max_tokens caps (helper never generates essays)
  - Low temperature by default (helper is deterministic)
  - Request timeout to prevent blocking the main pipeline
  - Token counting for throughput metrics
"""

import time
import logging
import asyncio
from dataclasses import dataclass, field
from typing import Dict, List, Optional

import httpx

logger = logging.getLogger("qwopus.scratchpad.helper")


@dataclass
class HelperConfig:
    """Configuration for the helper LLM."""

    # Connection
    base_url: str = "http://localhost:8081"
    model_name: str = "scratchpad"
    api_key: str = "no-key"

    # Generation limits — keep helper responses SHORT
    max_tokens_classify: int = 64      # Task classification
    max_tokens_compress: int = 256     # Context compression
    max_tokens_verify: int = 128       # Output verification
    max_tokens_general: int = 256      # Catch-all cap

    # Sampling — deterministic by default
    temperature: float = 0.1
    top_p: float = 0.9
    top_k: int = 20

    # Timeouts
    request_timeout: float = 5.0       # Seconds — never block main model
    connect_timeout: float = 2.0

    # Performance
    max_concurrent: int = 2            # Max parallel helper requests

    @classmethod
    def from_config(cls, config: dict) -> "HelperConfig":
        """Build from the main config.yaml dict."""
        scratch = config.get("scratchpad", {})
        return cls(
            base_url=scratch.get("helper_url", "http://localhost:8081"),
            model_name=scratch.get("helper_model", "scratchpad"),
            max_tokens_classify=scratch.get("max_tokens_classify", 64),
            max_tokens_compress=scratch.get("max_tokens_compress", 256),
            temperature=scratch.get("helper_temperature", 0.1),
            request_timeout=scratch.get("helper_timeout", 5.0),
        )


@dataclass
class HelperResult:
    """Result from a helper LLM call."""

    text: str
    tokens_in: int = 0
    tokens_out: int = 0
    elapsed_ms: float = 0.0
    error: Optional[str] = None

    @property
    def tok_per_sec(self) -> float:
        if self.elapsed_ms <= 0:
            return 0.0
        return self.tokens_out / (self.elapsed_ms / 1000)

    @property
    def ok(self) -> bool:
        return self.error is None


class HelperLLM:
    """
    Async client for the scratch pad helper model.

    Designed to never block the main model for more than `request_timeout`
    seconds. If the helper is slow or down, callers get a fast failure
    and can fall back to main-model-only paths.
    """

    def __init__(self, config: Optional[HelperConfig] = None):
        self.config = config or HelperConfig()
        self._client: Optional[httpx.AsyncClient] = None
        self._semaphore = asyncio.Semaphore(self.config.max_concurrent)
        self._stats = {"calls": 0, "failures": 0, "total_tokens": 0}

    @property
    def client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(
                    timeout=self.config.request_timeout,
                    connect=self.config.connect_timeout,
                ),
            )
        return self._client

    async def close(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def health_check(self) -> bool:
        """Check if the helper server is alive."""
        try:
            resp = await self.client.get(f"{self.config.base_url}/health")
            return resp.status_code == 200
        except Exception:
            return False

    async def complete(
        self,
        messages: List[Dict],
        max_tokens: Optional[int] = None,
        temperature: Optional[float] = None,
        system_prefix: str = "",
    ) -> HelperResult:
        """
        Send a completion request to the helper model.

        Args:
            messages: Conversation messages
            max_tokens: Override token limit
            temperature: Override temperature
            system_prefix: Prepend to system message

        Returns:
            HelperResult with text or error
        """
        async with self._semaphore:
            start = time.monotonic()
            result = HelperResult(text="")

            try:
                # Inject system prefix if provided
                req_messages = messages
                if system_prefix:
                    req_messages = [
                        {"role": "system", "content": system_prefix}
                    ] + [
                        m for m in messages if m.get("role") != "system"
                    ]

                payload = {
                    "model": self.config.model_name,
                    "messages": req_messages,
                    "max_tokens": max_tokens or self.config.max_tokens_general,
                    "temperature": temperature if temperature is not None else self.config.temperature,
                    "top_p": self.config.top_p,
                    "top_k": self.config.top_k,
                    "stream": False,
                }

                resp = await self.client.post(
                    f"{self.config.base_url}/v1/chat/completions",
                    json=payload,
                )
                resp.raise_for_status()

                data = resp.json()
                choice = data["choices"][0]
                result.text = choice.get("message", {}).get("content", "")
                usage = data.get("usage", {})
                result.tokens_in = usage.get("prompt_tokens", 0)
                result.tokens_out = usage.get("completion_tokens", 0)

                self._stats["calls"] += 1
                self._stats["total_tokens"] += result.tokens_out

            except httpx.TimeoutException:
                result.error = "timeout"
                self._stats["failures"] += 1
                logger.warning(f"Helper timeout after {self.config.request_timeout}s")

            except httpx.HTTPStatusError as e:
                result.error = f"http_{e.response.status_code}"
                self._stats["failures"] += 1
                logger.warning(f"Helper HTTP error: {e}")

            except Exception as e:
                result.error = str(e)
                self._stats["failures"] += 1
                logger.warning(f"Helper error: {e}")

            result.elapsed_ms = (time.monotonic() - start) * 1000
            return result

    @property
    def stats(self) -> Dict:
        return {**self._stats}
