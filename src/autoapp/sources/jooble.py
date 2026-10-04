"""Jooble API (https://jooble.org/api/about). Free key on request. Aggregates many boards."""
from __future__ import annotations

from datetime import datetime

import requests

from ..models import Job, SearchPrefs
from ..web import UA
from .base import Source, strip_html, too_old


class Jooble(Source):
    name = "jooble"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def search(self, prefs: SearchPrefs) -> list[Job]:
        jobs: list[Job] = []
        for kw in prefs.keywords:
            for place in prefs.locations or [""]:
                r = requests.post(f"https://jooble.org/api/{self.api_key}",
                                  json={"keywords": kw, "location": place, "page": 1},
                                  headers={"User-Agent": UA}, timeout=20)
                r.raise_for_status()
                for it in r.json().get("jobs", []):
                    try:
                        posted = datetime.fromisoformat(it["updated"]) if it.get("updated") else None
                    except ValueError:
                        posted = None
                    if too_old(posted, prefs.max_age_days):
                        continue
                    jobs.append(Job(
                        source=self.name, title=it.get("title", ""), company=it.get("company", ""),
                        location=it.get("location", ""), url=it.get("link", ""),
                        description=strip_html(it.get("snippet", "")), posted_at=posted,
                        salary=it.get("salary", ""),
                    ))
        return jobs
