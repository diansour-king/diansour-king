<h1 align="center">{{NAME}}</h1>
<p align="center">{{TAGLINE}}</p>
<p align="center">{{BADGES}}</p>

---

## About

{{ABOUT}}

## Currently

{{FOCUS}}

## Stack

{{STACK}}

## Projects

{{PROJECTS}}

## What I actually write

{{LANGUAGES}}

## Lately

{{ACTIVITY}}

## By the numbers

{{STATS_CARDS}}

---

<details>
<summary><b>This README wrote itself. Here is how.</b></summary>

<br>

There is no hand-edited `README.md` in this repository. There is a template, a small
generator, and a scheduled workflow:

```
data/profile.json          the only hand-written content
templates/README.tmpl.md   the layout, with placeholders
scripts/generate_readme.py stdlib-only Python, no dependencies
.github/workflows/         runs the generator, commits the result if it changed
```

Every day the workflow calls the GitHub API for repositories, language byte counts and
the public event feed, renders the template, and commits the output only when the
rendered bytes differ from what is already on `main`. Editing `README.md` by hand is
pointless: the next run overwrites it. Edit the template or `profile.json` instead.

The counts below are produced by the same run that produced this page.

| | |
|---|---|
| Public repositories | {{COUNT_REPOS}} |
| Stars earned | {{COUNT_STARS}} |
| Languages detected | {{COUNT_LANGS}} |
| Bytes of code measured | {{COUNT_BYTES}} |

</details>

<p align="center"><sub>Last generated {{UPDATED}} — <a href="{{RUN_URL}}">workflow run</a></sub></p>
