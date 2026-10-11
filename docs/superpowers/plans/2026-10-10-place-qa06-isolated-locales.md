# PLACE-QA-06 — Isolated compiled translation build implementation plan

> **For agentic workers:** Execute only after the user approves this scope. Use `systematic-debugging`, `writing-plans`, `test-driven-development`, `playwright` and `verification-before-completion` as applicable. One sequential executor. No commit/push/deploy, no modifications of shared compiled assets or correct PO source. PLACE-QA-01–05 remain separate scopes.

**Goal:** Изолированный локальный стенд использует каталоги, собранные из текущих `.po`, и отказывается запускаться с отсутствующим, изменённым или устаревшим результатом сборки.

**Architecture:** Отдельная локальная CLI-команда собирает GNU `.mo` в новый принадлежащий запуску каталог под `.tmp`, сохраняет manifest исходников/результатов и предоставляет read-only проверку manifest. QA launcher выполняет эту проверку до `django.setup()` и задаёт `LOCALE_PATHS` только для проверенного каталога. Общие `locale/**/*.mo`, `.po`, Docker/CI/release и конфигурация приложения остаются вне области изменений.

**Tech Stack:** Python 3.12.15 stdlib, installed WSL GNU gettext `msgfmt` 0.21, Django 6.0.2, isolated PostgreSQL 17 and Playwright Chromium headless shell 153.0.8010.12.

**Spec:** [PLACE-QA-06](../../qa/module01-2026-10-09-r2/findings/PLACE-QA-06.md). [Fresh source/asset/browser evidence](../../qa/place-qa06-plan-2026-10-10/REPORT.md).

## Snapshot and constraints

- PLAN / AWAITING USER SCOPE APPROVAL. `C:\kidsmap`, branch `task33-progress`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, `active_run: NONE`.
- Preserve incoming QA register/module directories, all prior finding plans/evidence and foreign stands. This is an environment/generated-asset finding; it does not demonstrate a production defect.
- No production credentials, external integrations, system gettext installation, source PO rewrites, migration/deploy/release execution or modification of foreign `.mo` files.
- Tests use `DJANGO_TESTING=1`, dedicated DB/test DB/cache/media/private-media/email and synthetic records; no inherited service environment or `.env` loading.
- Do not run `scripts/release-server.sh` for this task: it migrates data and deletes shared `.mo` files before compilation. Existing Docker/CI compile steps are read-only references, not targets to run or edit.
- Do not use `--use-fuzzy`, suppress GNU format errors or fall back silently to a different compiler. If current source cannot compile, preserve diagnostics and report the exact blocker instead of modifying PO outside scope.

## Verified baseline / build boundary

All five target PO entries in each locale are present and non-fuzzy: descriptions AZ/RU/EN, map-warning title and full map-warning body. Direct GNUTranslations checks: RU 5/5 matches; AZ 0/5, EN 0/5. Current shared `.mo` files are older than their PO source. They are ignored by Git, so a clean tracked application diff does not establish a current translation build.

Fresh browser on byte-identical frozen copies of those existing `.mo`: RU/AZ/EN at 390 × 900, three content-language tabs, initial load and reload. Thirty string comparisons: 10 PASS / 20 FAIL. HTML language is correct, local resource failures and page errors are zero. AZ shows `Cədvəl`, EN shows `Schedule`, and both fall back to Russian map warnings.

Dockerfile and CI already run `compilemessages`. Installed Django uses `msgfmt --check-format` and skips outputs by mtime. That skip is not the observed cause here (current MO files are older); a new empty output plus hashes avoids trusting timestamps in future local stand preparation.

## Allowed files / ownership

| File | Proposed change |
|---|---|
| `scripts/build_isolated_locales.py` (new) | Local build/verify CLI without Django settings or DB access |
| `scripts/tests/test_build_isolated_locales.py` (new) | Compiler, manifest, freshness and output-ownership regressions |
| `docs/qa/isolated-locale-build.md` (new) | Reproducible local commands and mandatory stand preflight |
| `docs/qa/place-qa06-fix-2026-10-10/` (new) | Isolated launcher/settings, native command ledger, lookup/browser/save-reload results and screenshots |
| `.tmp/place-qa06-fix-20261010/` (ignored, new) | Owned PO snapshots/MO outputs/manifest, DB fixture media, private-media and browser state |

