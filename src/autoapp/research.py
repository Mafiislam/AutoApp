"""Step 1: research the company. Step 2: compare the advert with the user's profile."""
from __future__ import annotations

from urllib.parse import quote

import requests

from .llm import LLM
from .models import Job, Profile
from .web import UA, fetch_text


def _wikipedia(company: str) -> str:
    for lang in ("en", "de"):
        try:
            r = requests.get(
                f"https://{lang}.wikipedia.org/api/rest_v1/page/summary/{quote(company.replace(' ', '_'))}",
                headers={"User-Agent": UA}, timeout=10)
            if r.ok and r.json().get("type") == "standard":
                return r.json().get("extract", "")
        except requests.RequestException:
            pass
    return ""


def gather_context(job: Job) -> str:
    parts = []
    if job.company_url:
        parts.append("COMPANY WEBSITE:\n" + fetch_text(job.company_url, 5000))
    wiki = _wikipedia(job.company) if job.company else ""
    if wiki:
        parts.append("WIKIPEDIA SUMMARY:\n" + wiki)
    return "\n\n".join(p for p in parts if p.strip())


RESEARCH_SYSTEM = """You are a careful researcher helping a job applicant prepare. \
Research the employer and the role. Use web search when it is available. \
Report only what you can support. If you cannot find something, write "not found". \
Do not guess about size, funding, culture or news. Keep each field short and plain."""


def research_company(llm: LLM, job: Job) -> dict:
    user = f"""Company: {job.company}
Role: {job.title}
Location: {job.location}
Company website (if known): {job.company_url or 'unknown'}

JOB ADVERT:
{job.description[:6000]}

PAGES ALREADY FETCHED:
{gather_context(job) or 'none'}

Return JSON with these keys:
- "overview": what the organisation does, sector, rough size and location (2 to 3 sentences)
- "culture_and_values": what they say about how they work (1 to 3 sentences, or "not found")
- "recent_developments": recent projects, products, funding or news with dates (list of short strings, may be empty)
- "role_context": what the team likely does and why this role exists, based on the advert
- "letter_hooks": 2 to 4 specific, true details an applicant could mention to show real interest
- "cautions": anything an applicant should check (unclear employer, contract type, language needs, red flags)
- "contact": hiring contact name and title if the advert names one, else ""
- "sources": list of URLs you relied on"""
    return llm.json(RESEARCH_SYSTEM, user, web_search=True)


def research_markdown(job: Job, r: dict) -> str:
    def bullets(v):
        return "\n".join(f"- {x}" for x in v) if isinstance(v, list) and v else "- not found"
    return f"""# Company research: {job.company}

**Role:** {job.title}  
**Location:** {job.location}  
**Advert:** {job.url}

## Overview
{r.get('overview', 'not found')}

## Culture and values
{r.get('culture_and_values', 'not found')}

## Recent developments
{bullets(r.get('recent_developments'))}

## About the role
{r.get('role_context', '')}

## Points worth mentioning in the letter
{bullets(r.get('letter_hooks'))}

## Check before applying
{r.get('cautions', 'nothing flagged')}

## Sources
{bullets(r.get('sources'))}
"""


FIT_SYSTEM = """You are a senior academic and industry career advisor. Compare a job advert with \
a candidate profile. Be honest and specific. Never credit the candidate with anything that is \
not in the profile."""


def analyse_fit(llm: LLM, job: Job, profile: Profile, research: dict) -> dict:
    user = f"""JOB: {job.title} at {job.company} ({job.location})
{job.description[:7000]}

COMPANY NOTES:
{research.get('overview', '')} {research.get('role_context', '')}

CANDIDATE PROFILE:
{profile.as_text()}

Return JSON with these keys:
- "match_score": integer 0 to 100, how well the candidate fits
- "should_apply": true or false
- "reason": one or two plain sentences explaining the score
- "language": "en" or "de", the language the application should be written in (the advert's language, unless it asks otherwise)
- "requirements": list of objects {{"requirement": str, "evidence": str (from the profile, or ""), "strength": "strong" | "partial" | "gap"}}
- "strongest_points": 3 to 5 short strings, the best things from the profile to stress for this job
- "gaps": short strings for requirements the profile does not cover
- "keywords": important terms from the advert that truthfully describe the candidate and belong in the CV"""
    return llm.json(FIT_SYSTEM, user)


def fit_markdown(job: Job, f: dict) -> str:
    rows = "\n".join(
        f"| {r.get('requirement', '')} | {r.get('strength', '')} | {r.get('evidence', '')} |"
        for r in f.get("requirements", []))
    gaps = "\n".join(f"- {g}" for g in f.get("gaps", [])) or "- none"
    best = "\n".join(f"- {g}" for g in f.get("strongest_points", []))
    return f"""# Fit analysis: {job.title} at {job.company}

**Match score:** {f.get('match_score')} / 100  
**Recommendation:** {'apply' if f.get('should_apply') else 'think twice'}  
{f.get('reason', '')}

## Strongest points
{best}

## Requirements against evidence
| Requirement | Fit | Evidence |
|---|---|---|
{rows}

## Gaps
{gaps}
"""
