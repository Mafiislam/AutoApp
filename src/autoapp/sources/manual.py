"""Add a single job yourself: a URL, or a text file. This is the route for LinkedIn,
Indeed and StepStone, whose terms do not allow automated search or scraping."""
from __future__ import annotations

from datetime import datetime
from pathlib import Path

from ..models import Job
from ..web import fetch_html, html_to_text, jsonld_job
from .base import strip_html


def job_from_url(url: str) -> Job:
    html = fetch_html(url)
    ld = jsonld_job(html) if html else None
    if ld:
        org = ld.get("hiringOrganization") or {}
        loc = ld.get("jobLocation") or {}
        if isinstance(loc, list):
            loc = loc[0] if loc else {}
        addr = (loc.get("address") or {}) if isinstance(loc, dict) else {}
        try:
            posted = datetime.fromisoformat(str(ld.get("datePosted", "")).replace("Z", "+00:00"))
        except ValueError:
            posted = None
        return Job(source="manual", title=ld.get("title", ""),
                   company=org.get("name", "") if isinstance(org, dict) else str(org),
                   location=addr.get("addressLocality", "") if isinstance(addr, dict) else "",
                   url=url, description=strip_html(ld.get("description", "")), posted_at=posted,
                   company_url=org.get("sameAs", "") if isinstance(org, dict) else "")
    if html:
        return Job(source="manual", title="", url=url, description=html_to_text(html))
    raise RuntimeError(
        "The page could not be read (it may need a login or block automated access). "
        "Copy the job text into a file and use: autoapp apply-file FILE")


def job_from_file(path: str | Path) -> Job:
    """Text file format. Optional header lines, then a blank line, then the advert:

        Title: Research Associate
        Company: Example GmbH
        Location: Berlin
        URL: https://...
    """
    raw = Path(path).read_text(encoding="utf-8")
    head, _, body = raw.partition("\n\n")
    meta: dict[str, str] = {}
    for line in head.splitlines():
        if ":" in line:
            k, v = line.split(":", 1)
            meta[k.strip().lower()] = v.strip()
    if not meta.get("title"):  # no header at all: whole file is the advert
        body = raw
    return Job(source="manual", title=meta.get("title", ""), company=meta.get("company", ""),
               location=meta.get("location", ""), url=meta.get("url", ""),
               company_url=meta.get("company_url", ""), description=body.strip())
