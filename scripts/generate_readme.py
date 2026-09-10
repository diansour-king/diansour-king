"""Render README.md from templates/README.tmpl.md plus live GitHub data.

Standard library only. A dependency here would mean a pip install on every
scheduled run, and a broken profile the first time a wheel disappears.

Run locally with:
    GITHUB_TOKEN=$(gh auth token) GITHUB_REPOSITORY_OWNER=<you> python scripts/generate_readme.py
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROFILE_PATH = ROOT / "data" / "profile.json"
TEMPLATE_PATH = ROOT / "templates" / "README.tmpl.md"
OUTPUT_PATH = ROOT / "README.md"

API = "https://api.github.com"
BAR_WIDTH = 24


class GitHubError(RuntimeError):
    """The GitHub API refused a request we cannot proceed without."""


def api_get(path: str, token: str, params: dict | None = None):
    url = f"{API}{path}"
    if params:
        pairs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{pairs}"
    request = urllib.request.Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {token}",
            "User-Agent": "self-generating-profile",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        raise GitHubError(f"{exc.code} {exc.reason} for {path}") from exc
    except urllib.error.URLError as exc:
        raise GitHubError(f"could not reach {path}: {exc.reason}") from exc


def api_get_optional(path: str, token: str, params: dict | None = None, default=None):
    """Some endpoints are allowed to fail without taking the whole page down.

    The event feed in particular 404s for accounts with no public activity, and
    a private repository's /languages is invisible to a read-only token.
    """
    try:
        return api_get(path, token, params)
    except GitHubError as exc:
        print(f"  skipped {path}: {exc}", file=sys.stderr)
        return default


def fetch_repos(user: str, token: str) -> list[dict]:
    repos: list[dict] = []
    page = 1
    while True:
        batch = api_get(
            f"/users/{user}/repos",
            token,
            {"per_page": "100", "page": str(page), "type": "owner", "sort": "pushed"},
        )
        repos.extend(batch)
        if len(batch) < 100:
            return repos
        page += 1


def language_totals(repos: list[dict], token: str, excluded: set[str]) -> dict[str, int]:
    totals: dict[str, int] = {}
    for repo in repos:
        if repo.get("fork") or repo.get("archived"):
            continue
        counts = api_get_optional(f"/repos/{repo['full_name']}/languages", token, default={})
        for language, byte_count in (counts or {}).items():
            if language in excluded:
                continue
            totals[language] = totals.get(language, 0) + byte_count
    return totals


def render_languages(totals: dict[str, int], limit: int) -> tuple[str, int, int]:
    total_bytes = sum(totals.values())
    if not total_bytes:
        return "_No language data yet — push some code._", 0, 0

    ranked = sorted(totals.items(), key=lambda pair: pair[1], reverse=True)[:limit]
    name_width = max(len(name) for name, _ in ranked)

    lines = ["```text"]
    for name, byte_count in ranked:
        share = byte_count / total_bytes
        filled = round(share * BAR_WIDTH)
        bar = "█" * filled + "░" * (BAR_WIDTH - filled)
        lines.append(f"{name.ljust(name_width)}  {bar}  {share * 100:5.1f}%")
    lines.append("```")
    return "\n".join(lines), len(totals), total_bytes


EVENT_PHRASES = {
    "PushEvent": "pushed to",
    "CreateEvent": "created",
    "PullRequestEvent": "opened a pull request in",
    "IssuesEvent": "opened an issue in",
    "WatchEvent": "starred",
    "ForkEvent": "forked",
    "ReleaseEvent": "released",
    "PublicEvent": "made public",
}


def render_activity(events: list[dict] | None, limit: int) -> str:
    if not events:
        return "_Nothing public in the last little while._"

    lines: list[str] = []
    seen: set[tuple[str, str]] = set()
    for event in events:
        kind = event.get("type", "")
        phrase = EVENT_PHRASES.get(kind)
        if not phrase:
            continue

        repo_name = event.get("repo", {}).get("name", "")
        key = (kind, repo_name)
        if key in seen:
            continue
        seen.add(key)

        detail = ""
        if kind == "PushEvent":
            commits = event.get("payload", {}).get("commits", [])
            if commits:
                message = commits[-1].get("message", "").splitlines()[0].strip()
                if len(message) > 72:
                    message = message[:69].rstrip() + "..."
                detail = f" — {message}"
        elif kind == "PullRequestEvent":
            number = event.get("payload", {}).get("number")
            if number:
                detail = f" (#{number})"

        when = relative_time(event.get("created_at", ""))
        lines.append(
            f"- {phrase} [`{repo_name}`](https://github.com/{repo_name}){detail} "
            f"<sub>{when}</sub>"
        )
        if len(lines) >= limit:
            break

    return "\n".join(lines) if lines else "_Nothing public in the last little while._"


def relative_time(stamp: str) -> str:
    if not stamp:
        return ""
    moment = datetime.strptime(stamp, "%Y-%m-%dT%H:%M:%SZ").replace(tzinfo=timezone.utc)
    seconds = (datetime.now(timezone.utc) - moment).total_seconds()
    if seconds < 3600:
        return "just now"
    if seconds < 86400:
        hours = int(seconds // 3600)
        return f"{hours}h ago"
    days = int(seconds // 86400)
    if days < 30:
        return f"{days}d ago"
    return moment.strftime("%d %b %Y")


def render_projects(projects: list[dict], user: str) -> str:
    if not projects:
        return "_Coming soon._"

    blocks: list[str] = []
    for project in projects:
        repo = project.get("repo")
        if repo:
            slug = repo if "/" in repo else f"{user}/{repo}"
            heading = f"### [{project['name']}](https://github.com/{slug})"
        else:
            heading = f"### {project['name']}"

        stack = project.get("stack") or []
        stack_line = " · ".join(f"`{item}`" for item in stack)

        block = [heading, "", project.get("blurb", "")]
        if stack_line:
            block += ["", stack_line]
        blocks.append("\n".join(block))

    return "\n\n".join(blocks)


def render_stack(stack: dict[str, list[str]]) -> str:
    if not stack:
        return ""
    lines = ["| | |", "|---|---|"]
    for group, items in stack.items():
        lines.append(f"| **{group}** | {' · '.join(f'`{item}`' for item in items)} |")
    return "\n".join(lines)


def render_stats_cards(user: str, theme: str, enabled: bool) -> str:
    if not enabled:
        return ""
    base = "https://github-readme-stats.vercel.app/api"
    cards = [
        f'<img src="{base}?username={user}&show_icons=true&hide_border=true&theme={theme}'
        f'&include_all_commits=true&count_private=true" height="165" alt="GitHub stats" />',
        f'<img src="https://github-readme-streak-stats.herokuapp.com/?user={user}'
        f'&hide_border=true&theme={theme}" height="165" alt="Contribution streak" />',
    ]
    return '<p align="center">\n  ' + "\n  ".join(cards) + "\n</p>"


def render_badges(links: dict[str, str | None], user: str) -> str:
    badges = [
        f'<a href="https://github.com/{user}">'
        f'<img src="https://img.shields.io/github/followers/{user}?label=Followers&style=flat-square&color=1f2937" alt="Followers" /></a>'
    ]
    icons = {"LinkedIn": ("linkedin", "0A66C2"), "Email": ("gmail", "EA4335"), "Resume": ("readdotcv", "111827")}
    for label, url in (links or {}).items():
        if not url:
            continue
        slug, color = icons.get(label, ("link", "1f2937"))
        href = f"mailto:{url}" if label == "Email" and "@" in url else url
        badges.append(
            f'<a href="{href}">'
            f'<img src="https://img.shields.io/badge/{label}-{color}?style=flat-square&logo={slug}&logoColor=white" alt="{label}" /></a>'
        )
    return "\n  ".join(badges)


def bullets(items: list[str]) -> str:
    return "\n".join(f"- {item}" for item in items)


def main() -> int:
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        print("GITHUB_TOKEN is not set", file=sys.stderr)
        return 1

    profile = json.loads(PROFILE_PATH.read_text(encoding="utf-8"))
    options = profile.get("options", {})

    user = os.environ.get("GITHUB_REPOSITORY_OWNER")
    if not user:
        print("GITHUB_REPOSITORY_OWNER is not set", file=sys.stderr)
        return 1

    print(f"Generating profile for {user}")
    account = api_get(f"/users/{user}", token)

    excluded_repos = set(options.get("exclude_repos") or [])
    repos = [r for r in fetch_repos(user, token) if r["name"] not in excluded_repos]
    owned = [r for r in repos if not r.get("fork")]
    stars = sum(r.get("stargazers_count", 0) for r in owned)

    excluded_languages = set(options.get("exclude_languages") or [])
    totals = language_totals(repos, token, excluded_languages)
    languages_block, language_count, total_bytes = render_languages(
        totals, int(options.get("language_count", 8))
    )

    events = api_get_optional(
        f"/users/{user}/events/public", token, {"per_page": "60"}, default=[]
    )

    run_id = os.environ.get("GITHUB_RUN_ID")
    repository = os.environ.get("GITHUB_REPOSITORY", f"{user}/{user}")
    run_url = (
        f"https://github.com/{repository}/actions/runs/{run_id}"
        if run_id
        else f"https://github.com/{repository}/actions"
    )

    replacements = {
        "{{NAME}}": profile.get("display_name") or account.get("name") or user,
        "{{TAGLINE}}": profile.get("tagline") or account.get("bio") or "",
        "{{BADGES}}": render_badges(profile.get("links", {}), user),
        "{{ABOUT}}": bullets(profile.get("about", [])),
        "{{FOCUS}}": bullets(profile.get("focus", [])),
        "{{STACK}}": render_stack(profile.get("stack", {})),
        "{{PROJECTS}}": render_projects(profile.get("projects", []), user),
        "{{LANGUAGES}}": languages_block,
        "{{ACTIVITY}}": render_activity(events, int(options.get("activity_count", 5))),
        "{{STATS_CARDS}}": render_stats_cards(
            user, options.get("theme", "tokyonight"), bool(options.get("show_stats_cards", True))
        ),
        "{{COUNT_REPOS}}": str(len(owned)),
        "{{COUNT_STARS}}": str(stars),
        "{{COUNT_LANGS}}": str(language_count),
        "{{COUNT_BYTES}}": f"{total_bytes:,}",
        "{{UPDATED}}": datetime.now(timezone.utc).strftime("%d %b %Y at %H:%M UTC"),
        "{{RUN_URL}}": run_url,
    }

    rendered = TEMPLATE_PATH.read_text(encoding="utf-8")
    for placeholder, value in replacements.items():
        rendered = rendered.replace(placeholder, value)

    leftover = [line for line in rendered.splitlines() if "{{" in line and "}}" in line]
    if leftover:
        print(f"Unresolved placeholders: {leftover}", file=sys.stderr)
        return 1

    previous = OUTPUT_PATH.read_text(encoding="utf-8") if OUTPUT_PATH.exists() else ""

    # A fresh timestamp on its own is not news. Leaving the old file untouched
    # keeps the commit history free of a daily bot commit that says nothing.
    if previous and strip_timestamp(previous) == strip_timestamp(rendered):
        print("No substantive change; leaving README.md as it is.")
        return 0

    OUTPUT_PATH.write_text(rendered, encoding="utf-8")
    print(f"README updated: {len(owned)} repos, {language_count} languages.")
    return 0


def strip_timestamp(text: str) -> str:
    """Ignore the footer line so a bare clock tick does not create a commit."""
    return "\n".join(line for line in text.splitlines() if "Last generated" not in line)


if __name__ == "__main__":
    raise SystemExit(main())
