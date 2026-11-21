# Morsel status

Uptime monitoring and the public status page for [Morsel](https://projectmorsel.web.app),
at **https://status.projectmorsel.com**. It runs on [Upptime](https://upptime.js.org), an
open-source monitor that uses GitHub Actions, Issues and Pages.

## How it works

- **Checks.** Uptime CI calls each address in [`.upptimerc.yml`](.upptimerc.yml). It's
  scheduled every five minutes, but GitHub runs schedules late at busy times, so "about every
  five minutes". Each run checks every site. It commits to `history/<slug>.yml` only when a
  status changes, so `lastUpdated` there is the last change, not the last check. The last
  check is the last successful Uptime CI run.
- **Incidents.** When a check fails, Upptime opens an issue labelled `status` and the site's
  slug. It closes the issue when the check passes again. These issues are the incident record:
  write updates as comments, in plain words.
- **Numbers.** Summary CI writes `history/summary.json` (uptime and response times) once a day.
  Graphs CI draws `graphs/`. Morsel's web app reads `history/summary.json` for its own
  `/status` page.
- **Website.** Static Site CI builds the page with `@upptime/status-page` and pushes it to the
  `gh-pages` branch. It runs daily, when `assets/` changes, and from Setup CI when
  `.upptimerc.yml` changes. GitHub Pages must publish from `gh-pages` at `/ (root)`; publishing
  from `main` shows this README instead of the status page.

## Look and words

Branding uses only Upptime's supported settings, so template updates don't undo it:

- `.upptimerc.yml` → `status-website`: name, logo, favicon, `themeUrl` (colours),
  `links` (a stylesheet loaded after Upptime's own), intro, navbar and `i18n` (the page's
  words).
- `assets/`: copied to the site's root after each build. It holds `morsel-theme.css`,
  `morsel.css`, Manrope (`fonts/`, SIL Open Font License in `fonts/OFL.txt`), the logo, the
  favicon, the app icons and `manifest.json`.

Asset addresses in `.upptimerc.yml` are absolute (`https://status.projectmorsel.com/...`).
The build crawls root-relative ones and creates folders with their names, which then block
copying the assets.

Never edit `.github/workflows/`; Update Template CI replaces those files.

## Preview locally

```bash
tools/build-site.sh       # builds exactly as Static Site CI does, into site/
python3 tools/preview.py site/status-page/__sapper__/export down /tmp/status-down 390 1280
```

The page loads its stylesheets from status.projectmorsel.com, so a plain local server shows
the published styles. `tools/preview.py` serves that host from the build instead. It also
answers GitHub with fixtures (all up, slow, down with an open incident, past incidents, no
history, GitHub failing), so every state can be checked without a real incident.

## Live status: <!--live status--> **Checking**

<!--start: status pages-->
<!--end: status pages-->

The Upptime code is MIT licensed (`LICENSE`). Manrope is under the SIL Open Font License
(`assets/fonts/OFL.txt`).
