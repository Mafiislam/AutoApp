from __future__ import annotations

import re
from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone

from ..models import Job, SearchPrefs


class Source(ABC):
    name = "source"

    @abstractmethod
    def search(self, prefs: SearchPrefs) -> list[Job]: ...


def strip_html(text: str) -> str:
    text = re.sub(r"<\s*br\s*/?>|</p>|</li>", "\n", text or "", flags=re.I)
    text = re.sub(r"<[^>]+>", "", text)
    return re.sub(r"\n\s*\n+", "\n\n", text).strip()


def too_old(posted: datetime | None, max_days: int) -> bool:
    if posted is None:
        return False
    if posted.tzinfo is None:
        posted = posted.replace(tzinfo=timezone.utc)
    return datetime.now(timezone.utc) - posted > timedelta(days=max_days)