No edits to `locale/**/*.po`, shared `locale/**/*.mo`, `src/config/settings.py`, templates, JS/CSS, Dockerfile, workflow or release scripts. Compiled binaries and synthetic credentials remain ignored local artifacts; reports contain hashes/paths and targeted public UI strings only.

## Task 1: Build/verify contract and RED regression

- [ ] Recheck HEAD/WORKTREE/active_run, current PO/MO hashes and existing stand ownership. Record approval and create a new fix evidence directory. Reuse this audit's read-only comparison and frozen-baseline approach; do not mutate planning evidence.
- [ ] Create the CLI with two subcommands: `build --source-locale PATH --output PATH --locales ru az en --compiler wsl|native` and `verify --manifest PATH --source-locale PATH`. Default source is repository `locale`; output must be explicit. The tool must not import application settings, load `.env`, connect to DB or launch a server.
- [ ] Restrict writable output to a new descendant of resolved `C:\kidsmap\.tmp` (or the equivalent checkout root on another host). Reject existing output directories, symlinks/junctions and paths resolving outside that boundary or onto source locale. Offer no overwrite/force option. `verify` must be read-only.
- [ ] Add meaningful tests before implementation: successful singular/context/plural lookup; fuzzy entries omitted; GNU format error causes failure/no complete manifest; existing output and source paths refused without byte changes; source changed with preserved mtime rejected; missing/tampered MO rejected; missing/incomplete manifest rejected; unchanged input builds yield identical MO hashes with the same compiler/options.

```python
# Behavioral shape; helper builds a minimal synthetic catalogue in owned scratch.
first = build_fixture_catalogue(output=run_root / 'first')
second = build_fixture_catalogue(output=run_root / 'second')
self.assertEqual(first.mo_sha256, second.mo_sha256)
original_times = source_po.stat().st_atime_ns, source_po.stat().st_mtime_ns
source_po.write_text(changed_source, encoding='utf-8')
os.utime(source_po, ns=original_times)
verification = run_verify(first.manifest, source_locale)
self.assertNotEqual(verification.returncode, 0)
self.assertEqual(first.mo_path.read_bytes(), first.mo_bytes)
```

Implement test helpers using subprocess argv lists and fresh `.tmp` fixtures; use actual GNU msgfmt for compiler behavior. No app model data is needed for these tool tests. Run `.venv/Scripts/python.exe -m unittest discover -s scripts/tests -p test_build_isolated_locales.py`; retain RED output/native exit before implementation.

## Task 2: Compile into an owned output and verify provenance

- [ ] Enumerate the requested locales' `LC_MESSAGES/*.po` deterministically, require their presence, and freeze byte-identical PO inputs under the new output directory. Check source hashes before and after copying; fail if source changed during capture. Do not copy old MO files into the new build.
- [ ] Invoke installed GNU msgfmt directly with `--check-format --statistics --endianness=little`, without fuzzy inclusion. Native compiler uses its executable path. WSL mode uses `wsl.exe --exec wslpath -u` for each absolute file path and then an argv list, never an interpolated shell command. Example compiler invocation for one frozen source:

```text
wsl.exe --exec msgfmt --check-format --statistics --endianness=little -o /mnt/c/kidsmap/.tmp/place-qa06-fix-20261010/locale-build-01/locale/az/LC_MESSAGES/django.mo.tmp /mnt/c/kidsmap/.tmp/place-qa06-fix-20261010/locale-build-01/source/az/LC_MESSAGES/django.po
```

- [ ] Decode each output with `gettext.GNUTranslations` before publishing it to its final path inside the owned output. Record compiler executable/mode/version/options/native exit and source/snapshot/asset SHA-256. Write a complete manifest only after every requested locale/domain succeeds; failed partial outputs must not be accepted by `verify` or a stand launcher.
- [ ] Manifest records schema version, locales/domains, relative source paths, source and compiled hashes, compiler identity and resolved locale root. `verify` checks all source files against current content, checks output hashes/readability/path containment and rejects incomplete or mismatched manifests. Do not rely on mtime or a directory merely existing.
- [ ] Document the concrete build/preflight commands:

