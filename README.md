# AutoApp

AutoApp finds recent jobs that fit your profile. For each good match it researches the company, checks the advert against your background, and writes a tailored CV and cover letter. Everything is saved in one folder per job, ready for you to review and send.

It does **not** submit applications. You read, edit and send them yourself. That is deliberate: employers can tell, and the final check is yours.

## How it works

```
profile.yaml ──> search jobs ──> score and rank ──> for each top job:
                                                    1. research the company (web search)
                                                    2. compare advert and profile (fit analysis)
                                                    3. tailor the CV, write the cover letter
                                                    4. style check, then save to applications/<date>_<company>_<role>/
```

Each folder contains:

| File | Content |
|---|---|
| `CV_<name>.docx` | Tailored CV |
| `CoverLetter_<name>.docx`, `CoverLetter.txt` | Cover letter (the text file is for pasting into web forms) |
| `company_research.md` | What the company does, culture, news, points to mention |
| `fit_analysis.md` | Requirement by requirement match, strongest points, gaps |
| `job_description.txt`, `job.json` | The advert as found |
| `README.md` | Checklist before you send |

## Job sources, and an honest note on LinkedIn, Indeed and StepStone

These three sites have no public job search API. Their terms forbid automated scraping, and they block it, so AutoApp does not scrape them. Instead:

* **Automatic search** uses sources that allow it: [Adzuna](https://developer.adzuna.com) (free key, aggregates many boards), [Jooble](https://jooble.org/api/about) (free key) and [Arbeitnow](https://www.arbeitnow.com/api/job-board-api) (no key, good for Germany and the EU). Adding another source means writing one small class in `src/autoapp/sources/`.
* **LinkedIn, Indeed, StepStone**: set up job alerts on those sites, open a job you like, then run `autoapp apply-url <link>`. If the page cannot be read, save the advert text to a file and run `autoapp apply-file advert.txt`.

## Setup

```bash
pip install -e .
export ANTHROPIC_API_KEY=...      # for the research and writing steps
export ADZUNA_APP_ID=... ADZUNA_APP_KEY=...   # optional but recommended

autoapp init                      # creates profile.yaml and config.yaml
# edit profile.yaml: skills, experience, education, interests, search settings
autoapp search                    # free: find and rank jobs, no LLM calls
autoapp run --limit 3             # prepare packages for the top 3 new jobs
autoapp apply-url "https://..."   # one specific job
autoapp apply-file advert.txt     # one advert saved as text
autoapp list                      # what has been processed
```

`profile.yaml` is the single source of truth. Titles, employers and dates in the CV are copied from it by the program, never written by the model.

## How the writing stays honest and natural

* The model may only select, order and lightly reword facts from your profile. Skills outside your profile are removed in code. Numbers that appear in neither your profile nor the advert are flagged.
* The prompts carry a style guide: plain words, short sentences, no dashes, no sentences starting with "This", no stock phrases such as "highlighting" or "passionate".
* A linter checks every draft against those rules. Failing drafts go back to the model for up to two repair rounds. Dashes are then removed mechanically. Anything still failing is listed in the folder's `README.md`.
* Edit the output. A letter you have read aloud and adjusted will always sound more like you than any generator can manage.

## Settings

`config.yaml` sets the model (`claude-opus-5-5` by default), effort, web search on or off, output folder and the per run limit. API keys are read from environment variables only.

## Cost and limits

A package takes roughly four model calls, plus web searches for the research step. Use `autoapp search` first, then `--limit` to control spend. Lowering `effort` to `low` cuts cost further.

## Development

```bash
pip install -e ".[dev]"
pytest
```

Tests use a stub model, so they run offline and cost nothing.
