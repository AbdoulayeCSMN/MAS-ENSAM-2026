"""LLM client using Groq + NVIDIA endpoints."""

from __future__ import annotations

import logging
import os
from pathlib import Path

def load_env():
    env_file = Path(__file__).parent.parent / ".env"
    if env_file.exists():
        for line in env_file.read_text().splitlines():
            if "=" in line and not line.startswith("#"):
                key, value = line.split("=", 1)
                os.environ[key.strip()] = value.strip()
                print(f"Loaded: {key.strip()}")

load_env()

from groq import Groq
from openai import OpenAI

logger = logging.getLogger(__name__)

MODEL_FAST = "llama-3.1-8b-instant"
MODEL_STRONG = "meta/llama-3.1-70b-instruct"


class LLMClient:
    def __init__(self) -> None:
        groq_key = os.environ.get("GROQ_API_KEY")
        nvidia_key = os.environ.get("NVIDIA_API_KEY")
        
        self._groq = Groq(api_key=groq_key) if groq_key else None
        self._nvidia = OpenAI(
            base_url="https://integrate.api.nvidia.com/v1",
            api_key=nvidia_key
        ) if nvidia_key else None

        self._total_calls = 0
        
        if not self._groq:
            logger.warning("GROQ_API_KEY not found")
        if not self._nvidia:
            logger.warning("NVIDIA_API_KEY not found")

    def query(self, system: str, user: str, model: str = "fast", max_tokens: int = 4096) -> str:
        self._total_calls += 1

        try:
            if model == "fast":
                if not self._groq:
                    raise Exception("GROQ_API_KEY not configured")
                response = self._groq.chat.completions.create(
                    model=MODEL_FAST,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=0.2,
                    max_tokens=max_tokens,
                )
            else:
                if not self._nvidia:
                    raise Exception("NVIDIA_API_KEY not configured")
                response = self._nvidia.chat.completions.create(
                    model=MODEL_STRONG,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    temperature=0.2,
                    max_tokens=max_tokens,
                )

            return response.choices[0].message.content

        except Exception as exc:
            logger.error(f"[llm] API error: {exc}")
            raise

    def stats(self) -> dict:
        return {"total_calls": self._total_calls}