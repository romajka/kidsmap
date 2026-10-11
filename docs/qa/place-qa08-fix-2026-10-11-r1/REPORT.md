# PLACE-QA-08 / CROSS-QA-03 — scoped repair and fresh verification

2026-10-11, Asia/Baku. Executor `/root`, canonical kidsmap-orchestrator and browser-qa definition read; execution in this chat, no independent specialists. Mode **APPROVED IMPLEMENT**, user instruction «Выполняй PLACE-QA-08 по плану». [Approved plan](../../superpowers/plans/2026-10-11-place-qa08-district-placeholder.md).

**PLACE-QA-08 / CROSS-QA-03 is fixed and passes the scoped fresh checks in dirty WORKTREE with newly compiled isolated RU/AZ/EN. Full module01 acceptance remains NOT RUN.** Common/shared MO and other runtime locale profiles were not rebuilt or verified as current.

## 1. State and snapshot

Checkout `C:\kidsmap`, branch `task33-progress`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, dirty WORKTREE preserved. `active_run: NONE`. [Entry inventory](entry.json), [foreign file hashes](foreign-entry.json), [runtime snapshot](runtime-snapshot.json), [runtime attestation](runtime-version.json), [isolation](isolation.json).

Own HTTP `http://localhost:8842`, PID19364; PostgreSQL loopback55447, DB `qa08_district`, container `kidsmap-place-qa08-fix-20261011-r1` ID `f2061c17580d837d81c563bef149b1e2a34918eb8d7f3189d2bd0fd1577dfc9b`, volume `9e3bb58a25137289648632676cb910594bf2dc1a5fec6e188f5fd59f82ad34bf`. Browser session `place-qa08-fix-r1`, Chromium headless shell. Python3.12.15, Django6.0.2, DJANGO_TESTING=1, DEBUG=False. Sole LOCALE_PATHS points to `.tmp/place-qa08-fix-20261011-r1/fixed-locales/locale`; manifest verified before django.setup. LocMem cache/email and own media/private-media, synthetic owner/photo/Place only. No production connection or inherited production credentials.

Runtime source digest `bf13ba902d73b8ab4b60e33919f8b4fe8873e68bf473e90b95511c2e6f51bdc8`,2789 source files, snapshot=startup=disk. Shared MO preserved; the fresh PO/MO key/SHAs are in [compiled proof](compiled-locales-proof.json).

## 2. Change and successful checks

In `locale/ru/LC_MESSAGES/django.po:18354`, only two obsolete `#~ ` markers were removed for `msgid/msgstr "Выберите район"`. All other original PO bytes are preserved; prior WORKTREE nature translations were retained. [Exact PO change proof](po-change.json), [applier](apply_fix.py).

New `src/catalog/testcases/test_place_qa08_district_localization.py` verifies the consumer-visible rendered empty option/gettext language and stable submitted district codes. `configure_location_choices`, geographic validation, request-language/fallback policy, ACL and existing assertions were unchanged.

| Check | Fresh result | Evidence |
|---|---|---|
| RED before PO change |2 tests,1 expected RU FAIL: Rayon seçin; code-set check PASS; exit1|[RED](django-red-confirmed.txt)|
| GREEN new tests + manual location + existing nature tests |6/6 PASS, exit0|[Django](django-green.txt)|
| Fresh compilation and manifest verification |baseline/fixed builds exit0; fixed verify exit0|[build](build-fixed.txt), [verify](verify-fixed.txt)|
| Owner RU/AZ/EN ×360/390/768/1024/1280/1440 |75 PASS,0 FAIL, CLI exit0|[raw matrix](placeholder-matrix.result.json)|
| Native district save/reload and public address |12 PASS,0 FAIL, CLI exit0|[roundtrip](roundtrip.result.json)|
| Runtime provenance and preservation |see final checks/counts|[verification](verification.json)|

RU is «Выберите район», AZ «Rayon seçin», EN «Select district». Native mouse/keyboard opens the select, Escape retains focus, Home/Enter selects the empty item; selected label, focus and control geometry pass at all18 cells. The empty selection is **SIMULATED unsaved state**, with non-GET blocked after login in its own browser context. Before/after read-only state compares the full candidate payload hash and live fields; both remain unchanged.

