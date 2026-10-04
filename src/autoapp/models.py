"""Data models for the user's profile and for job postings."""
from __future__ import annotations

import hashlib
from datetime import datetime
from pathlib import Path

import yaml
from pydantic import BaseModel, Field


class Experience(BaseModel):
    title: str
    company: str
    location: str = ""
    start: str = ""
    end: str = "present"
    bullets: list[str] = Field(default_factory=list)


class Education(BaseModel):
    degree: str
    institution: str
    location: str = ""
    start: str = ""
    end: str = ""
    details: list[str] = Field(default_factory=list)


class SearchPrefs(BaseModel):
    keywords: list[str] = Field(default_factory=list)
    locations: list[str] = Field(default_factory=list)
    countries: list[str] = Field(default_factory=lambda: ["de"])
    max_age_days: int = 7
    remote_ok: bool = True
    min_score: float = 45.0
    exclude_keywords: list[str] = Field(default_factory=list)


class Profile(BaseModel):
    name: str
    email: str
    phone: str = ""
    location: str = ""
    links: list[str] = Field(default_factory=list)
    headline: str = ""
    summary: str = ""
    skills: list[str] = Field(default_factory=list)
    languages: list[str] = Field(default_factory=list)
    experience: list[Experience] = Field(default_factory=list)
    education: list[Education] = Field(default_factory=list)
    interests: list[str] = Field(default_factory=list)
    extra_sections: dict[str, list[str]] = Field(default_factory=dict)
    search: SearchPrefs = Field(default_factory=SearchPrefs)

    @classmethod
    def load(cls, path: str | Path) -> "Profile":
        with open(path, encoding="utf-8") as fh:
            return cls.model_validate(yaml.safe_load(fh))

    def as_text(self) -> str:
        """Plain text version of the profile. Indices let the model refer to entries."""
        lines = [f"Name: {self.name}", f"Location: {self.location}"]
        if self.headline:
            lines.append(f"Headline: {self.headline}")
        if self.summary:
            lines.append(f"Summary: {self.summary}")
        lines.append("Skills: " + ", ".join(self.skills))
        if self.languages:
            lines.append("Languages: " + ", ".join(self.languages))
        lines.append("Interests: " + ", ".join(self.interests))
        lines.append("\nEXPERIENCE")
        for i, e in enumerate(self.experience):
            lines.append(f"[{i}] {e.title}, {e.company} ({e.start} to {e.end})")
            lines += [f"    - {b}" for b in e.bullets]
        lines.append("\nEDUCATION")
        for i, e in enumerate(self.education):
            lines.append(f"[{i}] {e.degree}, {e.institution} ({e.start} to {e.end})")
            lines += [f"    - {d}" for d in e.details]
        for title, items in self.extra_sections.items():
            lines.append(f"\n{title.upper()}")
            lines += [f"    - {x}" for x in items]
        return "\n".join(lines)


class Job(BaseModel):
    id: str = ""
    source: str
    title: str
    company: str = ""
    location: str = ""
    url: str = ""
    description: str = ""
    posted_at: datetime | None = None
    salary: str = ""
    company_url: str = ""
    score: float = 0.0
    score_notes: str = ""

    def model_post_init(self, _ctx) -> None:
        if not self.id:
            key = f"{self.source}|{self.url or (self.title + self.company)}"
            self.id = hashlib.sha1(key.encode()).hexdigest()[:12]
