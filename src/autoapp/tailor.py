"""Step 3: tailor the CV and write the cover letter, then check both against the style rules."""
from __future__ import annotations

import json
from datetime import date

from .llm import LLM
from .models import Job, Profile
from .style import lint, numbers_in, rules_text, sanitize

MAX_FIX_ROUNDS = 2


def _all_text(obj) -> str:
    if isinstance(obj, str):
        return obj
    if isinstance(obj, dict):
        return "\n".join(_all_text(v) for v in obj.values())
    if isinstance(obj, list):
        return "\n".join(_all_text(v) for v in obj)
    return ""


def _clean(obj):
    if isinstance(obj, str):
        return sanitize(obj)
    if isinstance(obj, dict):
        return {k: _clean(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [_clean(v) for v in obj]
    return obj


def _generate_checked(llm: LLM, system: str, user: str, known: set[str]) -> tuple[dict, list[str]]:
    """Generate, lint, ask for repairs, and finally sanitise. Returns content and leftover issues."""
    data = llm.json(system, user)
    for _ in range(MAX_FIX_ROUNDS):
        issues = lint(_all_text(data), known)
        if not issues:
            return data, []
        data = llm.json(system, user + "\n\nYOUR DRAFT:\n" + json.dumps(data, ensure_ascii=False)
                        + "\n\nRewrite the draft and fix every one of these problems. Keep what is good.\n- "
                        + "\n- ".join(sorted(set(issues))[:25]))
    data = _clean(data)
    return data, sorted(set(lint(_all_text(data), known)))


CV_SYSTEM = """You tailor a CV to one job. You only select, order and lightly reword facts that \
exist in the candidate profile. You never add employers, titles, dates, skills, numbers or results. \
Employer names, titles and dates are filled in by the program, so you only supply text.\n\n""" + rules_text()


def tailor_cv(llm: LLM, job: Job, profile: Profile, fit: dict, research: dict) -> tuple[dict, list[str]]:
    user = f"""JOB: {job.title} at {job.company}
{job.description[:6000]}

FIT NOTES
Strongest points: {fit.get('strongest_points')}
Keywords to use where true: {fit.get('keywords')}
Language: {fit.get('language', 'en')}

CANDIDATE PROFILE
{profile.as_text()}

Return JSON:
- "summary": 2 to 3 short sentences, a professional profile aimed at this job
- "skills": list of skills copied from the profile skills list, most relevant first, max 14
- "experience": list of {{"index": int (profile experience index), "bullets": [2 to 4 short bullets]}}.
  Keep every role, in the profile order. Reword bullets so the most relevant work comes first.
  Start bullets with a verb. No full stops needed at the end. Facts must stay true.
- "education": list of {{"index": int, "details": [0 to 2 short lines]}} using only profile details
Write in this language: {fit.get('language', 'en')}"""
    known = numbers_in(profile.as_text(), job.description)
    data, issues = _generate_checked(llm, CV_SYSTEM, user, known)
    allowed = {s.lower(): s for s in profile.skills}  # guard: no skills outside the profile
    data["skills"] = [allowed[s.lower()] for s in data.get("skills", []) if s.lower() in allowed]
    return data, issues


LETTER_SYSTEM = """You write a one page cover letter for a real person. It must sound like they wrote \
it themselves: specific, calm and honest. You only use facts from the profile and the research notes.\n\n""" + rules_text()


def write_letter(llm: LLM, job: Job, profile: Profile, fit: dict, research: dict) -> tuple[dict, list[str]]:
    lang = fit.get("language", "en")
    user = f"""JOB: {job.title} at {job.company} ({job.location})
{job.description[:6000]}

COMPANY RESEARCH
Overview: {research.get('overview')}
Role context: {research.get('role_context')}
Details that are safe to mention: {research.get('letter_hooks')}
Hiring contact: {research.get('contact') or 'unknown'}

FIT NOTES
Strongest points: {fit.get('strongest_points')}
Gaps (do not hide them, but do not dwell on them): {fit.get('gaps')}

CANDIDATE PROFILE
{profile.as_text()}

Write the letter in language: {lang}. Today is {date.today():%d %B %Y}.
Structure: opening (why this role and this employer, one concrete detail), one or two body paragraphs
that tie specific work from the profile to what the job asks for, a short close that suggests a conversation.
Total 220 to 300 words. No bullet points.

Return JSON:
- "salutation": e.g. "Dear Dr Meier," or "Dear Hiring Team," (German: "Sehr geehrte Frau Meier," or "Sehr geehrte Damen und Herren,"). Use a name only if the contact is known.
- "subject": short subject line, e.g. "Application for Research Associate"
- "paragraphs": list of 3 or 4 paragraph strings
- "closing": e.g. "Kind regards" or "Mit freundlichen Grüßen" """
    known = numbers_in(profile.as_text(), job.description, _all_text(research))
    return _generate_checked(llm, LETTER_SYSTEM, user, known)
