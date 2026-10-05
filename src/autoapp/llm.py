"""Model providers. Claude is the default. Llama and other models work through Ollama or any
OpenAI compatible service (Groq, OpenRouter, Gemini, xAI)."""
from __future__ import annotations

import json
import os
import re
import time
from typing import Protocol

import requests

from .config import LLMSettings


class LLM(Protocol):
    can_search: bool

    def text(self, system: str, user: str, *, web_search: bool = False) -> str: ...
    def json(self, system: str, user: str, *, web_search: bool = False) -> dict: ...


# provider: (base_url, api key variable, default model)
PRESETS: dict[str, tuple[str, str, str]] = {
    "anthropic": ("", "ANTHROPIC_API_KEY", "claude-opus-5-5"),
    "ollama": ("http://localhost:11434", "", "llama3.1:8b"),
    "groq": ("https://api.groq.com/openai/v1", "GROQ_API_KEY", "llama-3.3-70b-versatile"),
    "openrouter": ("https://openrouter.ai/api/v1", "OPENROUTER_API_KEY",
                   "meta-llama/llama-3.3-70b-instruct:free"),
    "gemini": ("https://generativelanguage.googleapis.com/v1beta/openai", "GEMINI_API_KEY",
               "gemini-2.5-flash"),
    "xai": ("https://api.x.ai/v1", "XAI_API_KEY", ""),  # Grok model names change, set llm.model
    "openai_compatible": ("", "LLM_API_KEY", ""),
}


def extract_json(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in model output")
    return json.loads(raw[start:end + 1])


def make_llm(s: LLMSettings) -> LLM:
    if s.provider not in PRESETS:
        raise RuntimeError(f"Unknown llm.provider '{s.provider}'. Choose one of: {', '.join(PRESETS)}")
    base, key_env, model = PRESETS[s.provider]
    s = s.model_copy(update={"base_url": s.base_url or base, "api_key_env": s.api_key_env or key_env,
                             "model": s.model or model})
    if not s.model:
        raise RuntimeError(f"Set llm.model in config.yaml for provider '{s.provider}'. "
                           "Check the provider's model list for the exact name.")
    if s.provider == "anthropic":
        return ClaudeLLM(s)
    if s.provider == "ollama":
        return OllamaLLM(s)
    if not s.base_url:
        raise RuntimeError("Set llm.base_url in config.yaml for provider 'openai_compatible'.")
    key = os.getenv(s.api_key_env) if s.api_key_env else ""
    if s.api_key_env and not key:
        raise RuntimeError(f"Set the {s.api_key_env} environment variable (your {s.provider} API key).")
    return OpenAICompatLLM(s, key or "")


class _JsonMixin:
    """JSON output with one retry. Smaller models slip more often, so this matters."""

    def json(self, system: str, user: str, *, web_search: bool = False) -> dict:
        system += "\n\nReply with one JSON object only. No text before or after it."
        try:
            return extract_json(self._complete(system, user, as_json=True, web_search=web_search))
        except ValueError:
            fix = self._complete(system, user + "\n\nYour last reply was not valid JSON. "
                                 "Return only the JSON object.", as_json=True, web_search=False)
            return extract_json(fix)

    def text(self, system: str, user: str, *, web_search: bool = False) -> str:
        return self._complete(system, user, as_json=False, web_search=web_search)


class ClaudeLLM(_JsonMixin):
    def __init__(self, settings: LLMSettings):
        import anthropic
        self.s = settings
        self.client = anthropic.Anthropic()

    @property
    def can_search(self) -> bool:
        return self.s.web_search

    def _call(self, system: str, user: str, tools: list[dict] | None) -> str:
        messages = [{"role": "user", "content": user}]
        kwargs = dict(model=self.s.model, max_tokens=self.s.max_tokens, system=system,
                      output_config={"effort": self.s.effort})
        if tools:
            kwargs["tools"] = tools
        for _ in range(4):  # server-side web search can pause long turns; resume them
            resp = self.client.messages.create(messages=messages, **kwargs)
            if resp.stop_reason == "refusal":
                raise RuntimeError("The model declined this request.")
            if resp.stop_reason != "pause_turn":
                break
            messages = [messages[0], {"role": "assistant", "content": resp.content}]
        return "".join(b.text for b in resp.content if b.type == "text")

    def _complete(self, system: str, user: str, *, as_json: bool, web_search: bool) -> str:
        import anthropic
        tools = None
        if web_search and self.s.web_search:
            tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 5}]
        try:
            return self._call(system, user, tools)
        except anthropic.BadRequestError:
            if not tools:
                raise
            return self._call(system, user, None)  # web search not enabled for this account


