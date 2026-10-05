# Stage25 actual application browser review

Execution identity `/root/stage25_browser`, canonical `.agents/agents/browser-qa/agent.md`; independent of application implementers. Approved stage25 scope, user acceptance `specialist-25-r1` on2026-10-03. LOCAL HEAD `015d031d8eb17114bd860159dde805b38df3c13c`, branch `task33-progress`, dirty WORKTREE. Production NOT_CONTACTED;26+ NOT_RUN.

This review concerns actual Django screens, not the earlier design gallery. Harness ownership is limited to `docs/task33/qa25/application_*`, `application_bridge/`, this report and `25-application-browser-results.json`. Application source was not modified by this reviewer. Existing design QA helpers/evidence remain intact.

**Final bounded browser acceptance PASS.** Current coverage168/168contexts:126unaffected rows from final full matrix plus42corrective person/index contexts. Full380/380workflow/focus/ACL checks PASS, corrective84/84focus checks PASS. Unexpected page/console errors0, request failures0, static4040, horizontal overflow0. Separate source-current comparison2758/2758SHA MATCH, new application files0; all owned launchers cleanup PASS. Machine-readable evidence: [25-application-browser-results.json](25-application-browser-results.json).

## Environment and source boundary

Own allowlisted WSL mirror `/root/km25-browser-frozen`; existing Python virtualenv reused through a symlink, no dependency installation. Source copies include only src/templates/static/locale/config/scripts/qa04/qa25 and manage.py; no environment files, production records, graph caches or credentials. SHA256 inventory retained alongside every executed matrix outside Git.

QA04 clean environment and guards reused unchanged: DJANGO_TESTING=1, disposable PostgreSQL17.11, no network/ports, tmpfs data, owned Unix socket, isolated LocMem cache/email and public/private media. Python3.12.3/Django6.0.2/psycopg3.2.10. Loopback8785 bridge forwards requests to actual Django Client with `enforce_csrf_checks=True`, real fixture users and real POST/multipart payloads; it does not override views/permissions/validation. Actual private-document bytes are synthetic `%PDF-synthetic-only`. Cached Material Symbols font is served from loopback; other external CDN transport is stubbed and recorded. External integrations are NOT_TESTED.

Codebase Memory C-kidsmap callable, ready19466nodes/66978edges, generation2026-10-03T15:41:17Z. Requested changed paths had coverage_unavailable/metadata_changed, public template partial; graph completeness/freshness for edits remains UNKNOWN. Relevant model/services/controller/routes/templates were verified in source. No graph-negative removal claims.

## Executed evidence

Exact commands, run independently and checking sync success before launch:

```powershell
wsl -u root --exec /bin/bash /mnt/c/kidsmap/docs/task33/qa25/application_sync.sh
wsl -u root --exec /bin/bash /mnt/c/kidsmap/docs/task33/qa25/application_run-browser.sh initial2-20261003
wsl -u root --exec /root/km24-security/.venv/bin/python /mnt/c/kidsmap/docs/task33/qa25/application_diagnostics.py /root/task33-evidence/browser25-initial2-20261003
```

Initial2:168 actual rendered rows (public profile, person editor, index, invitation, claim, certificates, organization and dedicated reviewer) ×AZ/RU/EN×320/360/390/768/1024/1280/1440;126clean.42rows expose untranslated `Дипломы и сертификаты` in AZ/EN person/invitation/certificate UI. All380 checks PASS: keyboard focus/Tab, labels/CSRF, actual org proposal and separate consent, person confirmation, pending claim and reviewer verification, private-document seven-role HTTP boundaries, nested foreign IDs, old localized owner editor URLs, invalid/valid uploads, approval and opt-out lifecycle. Horizontal overflow0, static4040, failed requests0. Five actual pageerrors describe aborted ViewTransition opt-in; source attribution initially UNKNOWN (motion.js place-route handler excludes specialist routes). Expected HTTP400 upload validation console failure recorded separately (1), not counted as unexpected JavaScript error. Launcher child0/cleanup PASS; browser acceptance wrapper exit1 because localization/runtime errors remain. Seventeen synthetic PNGs retained; reviewer personally viewed public/certificates/reviewer RU390.

Raw evidence outside Git: `/root/task33-evidence/browser25-initial2-20261003/{results.json,source-sha256.json,matrix.js,summary.json,launcher/}`. Executed matrix SHA256 `5b005a2cf005d8b88ed1632bb906ce2ee218cf0bd25eb45f6143816d262e1870`.

Initial uncounted environment attempt: sync failed msgfmt RU duplicate new translation (`Редактировать профиль`, existing obsolete entry). Owned bridge was explicitly finished before matrix acceptance and cleanup PASS; no browser acceptance counted. Root corrected redundant new locale entry. An earlier ad hoc shell-copy quoting failure created an unused mirror; it was stopped/discarded before any settings import/test execution. Durable sync script replaced interpolation and excludes environment files. Neither incident establishes an application regression.

## Findings and handoff

- QA25-B01, LOCAL initial2, P2: untranslated certificate heading/navigation in42AZ/EN rows. Evidence actual DOM aggregate; owner frontend-reviewer/root locale. Requires translated existing msgid and repeated affected languages/screens.
- QA25-B02, LOCAL initial2, P3: five aborted ViewTransition errors during successful real workflows. Source attribution UNKNOWN; `static/js/motion.js:pagereveal` has an uncaught ready.finally source candidate, but its place-route condition excludes specialist paths and therefore does not establish this runtime cause. Current runtime trigger verified, no production conclusion. Owner frontend-reviewer; investigate actual stacks/navigation phases, retain console assertions and rerun redirects.

