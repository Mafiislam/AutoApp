"""Fast, transparent job scoring. No LLM needed. The detailed fit check comes later."""
from __future__ import annotations

import re
from datetime import datetime, timezone

from .models import Job, Profile


def _has(term: str, text: str) -> bool:
    pat = r"(?<![\w+#])" + re.escape(term.lower()) + r"(?![\w+#])"
    return re.search(pat, text) is not None


def score_job(job: Job, profile: Profile) -> Job:
    prefs = profile.search
    text = f"{job.title}\n{job.description}".lower()
    title = job.title.lower()

    if any(_has(x, title) for x in prefs.exclude_keywords):
        job.score, job.score_notes = 0.0, "excluded by keyword"
        return job

    matched = [s for s in profile.skills if _has(s, text)]
    skills = min(1.0, len(matched) / max(3, min(8, len(profile.skills))))

    kw_hits = [k for k in prefs.keywords if _has(k, title)]
    title_score = 1.0 if kw_hits else (
        0.5 if any(_has(k, text) for k in prefs.keywords) else 0.0)

    interests = [i for i in profile.interests if _has(i, text)]
    interest_score = min(1.0, len(interests) / 2)

    loc = job.location.lower()
    if prefs.remote_ok and ("remote" in loc or "remote" in text[:600]):
        loc_score = 1.0
    elif not prefs.locations:
        loc_score = 0.5
    else:
        loc_score = 1.0 if any(p.lower() in loc for p in prefs.locations) else 0.0

    if job.posted_at:
        posted = job.posted_at if job.posted_at.tzinfo else job.posted_at.replace(tzinfo=timezone.utc)
        age = (datetime.now(timezone.utc) - posted).total_seconds() / 86400
        recency = max(0.0, 1 - age / max(1, prefs.max_age_days))
    else:
        recency = 0.5

    job.score = round(100 * (0.45 * skills + 0.25 * title_score + 0.10 * interest_score
                             + 0.10 * loc_score + 0.10 * recency), 1)
    job.score_notes = (f"skills: {', '.join(matched) or 'none'}; title match: {bool(kw_hits)}; "
                       f"interests: {', '.join(interests) or 'none'}")
    return job


def rank(jobs: list[Job], profile: Profile) -> list[Job]:
    scored = [score_job(j, profile) for j in jobs]
    return sorted(scored, key=lambda j: j.score, reverse=True)
