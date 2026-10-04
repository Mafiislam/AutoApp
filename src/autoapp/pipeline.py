"""The full flow for one job: research, fit check, tailored CV and cover letter, saved to a folder."""
from __future__ import annotations

import json
import re
from datetime import date
from pathlib import Path

from .config import Settings
from .llm import LLM
from .matching import rank
from .models import Job, Profile
from .render import letter_text, write_cv, write_letter_docx
from .research import analyse_fit, fit_markdown, research_company, research_markdown
from .sources import Source, discover
from .store import Store
from .tailor import tailor_cv, write_letter
from .web import fetch_html, html_to_text, jsonld_job
from .sources.base import strip_html


def slug(text: str, n: int = 40) -> str:
    s = re.sub(r"[^\w]+", "_", text, flags=re.UNICODE).strip("_")
    return s[:n] or "job"


def enrich(job: Job) -> Job:
    """Adzuna and Jooble return only a snippet. Try to read the full advert from the public page."""
    if len(job.description) > 1200 or not job.url:
        return job
    html = fetch_html(job.url)
    if not html:
        return job
    ld = jsonld_job(html)
    full = strip_html(ld.get("description", "")) if ld else html_to_text(html, 8000)
    if len(full) > len(job.description):
        job.description = full
    return job


def find_jobs(sources: list[Source], profile: Profile, store: Store | None = None) -> list[Job]:
    jobs = discover(sources, profile)
    if store:
        jobs = [j for j in jobs if not store.known(j.id)]
    return [j for j in rank(jobs, profile) if j.score >= profile.search.min_score]


def process_job(job: Job, profile: Profile, settings: Settings, llm: LLM,
                store: Store | None = None, force: bool = False) -> Path | None:
    job = enrich(job)
    print(f"  researching {job.company or 'the company'} ...")
    research = research_company(llm, job)
    print("  comparing advert and profile ...")
    fit = analyse_fit(llm, job, profile, research)
    job_label = f"{job.title} at {job.company}"

    if not fit.get("should_apply", True) and not force:
        print(f"  skipped (fit {fit.get('match_score')}): {fit.get('reason', '')}")
        if store:
            store.save(job, "skipped")
        return None

    lang = fit.get("language", "en")
    print("  tailoring CV ...")
    cv, cv_issues = tailor_cv(llm, job, profile, fit, research)
    print("  writing cover letter ...")
    letter, letter_issues = write_letter(llm, job, profile, fit, research)

    folder = Path(settings.output_dir) / f"{date.today():%Y-%m-%d}_{slug(job.company)}_{slug(job.title)}"
    folder.mkdir(parents=True, exist_ok=True)
    who = slug(profile.name, 30)
    write_cv(folder / f"CV_{who}.docx", profile, cv, lang)
    write_letter_docx(folder / f"CoverLetter_{who}.docx", profile, job.company, letter, lang)
    (folder / "CoverLetter.txt").write_text(letter_text(profile, job.company, letter, lang), encoding="utf-8")
    (folder / "company_research.md").write_text(research_markdown(job, research), encoding="utf-8")
    (folder / "fit_analysis.md").write_text(fit_markdown(job, fit), encoding="utf-8")
    (folder / "job_description.txt").write_text(
        f"{job_label}\n{job.location}\n{job.url}\n\n{job.description}", encoding="utf-8")
    (folder / "job.json").write_text(job.model_dump_json(indent=2), encoding="utf-8")

    issues = [f"CV: {i}" for i in cv_issues] + [f"Letter: {i}" for i in letter_issues]
    (folder / "README.md").write_text(_readme(job, fit, issues), encoding="utf-8")
    if store:
        store.save(job, "prepared", str(folder))
    print(f"  saved to {folder}")
    return folder


def _readme(job: Job, fit: dict, issues: list[str]) -> str:
    todo = "\n".join(f"- [ ] Fix: {i}" for i in issues) or "- [x] Style check passed"
    return f"""# {job.title} at {job.company}

Match score: {fit.get('match_score')} / 100. {fit.get('reason', '')}

Apply here: {job.url}

## Before you send
- [ ] Read the CV and the cover letter once, out loud. Change anything that does not sound like you.
- [ ] Check every date, title and number against your real record.
- [ ] Read `company_research.md` and `fit_analysis.md`. Check the claims you plan to repeat.
- [ ] Convert the Word files to PDF if the employer asks for PDF.
{todo}
"""


def run(profile: Profile, settings: Settings, sources: list[Source], llm: LLM | None,
        store: Store, limit: int | None = None, dry_run: bool = False) -> list[Path]:
    jobs = find_jobs(sources, profile, store)
    limit = limit or settings.max_applications_per_run
    print(f"{len(jobs)} new matching jobs. Showing the top {min(limit, len(jobs))}.\n")
    for j in jobs[:limit]:
        print(f"{j.score:5.1f}  {j.title} | {j.company} | {j.location} | {j.url}")
    if dry_run or llm is None:
        return []
    out = []
    for j in jobs[:limit]:
        print(f"\n== {j.title} at {j.company} ({j.score})")
        try:
            folder = process_job(j, profile, settings, llm, store)
        except Exception as exc:
            print(f"  failed: {exc}")
            store.save(j, "failed")
            continue
        if folder:
            out.append(folder)
    return out