These findings are RESOLVED on the final frozen snapshots. Root corrected used fuzzy locale entries; fresh full matrix `final-20261003` produced168/168rows and380/380checks, errors0/request failures0/static4040. Actual late `navigation_motion` block after motion.css, overridden only by the three Specialist templates with `@view-transition {navigation:none}`, removed native POST redirect errors without suppressing assertions. Global motion.js was not changed or attributed as their runtime cause. All domain workflows repeated with final nested-ID/claim-gate/document epoch contracts.

Visual inspection then exposed QA25-B03 (LOCAL P2): RU editor H1 and index edit button used AZ fallback `Profili redaktə et`, missed by the initial localization detector. RU had only an obsolete self-translation of `Редактировать профиль`, so default AZ supplied the active fallback. Root reactivated that exact obsolete pair. This is not a template-language/CSRF/fixture workaround. Stronger exact person heading assertions for all three languages and a RU AZ-fallback detector were added; no existing assertion was removed. Corrective `profile-final-20261003`:42/42person/index contexts across21language/width combinations and84/84focus checks PASS, all unexpected errors/static/request failures0. Corrected RU390 PNG was personally viewed; heading now `Редактировать профиль`.

Exact final commands (sync/launch executed as separate dependent calls, requiring sync exit0):

```powershell
wsl -u root --exec /bin/bash /mnt/c/kidsmap/docs/task33/qa25/application_sync.sh
wsl -u root --exec /bin/bash /mnt/c/kidsmap/docs/task33/qa25/application_run-browser.sh final-20261003
wsl -u root --exec /root/km24-security/.venv/bin/python /mnt/c/kidsmap/docs/task33/qa25/application_profile_followup.py
wsl -u root --exec node --check /mnt/c/kidsmap/docs/task33/qa25/application_profile_followup.js
wsl -u root --exec /bin/bash /mnt/c/kidsmap/docs/task33/qa25/application_sync.sh
wsl -u root --exec /bin/bash /mnt/c/kidsmap/docs/task33/qa25/application_run-browser.sh profile-final-20261003 /root/km25-browser-frozen/docs/task33/qa25/application_profile_followup.js
wsl -u root --exec /root/km24-security/.venv/bin/python /mnt/c/kidsmap/docs/task33/qa25/application_source_check.py /root/task33-evidence/browser25-profile-final-20261003
wsl -u root --exec /root/km24-security/.venv/bin/python /mnt/c/kidsmap/docs/task33/qa25/application_results.py /mnt/c/kidsmap/docs/task33/reports/25-application-browser-results.json
```

All final commands exit0; QA04 launcher status/cleanup PASS. Full final source inventory fingerprint `4dc72e1db35689c280bd954406ebcf97754a057746a0b0e6fd837a047d66fce0`; corrective final inventory `94aa8f512e4b3c175ab3afddd511410dbfbb378ef67a5f33a7959178ad733523`. Every executed matrix SHA is in the JSON artifact.2758current source files match corrective mirror; three generated .mo files are recorded separately (freshly compiled from tested .po), not falsely compared against Windows-generated runtime bytecode. Between full and corrective application snapshots the **only source delta is locale/ru/LC_MESSAGES/django.po**. Thus126other full render contexts and380full workflow checks remain applicable;42corrective contexts replace the affected person/index evidence.84corrective focus checks repeat part of380 and are not claimed as84new distinct domain tests.

Final raw evidence outside Git: `/root/task33-evidence/browser25-final-20261003` (17PNG) and `/root/task33-evidence/browser25-profile-final-20261003` (4PNG), each containing results, matrix, source inventory, isolated launcher evidence and ownership-checked cleanup. Safe copied final PNGs for root inspection: `scratch/stage25-browser-inspect/public-ru-390.png`, `certificates-ru-1440.png`, `org-ru-390.png`, `review-ru-390.png`, `person-corrected-ru-390.png`. This reviewer also personally viewed the full final invalid-upload error RU390 and corrected editor RU390. Root performed its own selected visual inspection separately.

Named handoff: frontend-reviewer `/root` receives bounded application browser acceptance PASS and exact source/evidence boundary. Root remains responsible for whole-stage criteria, transfer/domain/backend suite evidence, preservation, final report25 and releasing active_run. Browser acceptance does not claim the full historical application suite or production is green.

## Not run and practical limits

Production, real records/private-file inventory/transfer, deployed storage/nginx/TLS, real external integrations/CDNs, native OS file chooser translations, full screen-reader audit and26+ were not run. QA04 synthetic reconciliation runs in launcher; stage25 transfer/domain/concurrency evidence belongs to root/backend executor and is not relabeled browser evidence. Synthetic fixtures do not establish production permission configuration or actual legacy data quality.

Rendered screens/DOM/form labels/CSRF/focus/layout were exercised in all three languages; deep browser POST workflows and seven-role document-download boundaries ran in RU, with legacy editor GET URL smoke in AZ/RU/EN. Deep POST sequences were not redundantly repeated in AZ/EN. This is a stated coverage boundary, not63three-language document boundary checks or a claim of every language/action combination.
