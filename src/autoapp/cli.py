from __future__ import annotations

import argparse
import shutil
import sys
from importlib import resources
from pathlib import Path

from .config import Settings
from .models import Profile
from .pipeline import find_jobs, process_job, run
from .sources import build_sources, job_from_file, job_from_url
from .store import Store


def _load(args):
    settings = Settings.load(args.config)
    profile = Profile.load(args.profile)
    return settings, profile, Store(settings.db_path)


def _llm(settings):
    from .llm import ClaudeLLM
    return ClaudeLLM(settings.llm)


def cmd_init(args):
    root = Path(args.dir)
    for name, dest in (("profile.example.yaml", "profile.yaml"), ("config.example.yaml", "config.yaml")):
        target = root / dest
        if target.exists():
            print(f"{dest} exists, left unchanged")
            continue
        src = resources.files("autoapp").joinpath("templates", name)
        with resources.as_file(src) as p:
            shutil.copy(p, target)
        print(f"created {target}")
    print("Edit profile.yaml, then run: autoapp search")


def cmd_search(args):
    settings, profile, store = _load(args)
    run(profile, settings, build_sources(settings), None, store, args.limit, dry_run=True)


def cmd_run(args):
    settings, profile, store = _load(args)
    run(profile, settings, build_sources(settings), _llm(settings), store, args.limit, args.dry_run)


def _single(job, args):
    settings, profile, store = _load(args)
    process_job(job, profile, settings, _llm(settings), store, force=args.force)


def cmd_apply_url(args):
    _single(job_from_url(args.url), args)


def cmd_apply_file(args):
    _single(job_from_file(args.file), args)


def cmd_list(args):
    settings = Settings.load(args.config)
    for seen, status, score, company, title, folder in Store(settings.db_path).rows():
        print(f"{seen[:10]}  {status:9} {score:5.1f}  {company} | {title}  {folder}")


def main(argv=None):
    ap = argparse.ArgumentParser(prog="autoapp", description=__doc__)
    ap.add_argument("--config", default="config.yaml")
    ap.add_argument("--profile", default="profile.yaml")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("init", help="create profile.yaml and config.yaml")
    p.add_argument("--dir", default=".")
    p.set_defaults(fn=cmd_init)

    p = sub.add_parser("search", help="find and rank recent jobs (no LLM, no cost)")
    p.add_argument("--limit", type=int)
    p.set_defaults(fn=cmd_search)

    p = sub.add_parser("run", help="find jobs and prepare an application package for each")
    p.add_argument("--limit", type=int, help="max packages this run")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_run)

    p = sub.add_parser("apply-url", help="prepare a package for one job page (LinkedIn, Indeed, StepStone ...)")
    p.add_argument("url")
    p.add_argument("--force", action="store_true", help="prepare even if the fit check says no")
    p.set_defaults(fn=cmd_apply_url)

    p = sub.add_parser("apply-file", help="prepare a package from a job advert saved as text")
    p.add_argument("file")
    p.add_argument("--force", action="store_true")
    p.set_defaults(fn=cmd_apply_file)

    p = sub.add_parser("list", help="show what has been processed")
    p.set_defaults(fn=cmd_list)

    args = ap.parse_args(argv)
    try:
        args.fn(args)
    except FileNotFoundError as exc:
        sys.exit(f"File not found: {exc.filename}. Run 'autoapp init' first.")
    except RuntimeError as exc:
        sys.exit(str(exc))


if __name__ == "__main__":
    main()