```powershell
.venv/Scripts/python.exe scripts/build_isolated_locales.py build --source-locale locale --output .tmp/place-qa06-fix-20261010/locale-build-01 --locales ru az en --compiler wsl
.venv/Scripts/python.exe scripts/build_isolated_locales.py verify --manifest .tmp/place-qa06-fix-20261010/locale-build-01/manifest.json --source-locale locale
```

The directory must be new. A subsequent build uses another owned suffix, not a force rebuild over shared assets. Re-run the tool tests to GREEN and include a real build from the current project PO files.

## Task 3: Mandatory local-stand preflight and fresh process

- [ ] Adapt the audit's isolated QA runtime into the fix evidence directory. Use a new container/DB namespace, suggested `kidsmap-placeqa06-fix-20261010`, DB `placeqa06_fix`, test DB `test_placeqa06_fix`, loopback DB 55443 and HTTP 8822; recheck name/port availability first. Use the available `postgres:17-alpine --pull=never`, no existing foreign DB.
- [ ] The fix launcher runs `verify` before Django setup and refuses to start on nonzero exit. Its standalone settings set `LOCALE_PATHS` to the verified manifest's owned `locale` directory. Never append the shared root locale as an alternative; report the actual resolved path.
- [ ] Use a fresh Django process after choosing the catalogue. Do not modify private translation caches in a running worker or restart a foreign stand. Leave fallback catalogues supplied by installed Django/apps under their normal behavior; the project catalogue path is the verified one.
- [ ] Prove the startup gate by altering only a disposable fixture source or asset: preflight must fail and HTTP must remain unbound. Restore via a separate fresh build. Project PO/MO files must retain their original hashes throughout these tests.
- [ ] Verify all 15 targeted GNU lookups against current PO, then repeat in a fresh Django translation context/process. Expected descriptions: `Təsvir (AZ/RU/EN)`, `Description (AZ/RU/EN)` and unchanged RU. Map title/body must match the corresponding full PO messages. Check exact active LOCALE_PATHS and compiler/source/asset hashes in the report.

## Task 4: Real browser and save/reload acceptance

- [ ] Using only synthetic admin/place data, repeat the audited RU/AZ/EN flow. Open all three content-language tabs and verify each description label, map-warning title/body and correct HTML language before and after reload. Compare native browser strings with PO-derived expectations; record local static failures and deliberately blocked external fonts separately.
- [ ] Check affected labels/warnings at 390/768/1024/1280/1440, with fresh screenshots and no clipped evidence under sticky bars. Preserve the UI layout; new overflow or unrelated translation defects are reported separately rather than fixed in PO/CSS under this scope.
- [ ] Save a valid synthetic draft through admin with distinctive description text, reload and confirm both the translated label and persisted description field. Verify unrelated schedule/title/address fields are unchanged. This catches saving through a mislabeled field without claiming a source/UI rewrite. Use normal form validation; do not bypass failures by direct DB writes.
- [ ] Keep a same-run manifest linking PO hashes, MO hashes, resolved runtime path, process/browser versions and screenshots. A successful compiler alone does not prove that the running process loaded its output.

## Task 5: Preservation and final handoff

- [ ] Record exact commands/native exit codes, RED/GREEN comparisons, failed preflight cases, browser save/reload and explicit NOT RUN limits. Recheck shared PO/MO hashes, tracked application diff, prior plans, active_run and foreign stands.
- [ ] Close only the owned browser/server/container using creation records. Do not remove shared compiled assets, run release scripts or perform broad cleanup.
- [ ] Report PLACE-QA-06 resolved for the verified isolated build only when tool tests, current-PO compilation, startup preflight, effective lookups and rendered save/reload pass. Do not claim the common WORKTREE assets, other stands, Docker images or production were updated. Document build/verify as the required preparation step for future local QA runs.
