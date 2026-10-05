# Stage21 independent browser review — PASS

Actual delegated reviewer: canonical `browser-qa`. Bounded local AUDIT;
ownership only `docs/task33/qa21/*` and this report. No application changes,
production, commit/push/deployment or later stages by this reviewer.

LOCAL HEAD: `task33-progress`, `015d031d8eb17114bd860159dde805b38df3c13c`, plus
the lead's stage21 worktree. PRODUCTION UNKNOWN, not contacted. This PASS covers
the synthetic browser scope below, not the whole application or production.

## Executed evidence

| Check | Actual result |
|---|---|
| Five surfaces × AZ/RU/EN ×320/360/390/768/1024/1280/1440 | **105/105 PASS**, HTTP200 |
| Canonical/hreflang and separately identified entity JSON-LD | PASS105; valid JSON, correct approved language targets |
| Fallback/closed notices, shell headings, overflow, icon font | PASS105; zero horizontal overflow |
| AZN currency, AZ geography, factual entity schema | PASS; no invented Organization/Course rating/dates/geo |
| Hostile `</script>` text | Remains text/data; injected marker false |
| Stable review and real generated fixture image | PASS21 complete-place combinations; image loaded, no404 |
| Class language `en`, schedule `Şənbə 10:00`, price25 | Preserved on all21 activity combinations |
| Legacy `/place/<pk>/` in three locales | Three redirects to correct same-locale stable path, then200 |
| Matrix console/network/static errors | 0 console errors, 0 failed requests, 0 HTTP4xx/5xx |
| Final-source head follow-up | **15/15 PASS** after final explicit-offer-locale fix |
| Desktop keyboard1280 | Enter opens; Tab AZ→RU; Enter follows RU path, htmlRU |
| Mobile keyboard390 | Enter opens drawer; RU Enter follows RU path, htmlRU |
| Final fresh-browser console/network | 0 messages/errors/warnings; no failures/404/500 |
| Accepted matrix and final follow-up QA04 cleanup | Both child0/statusPASS/cleanupPASS, both temp roots removed |

Surfaces: AZ-only Place, fully translated Place, approved closed Place,
AZ-only approved Organization with hostile synthetic text, approved Activity
with Program inheritance/group/price. Fully translated Organization/Activity
combinations are backend-review scope. No private/publication browser mutations.

Raw evidence outside Git:

- `/root/task33-evidence/browser21-accepted-20261003/`: actual105 DOM facts,
  `matrix-rechecked.json`, `summary-rechecked.json`, source manifest,30 screenshots,
  original validator output, normal `launcher/run.json`.
- `/root/task33-evidence/browser21-final-verified-20261003/`: final15 facts,
  desktop/mobile keyboard results, source manifest, console/request logs,
  normal `launcher/run.json`.

Reviewer inspected actual accepted screenshots: EN fallback320, RU closed390,
EN Organization1280, RU Activity1280. Copies in ignored
`output/playwright/qa21/accepted-*.png`. Notices readable, hostile text visibly
inert, corrected Lesson/breadcrumb labels translated, class/schedule facts stable.
Full-page captures can include unrevealed scroll animations below the viewport;
blank screenshot space is not evidence of a missing footer.

## Snapshot and commands

Manifests conservatively hash1621 application-source files, all Windows bytes
matching actual Linux mirror bytes. This is not the actual changed-file count:
Linux Git sees Windows CRLF differences. No env/media/DB/compiled-catalog hashing.
Between105 matrix and final15 only two recorded source hashes changed:

- `src/catalog/services/public_presentation.py` final SHA256:
  `dd06ee23de45f403179d0bd262239cc1ee972462f55f505016027875cfcc13f0`.
- `src/catalog/testcases/test_task33_localization.py` final SHA256:
  `96380fb25c7b65c3cf2de2d93b28f05a166af2c2a6296bfd2305f2c35e17567e`.

