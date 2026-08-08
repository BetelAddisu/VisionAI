"""LLM provider for the planner.

Default is "none". An optional OpenAI-compatible HTTP provider supports any
local server (llama.cpp server, Ollama, LM Studio, vLLM, etc.) so the
planner can use a real local LLM without hard-coding a single backend.
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request

from backend.ai.base import LLMProvider, LLMResponse
from backend.config import Settings, get_settings
from backend.logging import get_logger

log = get_logger("llm")


class NoneLLMProvider(LLMProvider):
    @property
    def available(self) -> bool:
        return False

    @property
    def model_version(self) -> str:
        return "none"

    def generate(self, system_prompt: str, user_prompt: str,
                 *, max_tokens: int = 2048, temperature: float = 0.3) -> LLMResponse:
        return LLMResponse(text="", valid=False,
                           error="No LLM provider configured")


class OpenAICompatibleProvider(LLMProvider):
    """Talks to an OpenAI-compatible /v1/chat/completions endpoint (local).

    Reads base_url and api_key from settings.models.llm (model field is the
    model name; an optional extra field ``base_url`` may be supplied via the
    LLM config). Works fully offline when pointed at a local server.
    """

    def __init__(self, base_url: str, model: str, api_key: str = "none",
                 timeout: int = 120) -> None:
        self._base_url = base_url.rstrip("/")
        self._model = model
        self._api_key = api_key
        self._timeout = timeout

    @property
    def available(self) -> bool:
        return bool(self._base_url and self._model)

    @property
    def model_version(self) -> str:
        return f"openai-compat:{self._model}"

    def generate(self, system_prompt: str, user_prompt: str,
                 *, max_tokens: int = 2048, temperature: float = 0.3) -> LLMResponse:
        payload = {
            "model": self._model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self._base_url}/v1/chat/completions",
            data=data,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self._api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=self._timeout) as resp:
                body = json.loads(resp.read().decode("utf-8"))
            text = body["choices"][0]["message"]["content"]
            return LLMResponse(text=text, valid=True)
        except (urllib.error.URLError, KeyError, ValueError, TimeoutError) as exc:
            log.error("LLM request failed", extra={"error": str(exc)})
            return LLMResponse(text="", valid=False, error=str(exc))


def get_llm_provider(settings: Settings | None = None) -> LLMProvider:
    settings = settings or get_settings()
    cfg = settings.models.llm
    if cfg.provider == "openai-compatible":
        if not cfg.base_url:
            return NoneLLMProvider()
        return OpenAICompatibleProvider(
            base_url=cfg.base_url, model=cfg.model, api_key=cfg.api_key or "none")
    return NoneLLMProvider()
