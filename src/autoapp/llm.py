"""Thin wrapper around the Anthropic SDK."""
from __future__ import annotations

import json
import re
from typing import Protocol

import anthropic

from .config import LLMSettings


class LLM(Protocol):
    def text(self, system: str, user: str, *, web_search: bool = False) -> str: ...
    def json(self, system: str, user: str, *, web_search: bool = False) -> dict: ...


def extract_json(raw: str) -> dict:
    raw = raw.strip()
    raw = re.sub(r"^```(?:json)?\s*|\s*```$", "", raw)
    start, end = raw.find("{"), raw.rfind("}")
    if start == -1 or end == -1:
        raise ValueError("no JSON object in model output")
    return json.loads(raw[start:end + 1])


class ClaudeLLM:
    def __init__(self, settings: LLMSettings):
        self.s = settings
        self.client = anthropic.Anthropic()

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

    def text(self, system: str, user: str, *, web_search: bool = False) -> str:
        tools = None
        if web_search and self.s.web_search:
            tools = [{"type": "web_search_20260209", "name": "web_search", "max_uses": 5}]
        try:
            return self._call(system, user, tools)
        except anthropic.BadRequestError:
            if not tools:
                raise
            return self._call(system, user, None)  # web search not enabled for this account

    def json(self, system: str, user: str, *, web_search: bool = False) -> dict:
        system += "\n\nReply with one JSON object only. No text before or after it."
        raw = self.text(system, user, web_search=web_search)
        try:
            return extract_json(raw)
        except ValueError:
            fix = self.text(system, user + "\n\nYour last reply was not valid JSON. Return only the JSON object.")
            return extract_json(fix)
