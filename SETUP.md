# Setup

Everything in this folder is already generated. The steps below push it and put
the graphics on a schedule.

## 1. Push

Your profile repository already exists at `github.com/diansour-king/diansour-king`
and has GitHub's default "Hi there" README on it, so this builds on top of that
commit rather than colliding with it.

```bat
cd /d "%USERPROFILE%\Documents\bikash-profile"
mkdir .github\workflows
move workflow-stats.yml .github\workflows\stats.yml
git init -b main
git remote add origin https://github.com/diansour-king/diansour-king.git
git fetch origin main
git reset --soft origin/main
git add .
git commit -m "feat: ascii profile with generated stat graphics"
git push origin main
```

## 2. Let Actions write to the repository

`Settings -> Actions -> General -> Workflow permissions` -> **Read and write
permissions** -> Save.

Without this the workflow draws the graphics correctly and then fails on
`git push`, and your profile keeps the empty baseline forever.

## 3. Run it once

`Actions -> refresh stats -> Run workflow`.

The graphics committed here are an **empty baseline** — zeros everywhere. That is
deliberate: invented sample numbers on a public profile are a lie that a broken
workflow never gets round to correcting. The first run replaces them with your
real contribution data. After that it runs daily at 05:17 UTC (10:47 IST).

Note the workflow has no `push` trigger, on purpose. It commits SVG files, and a
push trigger would make it re-run on its own commit forever.

## 4. Add your links

`README.md` currently links GitHub and email. There is a commented block just
below them with LinkedIn and LeetCode ready to go — uncomment it and drop your
URLs in.

The project links all point at your profile page, because none of those repos are
public yet. Point each at its real repository as you publish them.

## What is here

```
ascii.svg                    the wordmark at the top, self-typing
stats.svg streak.svg         drawn daily from the GitHub GraphQL API
langs.svg year.svg
hd-*.svg                     section headings, so they use the page's own typeface
icon-*.svg                   link icons, light and dark
scripts/generate_stats.py    the daily generator — stdlib only, no dependencies
scripts/make_wordmark.py     one-off: rebuilds ascii.svg from text
scripts/make_portrait.py     one-off: rebuilds ascii.svg from a photograph
scripts/embed_portrait_font.py  inlines JetBrains Mono into ascii.svg
```

## Rebuilding the top graphic

To change the wordmark text:

```bash
python3 scripts/make_wordmark.py "BIKASH" "KUMAR SHAH" --tagline "cse @ nit rourkela  -  batch of 2027"
python3 scripts/embed_portrait_font.py
```

To use a photograph of yourself instead — this is the version that makes people
stop scrolling, and it is what the original design was built around:

```bash
pip install pillow numpy opencv-python-headless rembg onnxruntime
python3 scripts/make_portrait.py photo.png --crop 400,110,910,790
python3 scripts/embed_portrait_font.py
```

Read the docstring at the top of `make_portrait.py` first. The photo decides
everything: side light at roughly 45 degrees, a tight crop from chin to just
above the hair, real resolution. Flat frontal light renders your face as a hole.

The second command is not optional in either case. The character grid assumes an
advance width of exactly 0.600 em, and without the inlined font a viewer whose
default monospace is narrower sees the whole thing squeezed.

## Why the fonts are inlined as base64

These SVGs are loaded through `<img>` tags, and browsers refuse to fetch
subresources for an image document — an external font URL simply never loads.
Same reason the animation is SMIL rather than JavaScript: GitHub strips `<script>`
from rendered READMEs.

## Credit

The layout, the generator and the drawing code are adapted from
[vivekstackk/vivekstackk](https://github.com/vivekstackk), which is where this
design comes from. That repository carries no licence, which strictly means no
permission is granted to reuse it. Adding a line of credit in the README, or
asking the author, is the decent thing to do — see the note in this project's
setup conversation.