Separate normal browser contexts perform native `save_draft` POST and reload on all three languages. `baku_yasamal` persists, live district/address/names/nature stay identical, candidate effective district/address match, and public address remains rendered unchanged. Only initial synthetic fixture creation uses ORM; audited transitions use native forms. DB readback uses explicit READ ONLY transaction and timeouts.

Total browser result **87 PASS /0 FAIL observations**, not87 independent end-to-end tests. [Counts](counts.json), [CSV matrix](matrix.csv), [commands](COMMANDS.md), [command ledger](command-ledger.jsonl).

## 3. Real issue and closure

One root cause and alias only: PLACE-QA-08 = CROSS-QA-03, P3 wrong-language empty district option. Source `_('Выберите район')` in `locations.py:561` was present, RU PO entry was obsolete; fresh baseline RU MO lacked the key while AZ had it. RED reproduced the actual Django fallback to AZ. Fixed RU MO now contains the active mapping. No change to district codes or fallback implementation was needed.

Status **CLOSED within this WORKTREE/fresh isolated profile**. Clean HEAD and deployed application status are not inferred. PLACE-QA-01–07 were not reimplemented or fully reaccepted here; their prior fresh recheck remains separate evidence.

## 4. Tech debt and own QA corrections

The original plan's new test assumed identical option ordering across languages. Source sorts translated labels; the first own test run retained the expected RU failure plus this incorrect oracle. Only the new code-set assertion was corrected, then RED repeated with exactly one RU failure. Existing assertions were never weakened.

First Windows shell log displayed damaged non-ASCII; the UTF-8 subprocess recorder was used for the confirmed RED/GREEN evidence. Installed Chrome failed during own automation launch; the available Chromium headless shell succeeded. These are QA/environment events, not application regressions. An early contact-sheet read preceded aggregate completion; later rendering and visual reads succeeded.

## 5. Risks and integration limits

No pageerror and no local HTTP>=400 in final scripts. There are54 console `net::ERR_FAILED` messages, from intentionally blocked Google Fonts/unpkg Leaflet GETs. External resources can use font fallback. Real provider/GPS/SDK integrations are NOT RUN; this scope does not validate them. All locale builds reuse existing GNU msgfmt helper; shared MO and other launchers were untouched.

24 native viewport PNGs are retained with [SHA/dimensions manifest](screenshots-manifest.json). Six contact/crop sheets are **DERIVED**, not extra browser captures. All18 placeholder captures were visually inspected through [RU contact](contact-ru.jpg), [AZ contact](contact-az.jpg), [EN contact](contact-en.jpg) and the three label sheets; five original full-size PNGs were additionally inspected (RU390/1440, AZ390, EN390/1440). Manual full-size review of all24 PNGs is not claimed. Native menu popup imagery is not asserted: screenshots show the selected focused control; opening and selection are recorded native actions.

## 6. Dead/legacy candidates

None deleted. Only this exact obsolete translation pair was made active. Shared MO remain intact and require a separate runtime build decision. Graph absence was not used as deletion evidence.

## 7. Test gaps

Full module01, full configured backend/JS suites, full category/branch/gallery/schedule/ACL/concurrency/recovery acceptance, real external integrations/GPS, physical devices/other browser engines, full keyboard/screen-reader audit, clean-HEAD regression comparison, other runtime/shared-MO freshness and production are **NOT RUN**. Node/helper suites were not rerun because their implementation was unchanged; the existing builder was exercised by new baseline/fixed builds and manifest checks. [Explicit limits](limits.json).

## 8. Recommendations and handoff

Use the new report to close only PLACE-QA-08 / CROSS-QA-03 for the verified profile. Journal update is restricted to row01 with links preserving earlier evidence; other module rows and canonical/module13 MASTER_AUDIT remain unchanged. Next proposed scope is AUDIT ONLY of the missing full module01 acceptance, after the user's selection. [Next-chat text](next-chat.txt).

## 9. Priority and preservation

P3 PLACE-QA-08 closed within the tested scope. No new P0/P1/P2 or additional confirmed application defect established by this bounded run. Other project findings remain outside scope.

Finalizer checks hashes of pre-existing tracked/untracked artifacts, exact approved PO bytes, shared MO, other application source, HEAD/branch, active_run, foreign container identities/listener PIDs, own runtime source and credential absence before modifying only journal row01. Exact final result is [verification.json](verification.json) and [finalize.txt](finalize.txt). No commit/push/deploy/production; no foreign runtime restart.