def _post(url: str, payload: dict, headers: dict, timeout: int, tries: int = 5) -> requests.Response:
    """POST with patient retries. Free tiers answer 429 when you go over the per minute limit."""
    for attempt in range(tries):
        r = requests.post(url, json=payload, headers=headers, timeout=timeout)
        if r.status_code not in (429, 500, 502, 503, 504) or attempt == tries - 1:
            return r
        wait = r.headers.get("retry-after", "")
        delay = float(wait) if wait.replace(".", "", 1).isdigit() else min(60, 5 * 2 ** attempt)
        print(f"  provider is busy or rate limited, waiting {delay:.0f}s ...")
        time.sleep(min(delay, 90))
    return r  # pragma: no cover


class OpenAICompatLLM(_JsonMixin):
    """Groq, OpenRouter, Gemini, xAI and any other service with an OpenAI style chat endpoint."""
    can_search = False

    def __init__(self, settings: LLMSettings, api_key: str):
        self.s, self.key = settings, api_key

    def _complete(self, system: str, user: str, *, as_json: bool, web_search: bool) -> str:
        payload = {"model": self.s.model, "max_tokens": self.s.max_tokens,
                   "messages": [{"role": "system", "content": system},
                                {"role": "user", "content": user}]}
        if as_json:
            payload["response_format"] = {"type": "json_object"}
        headers = {"Authorization": f"Bearer {self.key}"} if self.key else {}
        url = self.s.base_url.rstrip("/") + "/chat/completions"
        r = _post(url, payload, headers, timeout=300)
        if r.status_code == 400 and as_json:  # some models do not accept response_format
            payload.pop("response_format")
            r = _post(url, payload, headers, timeout=300)
        if r.status_code in (401, 403):
            raise RuntimeError(f"{self.s.provider} rejected the API key ({self.s.api_key_env}).")
        if r.status_code == 404:
            raise RuntimeError(f"{self.s.provider} does not know the model '{self.s.model}'. "
                               "Check the model name in config.yaml.")
        if not r.ok:
            raise RuntimeError(f"{self.s.provider} error {r.status_code}: {r.text[:200]}")
        return r.json()["choices"][0]["message"]["content"] or ""


class OllamaLLM(_JsonMixin):
    """Local models through Ollama. Free, private, runs on your computer."""
    can_search = False

    def __init__(self, settings: LLMSettings):
        self.s = settings

    def _complete(self, system: str, user: str, *, as_json: bool, web_search: bool) -> str:
        # Ollama's default context is only 4096 tokens on most computers. A CV prompt needs more.
        payload = {"model": self.s.model, "stream": False,
                   "messages": [{"role": "system", "content": system},
                                {"role": "user", "content": user}],
                   "options": {"num_ctx": self.s.num_ctx, "num_predict": self.s.max_tokens}}
        if as_json:
            payload["format"] = "json"
        try:
            r = requests.post(self.s.base_url.rstrip("/") + "/api/chat", json=payload, timeout=900)
        except requests.ConnectionError:
            raise RuntimeError("Ollama is not running. Open the Ollama app, or run 'ollama serve' "
                               "in another terminal, then try again.") from None
        if r.status_code == 404:
            raise RuntimeError(f"Model '{self.s.model}' is not installed. Run: ollama pull {self.s.model}")
        if not r.ok:
            raise RuntimeError(f"Ollama error {r.status_code}: {r.text[:200]}")
        return r.json()["message"]["content"]
