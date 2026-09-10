# Setup

One-time steps. After this the profile maintains itself.

## 1. Create the repository

The repository name must be **exactly your GitHub username**. That is what makes GitHub
render its README on your profile page.

```
https://github.com/new   ->   Repository name: <your-username>
Public. Do not add a README, .gitignore or licence.
```

## 2. Push this folder

From this folder, in a terminal:

```bash
git init -b main
git add .
git commit -m "feat: self-generating profile README"
git remote add origin https://github.com/<your-username>/<your-username>.git
git push -u origin main
```

## 3. Let Actions write to the repository

`Settings -> Actions -> General -> Workflow permissions` ->
select **Read and write permissions** -> Save.

Without this the workflow renders the README fine and then fails on `git push`.

## 4. Run it once

`Actions -> Generate README -> Run workflow`.

The push in step 2 already triggers it, but running it by hand is the quickest way to
read the log if something is off. Give it about a minute, then reload your profile page.

## 5. Fill in the parts only you know

Open `data/profile.json` and set:

- `links.LinkedIn` — your profile URL
- `links.Email` — the address you want recruiters to use
- `links.Resume` — a public link to your CV, if you want one on the page
- `projects[].repo` — the repo name once each project is public, which turns the
  project heading into a link

Leave `display_name`, `location` and any link as `null` and it is simply left out or
filled from your GitHub account.

Commit and push. The workflow reruns on any change under `data/`, `templates/` or
`scripts/`.

## How it fits together

```
data/profile.json          the only hand-written content
templates/README.tmpl.md   the layout, with {{PLACEHOLDER}} slots
scripts/generate_readme.py fetches live data, fills the slots, writes README.md
.github/workflows/         runs daily at 00:30 UTC, on push, and on demand
```

`README.md` is build output. Editing it directly is pointless — the next run overwrites
it. Edit the template or `profile.json`.

## Running it on your own machine

```bash
GITHUB_TOKEN=$(gh auth token) GITHUB_REPOSITORY_OWNER=<your-username> python scripts/generate_readme.py
```

Standard library only, so there is nothing to install.

## Things worth knowing

- **The daily run usually commits nothing.** The generator ignores its own timestamp
  when deciding whether anything changed, so a day with no new public activity produces
  no commit. That keeps the history free of bot noise, at the cost of a `Last generated`
  date that can be a few days stale.
- **The streak card is third-party.** `github-readme-streak-stats` is hosted by someone
  else and goes down occasionally. If you would rather not depend on it, remove that card
  from `render_stats_cards` in the generator.
- **Private work is invisible.** The event feed is public events only. Private repos
  count toward the stats card totals but never appear in `Lately`.
- **Language percentages are bytes, not effort.** A generated lockfile can outweigh a
  month of careful work. Add noisy languages to `options.exclude_languages`, or noisy
  repos to `options.exclude_repos`.
