"""Infrastructure settings (API keys come from environment variables, never from files)."""
from __future__ import annotations

from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class LLMSettings(BaseModel):
    # anthropic | ollama | groq | openrouter | gemini | xai | openai_compatible
    provider: str = "anthropic"
    model: str = ""          # empty means the provider's default model
    effort: str = "medium"   # Claude only
    web_search: bool = True  # Claude only: lets the model search the web while researching a company
    max_tokens: int = 8000
    base_url: str = ""       # only needed for openai_compatible, or to override a preset
    api_key_env: str = ""    # name of the environment variable that holds the key
    num_ctx: int = 16384     # Ollama only: context window in tokens


class AdzunaSettings(BaseModel):
    enabled: bool = True
    app_id_env: str = "ADZUNA_APP_ID"
    app_key_env: str = "ADZUNA_APP_KEY"


class JoobleSettings(BaseModel):
    enabled: bool = False
    api_key_env: str = "JOOBLE_API_KEY"


class ArbeitnowSettings(BaseModel):
    enabled: bool = True


class Sources(BaseModel):
    adzuna: AdzunaSettings = Field(default_factory=AdzunaSettings)
    jooble: JoobleSettings = Field(default_factory=JoobleSettings)
    arbeitnow: ArbeitnowSettings = Field(default_factory=ArbeitnowSettings)


class Settings(BaseModel):
    llm: LLMSettings = Field(default_factory=LLMSettings)
    sources: Sources = Field(default_factory=Sources)
    output_dir: str = "applications"
    db_path: str = "data/autoapp.db"
    max_applications_per_run: int = 5

    @classmethod
    def load(cls, path: str | Path | None) -> "Settings":
        if path and Path(path).exists():
            with open(path, encoding="utf-8") as fh:
                return cls.model_validate(yaml.safe_load(fh) or {})
        return cls()
