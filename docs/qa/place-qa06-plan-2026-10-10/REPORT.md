# PLACE-QA-06 — source/compiled/runtime baseline and proposed scope

Date: 2026-10-10, Asia/Baku. AUDIT / PLAN. One sequential executor `/root`, canonical orchestrator/release-reviewer/browser-qa responsibilities; no independent specialist execution claimed. No application or translation build implementation was performed.

## Snapshot, isolation and authorization

Actual checkout `C:\kidsmap`, branch `task33-progress`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, `active_run: NONE`. [Snapshot](snapshot.json) includes the incoming QA register/module directories and five earlier finding plans. PRODUCTION was not accessed; production state remains UNKNOWN.

Created a fresh owned container `kidsmap-placeqa06-plan-20261010`, local `postgres:17-alpine --pull=never`, DB `placeqa06_plan` on loopback 55442. Actual rendered endpoint: `http://127.0.0.1:8821/admin/catalog/place/1/change/`, synthetic superuser and synthetic draft place. No production credentials or inherited service environment, no `.env`, dedicated media/private-media, LocMem cache/email; backend and browser external transport blocked. [Isolation metadata](isolation.json).

All three shared PO/MO pairs were read and copied byte-for-byte to ignored `.tmp/place-qa06-plan-20261010/baseline-locale`. The stand's `LOCALE_PATHS` points only to this frozen baseline copy, giving stable reproduction without changing another stand's catalogues. [Frozen copy hashes](frozen-catalog-manifest.json), [bootstrap](bootstrap_audit.py), [stand settings](qa06_settings.py). **No catalogue was compiled.**

## Direct source versus compiled comparison

[Read-only inspection](inspect_catalogs.py) parses only the five singular, non-context target entries in each PO (including wrapped strings), checks their presence/flags, and reads the corresponding MO with Python `gettext.GNUTranslations`. This narrow parser is diagnostic tooling, not a proposed replacement for GNU gettext compilation.

| Target | AZ current PO | AZ current MO | EN current PO | EN current MO |
|---|---|---|---|---|
| Description AZ/RU/EN | `Təsvir (AZ/RU/EN)` | `Cədvəl` for all three | `Description (AZ/RU/EN)` | `Schedule` for all three |
| Map-warning title | `Xəritə hazırda əlçatan deyil` | Missing key; Russian fallback | `Map currently unavailable` | Missing key; Russian fallback |
| Full map-warning body | Current Azerbaijani message | Missing key; Russian fallback | Current English message | Missing key; Russian fallback |

All 15 target PO entries are present and non-fuzzy. GNU comparisons: **5 PASS / 10 FAIL**, all failures AZ/EN; RU agrees. [Exact strings, flags, key presence and hashes](catalog-comparison.json). Current MO mtimes precede PO mtimes in all three locales; the mismatch does not establish an mtime-skip failure.

`.gitignore:60` ignores `*.mo`. `src/config/settings.py:LOCALE_PATHS` normally points to the shared root locale directory. Correct tracked PO and an empty tracked application diff therefore do not prove the runtime translation build is current.

## Fresh rendered browser evidence

Installed Playwright Chromium headless shell **153.0.8010.12**, desktop viewport 390 × 900, DPR 1. RU/AZ/EN, initial load and real reload, each of the three content-language tabs opened. [Browser strings/network](browser-baseline.json), [source-derived browser assertions](browser-assertions.json).

**30 string comparisons: 10 PASS / 20 FAIL.** RU passes in both phases; every targeted AZ/EN string differs from PO before and after reload. All six HTML language checks match the selected locale. Local resource failures: **0**; page errors: **0**. Google font requests were deliberately blocked; fallback fonts were used.

Representative images: [AZ description after reload](screenshots/az-reload-description-az.png), [EN description after reload](screenshots/en-reload-description-az.png), [RU description after reload](screenshots/ru-reload-description-az.png), [AZ map warning](screenshots/az-map-visible.png), [EN map warning](screenshots/en-map-visible.png). [Manifest](screenshots-manifest.json) records all 27 image hashes/dimensions.

