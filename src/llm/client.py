"""Claude API client with prompt caching for cost/latency optimization."""

from __future__ import annotations

import logging
import os
from functools import lru_cache

import anthropic

logger = logging.getLogger(__name__)

MODEL_FAST = "claude-sonnet-4-6"   # scanner, scorer, semantic
MODEL_STRONG = "claude-opus-4-7"   # patch generation (complex reasoning)

# System prompts are large and stable — ideal for prompt caching
_CACHE_CONTROL = {"type": "ephemeral"}


class LLMClient:
    def __init__(self) -> None:
        self._client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
        self._cache_hits = 0
        self._total_calls = 0

    def query(
        self,
        system: str,
        user: str,
        model: str = "sonnet",
        max_tokens: int = 4096,
    ) -> str:
        """Send a query with prompt caching on the system prompt."""
        resolved_model = MODEL_STRONG if model == "opus" else MODEL_FAST
        self._total_calls += 1

        try:
            response = self._client.messages.create(
                model=resolved_model,
                max_tokens=max_tokens,
                system=[
                    {
                        "type": "text",
                        "text": system,
                        "cache_control": _CACHE_CONTROL,
                    }
                ],
                messages=[{"role": "user", "content": user}],
            )
        except anthropic.APIError as exc:
            logger.error("[llm] API error: %s", exc)
            raise

        usage = response.usage
        if hasattr(usage, "cache_read_input_tokens") and usage.cache_read_input_tokens:
            self._cache_hits += 1
            logger.debug(
                "[llm] cache hit — read %d tokens from cache",
                usage.cache_read_input_tokens,
            )

        text = response.content[0].text
        logger.debug("[llm] response length: %d chars", len(text))
        return text

    def cache_stats(self) -> dict:
        return {
            "total_calls": self._total_calls,
            "cache_hits": self._cache_hits,
            "hit_rate": self._cache_hits / max(self._total_calls, 1),
        }
