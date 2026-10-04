"""Polite page fetching. Checks robots.txt and identifies itself."""
from __future__ import annotations

import json
import re
import urllib.robotparser
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

UA = "AutoApp/0.1 (personal job application assistant)"
_robots: dict[str, urllib.robotparser.RobotFileParser | None] = {}


def allowed(url: str) -> bool:
    p = urlparse(url)
    base = f"{p.scheme}://{p.netloc}"
    if base not in _robots:
        rp = urllib.robotparser.RobotFileParser()
        try:
            r = requests.get(base + "/robots.txt", headers={"User-Agent": UA}, timeout=10)
            rp.parse(r.text.splitlines() if r.ok else [])
            _robots[base] = rp
        except requests.RequestException:
            _robots[base] = None
    rp = _robots[base]
    return True if rp is None else rp.can_fetch(UA, url)


def fetch_html(url: str) -> str:
    """Returns page HTML, or an empty string when blocked or unavailable."""
    if not url.startswith(("http://", "https://")) or not allowed(url):
        return ""
    try:
        r = requests.get(url, headers={"User-Agent": UA, "Accept-Language": "en,de;q=0.8"}, timeout=15)
        return r.text if r.ok else ""
    except requests.RequestException:
        return ""


def html_to_text(html: str, limit: int = 12000) -> str:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "svg"]):
        tag.decompose()
    text = soup.get_text("\n")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n\s*\n+", "\n\n", text).strip()
    return text[:limit]


def fetch_text(url: str, limit: int = 12000) -> str:
    return html_to_text(fetch_html(url), limit)


def jsonld_job(html: str) -> dict | None:
    """Most job boards embed a schema.org JobPosting block for search engines."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(tag.string or "")
        except (json.JSONDecodeError, TypeError):
            continue
        items = data if isinstance(data, list) else data.get("@graph", [data])
        for item in items:
            if isinstance(item, dict) and item.get("@type") == "JobPosting":
                return item
    return None