Final change supplies explicit offer-label locale outside ambient request locale;
browser routes already used their current locale. Final15 checks confirm final
mirrored source; templates/CSS/UI unchanged after105 matrix.

Executed under WSL Ubuntu24.04, immutable helper copy:

```bash
bash /root/task33-browser-tools/run-browser-frozen.sh accepted-20261003
python3 /mnt/c/kidsmap/docs/task33/qa21/recheck.py /root/task33-evidence/browser21-accepted-20261003
bash /root/task33-browser-tools/run-browser-frozen.sh final-verified-20261003 final-smoke
npx playwright-cli -s=qa21 console error
npx playwright-cli -s=qa21 requests
```

Unchanged QA04 launcher/guards: disposable PostgreSQL17, network-none/tmpfs/Unix
socket, synthetic credentials, LocMem cache/email, temporary media, no external
integration credentials. Anonymous bridge exposes fixed read-only synthetic
public routes, one generated image, static finder resources and bounded font/
control routes on127.0.0.1:8781. ThreadingHTTPServer avoids speculative-connection
deadlock. External scripts explicitly stubbed. Public Material Symbols font was
cached during setup outside Git; runtime font and kidsmap.az display navigation
intercepted/served locally. Live site/providers never HTTP destinations.

Outside-Git tools: Node22.23.3, CLI0.1.22, Playwright1.64.0-alpha-1790635538000,
Chromium155. Python3.12/Django6.0.2. Apt Node18 incompatibility corrected locally.

## Findings and harness history

- **B21-01 / environment:** absent ignored `.mo` caused EN/AZ shell Russian
  fallback. Lead compiled three catalogs; fresh rendered shell checks pass.
- **B21-02 / P2 / application:** EN pricing rendered `Занятие` from fuzzy/wrong
  gettext entry. Lead corrected narrow entry; accepted screenshot shows Lesson.
- **B21-03 / P2 / application:** fallback EN breadcrumbs used canonical AZ
  labels. Lead separated shell navigation from canonical JSON-LD language;
  accepted screenshot shows Home/Catalog/Education.

No confirmed application finding remains in this bounded review. Preliminary
harness failures corrected/retained: missing `dump` re-export; editing executing
shell helper; choosing site-wide Organization instead of entity schema;
transition/deferred-navigation timing; single-thread speculative-connection
deadlock; Chromium loopback-font permission after virtual HTTPS navigation.
Entity selector now requires canonical URL. Raw105 facts were rechecked with
strict expected type/currency/geo/closed-fact assertions; original validator
failures remain in archive. This was a selector correction, not relaxed evidence.

One interrupted preliminary launcher did not persist its original nonce record.
Its specifically identified container was removed after repeated name/label,
exact creation time, exclusive expected bind, network-none/tmpfs checks.
Separate `browser21-final-20261003/cleanup-recovery.json` records recovery;
standard cleanup for that preliminary run is UNKNOWN, not PASS. Unknown temp
roots preserved. Final accepted launchers completed normal nonce-guarded cleanup.
Single-thread timeout was released by closing only qa21 browser and finishing its
own launcher; that run also completed normal cleanup.

## Research boundary and handoff

Registry/role, engineering/audit contracts and READ FIRST navigation read.
Codebase Memory `C-kidsmap` callable/ready; header partial with changed metadata,
qa21 untracked. Graph `public_entity_detail` search returned no matches; actual
routes/selectors/gettext/templates verified. Graph absence not deletion evidence.
Context7 unavailable. Playwright skill CLI-first, real rendered run-code, no
jsdom or `@playwright/test` specs.

NOT RUN by this role: production/providers/accounts/media, whole app suite,
admin/owner writes, sitemap query budgets, publication/migration checks, full
accessibility audit, Escape-specific acceptance, later stages. Backend evidence
belongs to lead/integration reviewer.

Named handoff: `/root` may incorporate bounded browser PASS and final snapshot
into stage21 report/journal; `integration-reviewer` owns final backend/regression
decision. No independent production-readiness claim.
