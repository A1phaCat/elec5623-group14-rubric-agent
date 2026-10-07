"""Derive the team contribution register from git history.

A2 marks team contributions under documentation and delivery, and the proposal
lost half a mark for not assigning work to named people. The answer is not a
better-worded table: it is a table a marker can verify. This reads the actual
commit history and reports, per author, what they committed and which
ownership areas those files belong to.

    .venv/bin/python scripts/contribution_register.py
    .venv/bin/python scripts/contribution_register.py --markdown

It reports what git contains. An author with no commits shows zero, and the
output says so plainly rather than describing an intention. Mapping a git
identity to a group member is a human step, recorded in IDENTITIES below.
"""

from __future__ import annotations

import argparse
import json
import subprocess
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# Every group member, with the git identities known to be theirs. A member with
# no identity has not committed yet; add theirs when their first commit lands.
# Never guess an identity and never attribute a commit to someone who did not
# make it.
MEMBERS: dict[str, list[str]] = {
    "Zongjian Li": [],
    "Zhengyu Han": ["hanzhengyu202305@gmail.com"],
    "Yuchun Zheng": [],
    "Yutong Liu": [],
    "Zhaoxinyi Zhou": [],
}

# Ownership areas from docs/TEAM_DELIVERY.md, by path prefix. Order matters:
# the first matching prefix wins.
AREAS: list[tuple[str, str]] = [
    ("src/rubric_agent/rubric_parser.py", "A1 rubric schema and parser"),
    ("src/rubric_agent/text_parser.py", "A2 document ingestion and provenance"),
    ("src/rubric_agent/chunker.py", "A2 document ingestion and provenance"),
    ("src/rubric_agent/retriever.py", "A3 retrieval and logging"),
    ("src/rubric_agent/store.py", "A3 retrieval and logging"),
    ("src/rubric_agent/gateway.py", "A4 GenAI assessment and validation"),
    ("src/rubric_agent/validator.py", "A4 GenAI assessment and validation"),
    ("src/rubric_agent/pipeline.py", "A4 GenAI assessment and validation"),
    ("src/rubric_agent/eval.py", "A4 evaluation design"),
    ("src/rubric_agent/review.py", "A5 marker UI and review workflow"),
    ("app/", "A5 marker UI and review workflow"),
    ("prompts/", "A4 GenAI assessment and validation"),
    ("dataset/final_test/annotation/", "A2 independent annotation coordination"),
    ("dataset/", "A2 document ingestion and provenance"),
    ("docs/sessions/", "A5 marker study"),
    ("docs/MARKER_SESSIONS.md", "A5 marker study"),
    ("docs/RELATED_WORK", "A1 related-work audit"),
    ("docs/EVALUATION", "A4 evaluation design"),
    ("docs/tuning/", "A4 evaluation design"),
    ("scripts/", "A3 experiment execution"),
    ("tests/", "shared: tests"),
    ("docs/", "shared: documentation"),
    ("src/", "A4 GenAI assessment and validation"),
]


def area_for(path: str) -> str:
    for prefix, area in AREAS:
        if path.startswith(prefix):
            return area
    return "shared: project files"


def history() -> list[dict]:
    """One record per commit, with author email and the files it touched."""
    separator = "\x1e"
    raw = subprocess.run(
        ["git", "log", f"--format={separator}%H%x1f%ae%x1f%an%x1f%aI%x1f%s", "--name-only", "--no-merges"],
        cwd=ROOT, capture_output=True, text=True, check=True,
    ).stdout
    commits = []
    for block in raw.split(separator):
        if not block.strip():
            continue
        header, _, files = block.partition("\n")
        sha, email, name, date, subject = header.split("\x1f")
        commits.append({
            "sha": sha[:9], "email": email, "git_name": name, "date": date, "subject": subject,
            "files": [line for line in files.strip().splitlines() if line],
        })
    return commits


def register() -> dict:
    commits = history()
    by_email: dict[str, list[dict]] = defaultdict(list)
    for commit in commits:
        by_email[commit["email"]].append(commit)

    people = []
    for member, emails in sorted(MEMBERS.items()):
        owned = sorted((c for email in emails for c in by_email.get(email, [])),
                       key=lambda c: c["date"], reverse=True)
        areas: dict[str, int] = defaultdict(int)
        files: set[str] = set()
        for commit in owned:
            for path in commit["files"]:
                areas[area_for(path)] += 1
                files.add(path)
        people.append({
            "member": member,
            "git_identities": emails or None,
            "commits": len(owned),
            "files_touched": len(files),
            "areas": dict(sorted(areas.items(), key=lambda item: -item[1])),
            "first_commit": owned[-1]["date"] if owned else None,
            "last_commit": owned[0]["date"] if owned else None,
            "evidence": [{"sha": c["sha"], "date": c["date"][:10], "subject": c["subject"]} for c in owned],
        })

    claimed = {email for emails in MEMBERS.values() for email in emails}
    unmapped = sorted(set(by_email) - claimed)
    return {
        "generated_from": "git log --no-merges",
        "total_commits": len(commits),
        "members": people,
        "members_with_no_commits": [p["member"] for p in people if p["commits"] == 0],
        "unmapped_git_identities": unmapped,
        "honesty_note": (
            "This is what the repository contains. A member with no commits has no committed "
            "contribution evidence here; reviewing, annotating or running a session is real work but "
            "must be recorded in its own artifact (annotation sheets, session files) and named there."
        ),
    }


def to_markdown(data: dict) -> str:
    lines = [
        "<!-- Generated by scripts/contribution_register.py. Do not hand-edit. -->",
        "# Contribution register (from git history)",
        "",
        f"Derived from `{data['generated_from']}`: {data['total_commits']} commits.",
        "",
        "| Member | Git identity | Commits | Files touched | Main areas by files changed |",
        "|---|---|---:|---:|---|",
    ]
    for person in data["members"]:
        areas = ", ".join(f"{name} ({count})" for name, count in list(person["areas"].items())[:3]) or "—"
        identity = ", ".join(f"`{e}`" for e in person["git_identities"] or []) or "not recorded"
        lines.append(f"| {person['member']} | {identity} | {person['commits']} "
                     f"| {person['files_touched']} | {areas} |")
    if data["members_with_no_commits"]:
        lines += ["", "**No committed contribution evidence in this repository yet:** "
                  + ", ".join(data["members_with_no_commits"]) + "."]
    if data["unmapped_git_identities"]:
        lines += ["", "**Unmapped git identities** (add them to `MEMBERS`): "
                  + ", ".join(f"`{e}`" for e in data["unmapped_git_identities"]) + "."]
    lines += ["", data["honesty_note"], ""]
    for person in data["members"]:
        if not person["evidence"]:
            continue
        lines += [f"## {person['member']}", ""]
        lines += [f"- `{c['sha']}` {c['date']} — {c['subject']}" for c in person["evidence"]]
        lines.append("")
    return "\n".join(lines)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--markdown", action="store_true", help="write docs/CONTRIBUTIONS.md")
    args = parser.parse_args()
    data = register()
    if args.markdown:
        out = ROOT / "docs/CONTRIBUTIONS.md"
        out.write_text(to_markdown(data) + "\n", encoding="utf-8")
        print(f"wrote {out.relative_to(ROOT)}")
    else:
        print(json.dumps(data, indent=2, ensure_ascii=False))
    for member in data["members_with_no_commits"]:
        print(f"note: {member} has no commits in this repository")
    for email in data["unmapped_git_identities"]:
        print(f"note: unmapped git identity {email}; add it to IDENTITIES")


if __name__ == "__main__":
    main()
