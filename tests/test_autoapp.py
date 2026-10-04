from pathlib import Path

import yaml
from docx import Document

from autoapp.config import Settings
from autoapp.matching import score_job
from autoapp.models import Job, Profile
from autoapp.pipeline import process_job
from autoapp.sources import job_from_file
from autoapp.store import Store
from autoapp.style import lint, sanitize

ROOT = Path(__file__).parent.parent
PROFILE = yaml.safe_load((ROOT / "src/autoapp/templates/profile.example.yaml").read_text())


def profile():
    return Profile.model_validate(PROFILE)


def job():
    return Job(source="t", title="Research Associate AI Governance", company="Acme GmbH",
               location="Berlin", url="https://x.test/1",
               description="We need Python, text analysis and policy analysis for AI governance work. 40,000 texts.")


class StubLLM:
    """Returns canned answers. The first CV draft breaks the style rules on purpose."""
    def __init__(self):
        self.cv_calls = 0

    def text(self, system, user, *, web_search=False):
        return ""

    def json(self, system, user, *, web_search=False):
        if "Research the employer" in system or "researcher helping" in system:
            return {"overview": "Acme builds tools.", "letter_hooks": ["their audit tool"],
                    "culture_and_values": "not found", "role_context": "AI team", "contact": "",
                    "recent_developments": [], "cautions": "", "sources": []}
        if "career advisor" in system:
            return {"match_score": 80, "should_apply": True, "reason": "Good fit.", "language": "en",
                    "requirements": [{"requirement": "Python", "evidence": "pipeline", "strength": "strong"}],
                    "strongest_points": ["Python pipeline"], "gaps": [], "keywords": ["Python"]}
        if "tailor a CV" in system:
            self.cv_calls += 1
            summary = "Researcher — passionate about AI." if self.cv_calls == 1 else "Researcher in AI governance."
            return {"summary": summary, "skills": ["Python", "Invented Skill", "R"],
                    "experience": [{"index": 0, "bullets": ["Built a text analysis pipeline for 40,000 speeches"]}],
                    "education": [{"index": 0, "details": []}]}
        return {"salutation": "Dear Hiring Team,", "subject": "Application for Research Associate",
                "paragraphs": ["I read about the Acme audit tool. It fits my work.",
                               "I built a pipeline for 40,000 speeches in Python."],
                "closing": "Kind regards"}


def test_lint_catches_problems():
    bad = "This is a — passionate, dynamic sentence! 2019-2022 and 99 percent."
    issues = " ".join(lint(bad, known_numbers=set()))
    for needle in ("dash", "passionate", "dynamic", "exclamation", "This/These", "'99'"):
        assert needle in issues


def test_lint_clean_text():
    assert lint("I built a tool in Python. It read 40 files.", {"40"}) == []


def test_sanitize_removes_dashes():
    out = sanitize("2019–2022 and research — teaching")
    assert "–" not in out and "—" not in out and "2019 to 2022" in out


def test_scoring_prefers_relevant_job():
    p = profile()
    good = score_job(job(), p)
    other = score_job(Job(source="t", title="Welder", description="steel"), p)
    assert good.score > 45 > other.score


def test_exclude_keyword():
    p = profile()
    j = score_job(Job(source="t", title="Internship AI", description="Python"), p)
    assert j.score == 0


def test_job_from_file(tmp_path):
    f = tmp_path / "j.txt"
    f.write_text("Title: Analyst\nCompany: Foo\n\nDo analysis.")
    j = job_from_file(f)
    assert (j.title, j.company, j.description) == ("Analyst", "Foo", "Do analysis.")


def test_end_to_end(tmp_path, monkeypatch):
    monkeypatch.setattr("autoapp.pipeline.enrich", lambda j: j)
    s = Settings(output_dir=str(tmp_path / "apps"), db_path=str(tmp_path / "db.sqlite"))
    store = Store(s.db_path)
    llm = StubLLM()
    folder = process_job(job(), profile(), s, llm, store)
    names = {p.name for p in folder.iterdir()}
    assert {"CoverLetter.txt", "company_research.md", "fit_analysis.md", "README.md", "job.json"} <= names
    assert any(n.startswith("CV_") for n in names) and any(n.startswith("CoverLetter_") for n in names)
    assert llm.cv_calls == 2, "style problems should trigger one repair round"
    cv = Document(next(folder.glob("CV_*.docx")))
    text = "\n".join(p.text for p in cv.paragraphs)
    assert "Invented Skill" not in text and "—" not in text
    assert "Doctoral Researcher, Example University" in text
    assert store.known(job().id)
