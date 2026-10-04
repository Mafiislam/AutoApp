from __future__ import annotations

import os

from ..config import Settings
from ..models import Job, Profile
from .adzuna import Adzuna
from .arbeitnow import Arbeitnow
from .base import Source
from .jooble import Jooble
from .manual import job_from_file, job_from_url

__all__ = ["Source", "build_sources", "discover", "job_from_file", "job_from_url"]


def build_sources(settings: Settings) -> list[Source]:
    s = settings.sources
    out: list[Source] = []
    if s.adzuna.enabled:
        app_id, app_key = os.getenv(s.adzuna.app_id_env), os.getenv(s.adzuna.app_key_env)
        if app_id and app_key:
            out.append(Adzuna(app_id, app_key))
        else:
            print(f"[skip] Adzuna: set {s.adzuna.app_id_env} and {s.adzuna.app_key_env}")
    if s.jooble.enabled:
        key = os.getenv(s.jooble.api_key_env)
        if key:
            out.append(Jooble(key))
        else:
            print(f"[skip] Jooble: set {s.jooble.api_key_env}")
    if s.arbeitnow.enabled:
        out.append(Arbeitnow())
    return out


def discover(sources: list[Source], profile: Profile) -> list[Job]:
    jobs: dict[str, Job] = {}
    for src in sources:
        try:
            for job in src.search(profile.search):
                key = (job.title.lower().strip(), job.company.lower().strip())
                jobs.setdefault(str(key), job)
        except Exception as exc:  # one broken source must not stop the run
            print(f"[warn] {src.name} failed: {exc}")
    return list(jobs.values())
