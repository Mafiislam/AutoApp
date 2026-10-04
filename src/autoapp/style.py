"""Writing rules for generated documents, plus a linter that checks the output against them."""
from __future__ import annotations

import re

STYLE_RULES = """\
WRITING RULES (follow all of them)
- Plain Oxford English (or plain German when the job advert is in German). Simple, common words.
- Short sentences. Aim for 8 to 18 words. Never go above 25 words.
- Never use dashes of any kind: no em dash, no en dash, no spaced hyphen. Write "2019 to 2022", not "2019-2022".
- Never start a sentence with "This" or "These".
- Do not start more than two sentences in a row with "I".
- No exclamation marks.
- Do not use these words or phrases: {banned}.
- Do not open the letter with "I am writing to apply", "I am excited", "I am thrilled" or similar.
- Say concrete things. Name a real project, tool, result or detail from the profile. Skip empty praise of the company.
- Sound like a capable person writing to another person. Calm, direct, a little warm. No hype, no slogans.
- Vary sentence shape and length a little. Do not use lists of three adjectives or "not only X but also Y".
- Use only facts found in the profile. Never invent employers, dates, tools, numbers, degrees or results.
  If the job needs something the profile lacks, leave it out or mention the willingness to learn it once, honestly.
"""

BANNED_WORDS = [
    "highlighting", "highlight", "leverage", "leveraging", "delve", "passionate", "dynamic",
    "thrilled", "excited", "proven track record", "testament", "tapestry", "fast-paced",
    "synergy", "synergies", "spearhead", "cutting-edge", "cutting edge", "in today's",
    "robust", "seamless", "seamlessly", "unlock", "foster", "fostering", "realm",
    "underscore", "underscores", "pivotal", "crucial", "multifaceted", "landscape",
    "game-changer", "ever-evolving", "navigate", "embark", "showcase", "elevate",
    "enhance", "streamline", "utilize", "utilise", "commendable", "meticulous",
    "i am writing to express", "i am writing to apply", "i would like to apply",
    "look forward to the opportunity", "dream job", "team player", "results-driven",
    "detail-oriented", "hit the ground running", "valuable asset", "wealth of experience",
    # German clichés
    "hiermit bewerbe ich mich", "mit großer begeisterung", "dynamisch", "teamplayer",
]

_DASHES = re.compile(r"[‒–—―−]|(?<=\s)-(?=\s)|--")


def rules_text() -> str:
    return STYLE_RULES.format(banned=", ".join(f'"{w}"' for w in BANNED_WORDS[:40]))


def _sentences(text: str) -> list[str]:
    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    return [p.strip() for p in parts if p.strip()]


def lint(text: str, known_numbers: set[str] | None = None) -> list[str]:
    """Returns a list of human readable problems. Empty list means clean."""
    issues: list[str] = []
    if _DASHES.search(text):
        issues.append("contains a dash (use a comma, a full stop or the word 'to')")
    low = text.lower()
    for w in BANNED_WORDS:
        if re.search(r"(?<!\w)" + re.escape(w) + r"(?!\w)", low):
            issues.append(f"uses banned word or phrase: '{w}'")
    if "!" in text:
        issues.append("contains an exclamation mark")
    run = 0
    for s in _sentences(text):
        if re.match(r"(this|these)\b", s, re.I):
            issues.append(f"sentence starts with 'This/These': '{s[:50]}'")
        n = len(s.split())
        if n > 25:
            issues.append(f"sentence has {n} words, split it: '{s[:60]}...'")
        run = run + 1 if re.match(r"I\b", s) else 0
        if run == 3:
            issues.append("three or more sentences in a row start with 'I'")
    if known_numbers is not None:
        for num in set(re.findall(r"\d[\d.,%]*\d%?|\d", text)):
            if num.strip(".,") not in known_numbers:
                issues.append(f"number '{num}' is not found in the profile or job advert")
    return issues


def numbers_in(*texts: str) -> set[str]:
    out: set[str] = set()
    for t in texts:
        out |= {n.strip(".,") for n in re.findall(r"\d[\d.,%]*\d%?|\d", t)}
    return out


def sanitize(text: str) -> str:
    """Last resort, mechanical clean up of dashes so no output ever contains one."""
    text = re.sub(r"(?<=\d)\s*[‒–—−]\s*(?=\d)", " to ", text)
    text = re.sub(r"\s*[‒–—―−]\s*", ", ", text)
    text = re.sub(r"\s+--\s+|--", ", ", text)
    text = re.sub(r"(?<=\s)-(?=\s)", ",", text)
    text = re.sub(r",\s*,", ",", text)
    return re.sub(r"[ \t]+,", ",", text)
