"""Adzuna job search API (https://developer.adzuna.com). Free key, covers DE, GB, US and more."""
from __future__ import annotations

from datetime import datetime

import requests

from ..models import Job, SearchPrefs
from ..web import UA
from .base import Source, strip_html


class Adzuna(Source):
    name = "adzuna"

    def __init__(self, app_id: str, app_key: str):
        self.app_id, self.app_key = app_id, app_key

    def search(self, prefs: SearchPrefs) -> list[Job]:
        jobs: list[Job] = []
        places = prefs.locations or [""]
        for country in prefs.countries:
            for kw in prefs.keywords:
                for place in places:
                    params = {
                        "app_id": self.app_id, "app_key": self.app_key,
                        "what": kw, "max_days_old": prefs.max_age_days,
                        "results_per_page": 30, "sort_by": "date",
                        "content-type": "application/json",
                    }
                    if place:
                        params["where"] = place
                    r = requests.get(
                        f"https://api.adzuna.com/v1/api/jobs/{country}/search/1",
                        params=params, headers={"User-Agent": UA}, timeout=20)
                    r.raise_for_status()
                    for it in r.json().get("results", []):
                        lo, hi = it.get("salary_min"), it.get("salary_max")
                        jobs.append(Job(
                            source=self.name, title=it.get("title", ""),
                            company=(it.get("company") or {}).get("display_name", ""),
                            location=(it.get("location") or {}).get("display_name", ""),
                            url=it.get("redirect_url", ""),
                            description=strip_html(it.get("description", "")),
                            posted_at=datetime.fromisoformat(it["created"].replace("Z", "+00:00"))
                            if it.get("created") else None,
                            salary=f"{int(lo)} to {int(hi)}" if lo and hi else "",
                        ))
        return jobs
