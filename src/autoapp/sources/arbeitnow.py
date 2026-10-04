"""Arbeitnow public job board API (no key needed, strong on German and EU roles)."""
from __future__ import annotations

from datetime import datetime, timezone

import requests

from ..models import Job, SearchPrefs
from ..web import UA
from .base import Source, strip_html, too_old


class Arbeitnow(Source):
    name = "arbeitnow"

    def search(self, prefs: SearchPrefs) -> list[Job]:
        r = requests.get("https://www.arbeitnow.com/api/job-board-api",
                         headers={"User-Agent": UA}, timeout=20)
        r.raise_for_status()
        wanted = [k.lower() for k in prefs.keywords]
        jobs: list[Job] = []
        for it in r.json().get("data", []):
            posted = datetime.fromtimestamp(it["created_at"], tz=timezone.utc) if it.get("created_at") else None
            if too_old(posted, prefs.max_age_days):
                continue
            blob = f"{it.get('title', '')} {' '.join(it.get('tags', []))} {it.get('description', '')}".lower()
            if wanted and not any(k in blob for k in wanted):
                continue
            jobs.append(Job(
                source=self.name, title=it.get("title", ""), company=it.get("company_name", ""),
                location=("Remote, " if it.get("remote") else "") + it.get("location", ""),
                url=it.get("url", ""), description=strip_html(it.get("description", "")),
                posted_at=posted,
            ))
        return jobs
