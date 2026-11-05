# Baku family guide — local review, 2026-11-05

Status: implemented and verified locally. Not deployed, committed or pushed. Google indexing/ranking was not changed or measured by this implementation.

Base: `5ff3da4540cc61ea74cb71538f4799190574776b`. Isolated managed worktree: `/home/ramin/.codex/worktrees/baku-guide-choice/kidsmap`. Original dirty checkout preserved.

## Changes
- AZ/RU/EN: four situation sections (toddler, rain, free visit, schoolchild), each linking to up to two currently public matching venues.
- Featured editorial order: Central Park (366), Happyland Park Bulvar (363), Carpet Museum (324), Baku Zoo (80), Tusi-Bohm Planetarium (294), Miniature Book Museum (287). Current public visibility/geography/deduplication still apply; stable topic-balanced fallback replaces missing choices.
- Shared age labels, program caveats and price summary displayed inside featured cards. Free entry with paid services, mixed tariffs and unknown prices retain their meanings. No invented family totals.
- Short localized editorial notes explain how to approach each featured venue. Existing URL, canonical/hreflang, publication date and other guide layouts preserved. Modification date updated to 2026-11-05.

## Verification
- RED: new tests reproduced missing comparison/scenario UI and unstable featured ordering.
- Initial GREEN run exposed an invalid unknown-price fixture. Fixed the fixture with an active `on_request` tariff, preserving public eligibility and expectations.
- 30 focused Django tests passed.
- Final regression: **93 Django tests passed** across all five parent guides, images, homepage parent intent, shared public age notes and current pricing contracts.
- **9 Node navigation tests passed**. The historical jsdom path was absent; installed jsdom 26.1.0 in this ignored local QA directory only.
- Browser: **12 responsive states passed** (AZ/RU/EN × 320/375/768/1280), with four scenarios, six comparison cards, no horizontal overflow or clipped new content. Visually inspected RU desktop/mobile, AZ/EN narrow screens. New scenario link opened the correct Central Park detail page and browser Back returned to the guide. No browser console warnings/errors or broken rendered card images observed.
- **21 unique venue links** from rendered AZ/RU/EN pages returned HTTP 200 locally.
- Canonical and all four language alternates present; existing schema tests pass. `git diff --check` passed.

Test command (from this worktree):

```sh
/home/ramin/kidsmap/.venv/bin/python .tmp/baku-guide/runner.py test catalog.testcases.test_baku_guide_choices catalog.testcases.test_parent_guides catalog.testcases.test_parks_guide catalog.testcases.test_museums_guide catalog.testcases.test_play_centers_guide catalog.testcases.test_parent_guide_images catalog.testcases.test_home_parent_intent catalog.testcases.test_public_age_notes catalog.testcases.test_current_pricing_contract --noinput --keepdb
NODE_PATH="$PWD/.tmp/baku-guide/node/node_modules" node --test scripts/tests/parent_guide_links.test.cjs
```

Logs: `.tmp/baku-guide/regression2.log`, `links2.log`, `browser-checks.json`, `http-checks.json`.

## Preview and limits
- RU: http://127.0.0.1:8774/ru/parents/baku-with-kids/
- AZ: http://127.0.0.1:8774/parents/baku-with-kids/
- EN: http://127.0.0.1:8774/en/parents/baku-with-kids/
- Preview data: ten public venue records fetched through public pages on 2026-11-05, with public images and translated price labels. This is a bounded fixture, not the production database or the complete catalog. Numeric/mixed public labels were preserved as labels rather than guessed tariff rows. Real structured tariff behavior is covered by tests.
- `DJANGO_TESTING=1`; process environment cleared before settings import; isolated SQLite, locmem cache, local email, media and compiled locale paths. No production credentials or connections.
- SQLite emitted the existing warning that nulls-distinct uniqueness on SpecialistEmployment is unsupported. PostgreSQL constraints, whole-project regression and production deployment were not tested in this scope. No schema changes were made.
- Local preview server is listening only at 127.0.0.1:8774; runner: `.tmp/baku-guide/runner.py runserver 127.0.0.1:8774 --noreload`.

## Visual revision requested after review

Replaced the plain scenario rows with four illustrated pastel cards. Generated four original transparent illustrations using the built-in `image_gen.imagegen` tool; encoded them as WebP with alpha preserved (735,594 bytes total). Artwork files: `static/img/guides/family-toddler.webp`, `family-rain.webp`, `family-free.webp`, `family-schoolchild.webp`. Exact prompts and paths: [art manifest](baku-guide-art-prompts-2026-11-05.json).

Added gentle independent floating artwork, hover lift, link arrows, and existing intersection reveal. Text and links do not float. A native keyboard-accessible checkbox pauses/resumes all four illustration loops without JavaScript. The dedicated stylesheet disables animation/transitions under `prefers-reduced-motion`; OS reduced-motion rendering was not emulated by the available browser API.

Fresh validation of this visual revision:
- 34 Django guide/choice/image tests passed (`visual-tests.log`).
- 9 existing Node navigation/motion checks passed (`visual-links.log`).
- 15 browser sizes/languages passed: AZ/RU/EN × 320/375/768/1024/1440; no document overflow or clipped text; eight venue links; smallest link touch target 48px.
- Four images loaded; native checkbox changed every image from `running` to `paused` and back; keyboard Tab reached the first venue link; desktop hover computed transform was `translateY(-5px)`; no console warnings/errors observed.
- Desktop RU and mobile EN inspected visually. Evidence: `.tmp/baku-guide/visual-scenes-ru.jpg`, `visual-mobile-en.jpg`, `visual-responsive.json`.
- `git diff --check` passed. Remains local only; no deploy, commit or push.