The first 24 component screenshots cover descriptions/map on initial/reload. Some map element screenshots intersect sticky mobile navigation; three additional viewport screenshots deliberately scroll the warning below that bar and provide readable map evidence. No styles, translations or DOM text were patched for screenshots.

The first browser script attempt exited 1 on an ambiguous tab selector (three independent language-tab groups). The audit selector was narrowed to the actual description-tab ID; the repeated run completed and produced the accepted evidence. This was a harness error, not an application failure. The complete native CLI results remain in [browser command ledger](browser-command-ledger.jsonl).

## Build path and proposed correction

Verified references: Dockerfile compiles translations into the image; `.github/workflows/deploy.yml` also runs compilation. `scripts/release-server.sh` removes shared MO outputs and recompiles, but it also mutates data and was **not executed**. Installed Django `compilemessages` invokes `msgfmt --check-format` and uses an mtime shortcut. Native Windows `msgfmt` was unavailable; WSL GNU gettext **0.21** is already installed. No tool installation or compilation was performed.

Codebase Memory project/root/status was checked first. Graph search found no compile helper under `scripts`; coverage had known gaps/metadata changes, so literal searches confirmed the bounded Docker/CI/script references. PO paths have partial parser coverage. Source and runtime evidence, not graph absence, support the conclusion.

[Reviewable implementation plan](../../superpowers/plans/2026-10-10-place-qa06-isolated-locales.md): add a local build/verify tool, hash manifest and mandatory preflight for the isolated QA launcher; compile into a new owned directory and start a fresh Django process using that path. Preserve correct PO, shared MO, existing build/release configuration and other stands. P2 remains an **environment/generated-asset staleness** finding, not a demonstrated production or current-PO defect.

## Commands, preservation and limits

- `.venv/Scripts/python.exe docs/qa/place-qa06-plan-2026-10-10/inspect_catalogs.py` — exit 1: expected RED, 15 checks / 10 mismatches; no assets written.
- `.venv/Scripts/python.exe docs/qa/place-qa06-plan-2026-10-10/bootstrap_audit.py` — exit 0: harness plus six byte-identical baseline copies.
- `.venv/Scripts/python.exe docs/qa/place-qa06-plan-2026-10-10/prepare.py` — exit 0: fresh owned PostgreSQL, isolated migrations and synthetic fixture/session.
- `runtime.py serve` — owned loopback server only; stopped after browser evidence by verified PID/script identity, process exit 1 from intentional termination.
- `pw.py run-code --filename` with [browser baseline](browser-baseline.js) — effective exit 0. [Visible map capture](browser-map-evidence.js) — exit 0. Native argv/output are in the browser ledger; generated authentication state remains only in ignored scratch.
- `.venv/Scripts/python.exe docs/qa/place-qa06-plan-2026-10-10/collect_browser_results.py` — exit 1: expected RED, 30 comparisons / 20 mismatches.
- `.venv/Scripts/python.exe docs/qa/place-qa06-plan-2026-10-10/verify_plan.py` — exit 0: evidence and preservation checks passed; the translation comparisons remain RED.
- [Final command ledger](command-ledger.jsonl) and [verification](plan-verification.json) record source/copy preservation, test exits, document links, screenshots and owned-resource shutdown.

Final preservation: all captured input hashes agree, including all shared PO/MO files and prior plans; application/build-source diff is empty. Owned browser/server/container are stopped, the container is retained. All initially running foreign stands remain running. A new foreign stand `kidsmap-module06-20261010-r1` on loopback 55437 appeared during this audit; it was not touched, and final inventory equality is therefore false.

NOT RUN: fresh PO compilation, proposed build/verify tool and tests, corrected-catalog Django/browser checks, DB save/reload of edited descriptions, full responsive matrix, restricted moderator ACL, other browsers/devices, complete backend suite, Docker/CI/release execution, external integrations and production. A browser reload was run; a form save was not. Prior finding approvals remain pending.
