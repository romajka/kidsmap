# Stage22 — independent integration review

**PASS for the bounded integration scope on the verified dirty snapshot.** Fresh reviewer-launched QA: **19/19 PASS**, zero failures/errors/skips, exit0, elapsed4.249s; Django checks and migration consistency PASS, disposable cleanup PASS. Overall stage completion remains the lead's decision after combined regression and separately owned browser/database evidence.

Reviewer: actual specialist `/root/stage21_integration`, canonical `.agents/agents/integration-reviewer/agent.md`, 2026-10-03. Mode AUDIT with assigned ownership of this report, `src/catalog/testcases/test_task33_review_independent.py` and ignored `scratch/task33-stage22-integration`. No application edits, production access, stage23+, commit/push/merge/deploy by reviewer. Parent owns approved stage22 implementation; stage21 changes preserved.

Snapshot: branch `task33-progress`, LOCAL HEAD `015d031d8eb17114bd860159dde805b38df3c13c`, dirty `C:/kidsmap`, mirrored to `/root/kidsmap-task33`; HEAD alone does not identify tested implementation. `active_run` assigned to lead `/root` stage22. Read D07, stage22 prompt, reviews architecture and journal plus canonical role/shared contracts. Production NOT CONTACTED / UNKNOWN.

Codebase Memory located typed models/services, index generation observed `2026-10-03T08:55:47Z`. Exact review versions/retention/controller/account-deletion coverage reported `coverage_unavailable / metadata_changed`. Critical conclusions verified in actual source; graph completeness UNKNOWN. These research results are not independent runtime evidence.

## Executed evidence

```powershell
& 'C:/Program Files/WSL/wsl.exe' -d Ubuntu-24.04 -u root --exec /bin/bash /mnt/c/kidsmap/scratch/task33-stage22/run-linux-qa.sh all independent-final-20261003-c --label catalog.testcases.test_task33_review_independent
```

QA04 wrapper mirrors allowlisted source only, compiles AZ/RU/EN catalogs before a fresh child, then invokes unchanged isolated launcher. Evidence retained outside Git: `/root/task33-evidence/independent-final-20261003-c`. Result:19 tests,0F/0E/0skip; check0 and makemigrations0;164 applied/0unapplied; discovery1597 unique/0duplicates. PostgreSQL17.11/Python3.12.3/Django6.0.2/psycopg3.2.10. DJANGO_TESTING with isolated DB/cache/media/email; network and libpq guards true; external credentials absent. Cleanup PASS, run/socket roots removed. Docker QA DB uses network none and disposable storage; no production credential or database used.

Independent cases cover four typed rating contributions, approved projection during pending/rejected edits, Organization exclusion; known-account effective-decision normalization preserving source/reaction IDs and text, repeat idempotency; separate unknown-author identities; business moderation denial, actual scoped public reply/private report; unprivileged staff denial; owner ACL revocation between preflight and locked write; wrong-parent and stale revision reactions; approved-version counter reset with historical reaction retention; hidden Activity404; genuinely public future Event200 and deleted/undated/expired/feature-disabled404; approved-history anonymization and candidate removal across all4 types; delete-all disposition; voter removal/counter refresh via both helper and full account-deletion finalizer; scheduled cutoff one microsecond before versus exact boundary; two concurrent first submits and two concurrent staff decisions using actual PostgreSQL connections.

Legacy synthetic aggregate is explicitly asserted before normalization `{average:3.5,count:2}` and after latest approved-source selection `{average:5.0,count:1}`; older approved/rejected source rows and reaction PK/text remain. No production formula change inferred from this fixture.

Nineteenth case renders actual admin change pages for all4 typed heads,200, correct workflow link/history, every model field read-only and empty editable form. Place admin additionally has no old approve/hide/reject links, save/continue controls or editable-text promise. Explicit cookie/locale AZ/EN requests require actual root html language and translated workflow/history/metrics labels. Default RU read-only copy and original assertions retained.

## Findings resolved in reviewed source

- IR22-P2-01: Event guard initially accessed nonexistent is_active and missed deleted visibility. Lead now uses existing Event.is_public plus feature switch; independent public/hidden/expired/deleted cases PASS.
- IR22-P2-02: business reply/report ACL was checked before locks only. Lead added actual ACL recheck inside locked write; independently authored owner-revocation negative PASS with zero responses.
- IR22-P2-03: malformed edit ID and SimpleLazyObject account lookup could produce500. Lead uses get_user_model(), guarded positive ID conversion and400 handling. Independent authenticated Activity edit rejects malformed ID with no candidate/current/history change; action IDs Unicode superscript, zero, negative and5000digit decimal also400/no write. The long decimal exposed Python integer conversion-limit risk; action length cap now rejects before conversion. Numeric stale-ID conflicts remain separate409.
- IR22-P2-04: browser independently found admin gettext alias shadowing producing500; lead renamed local tuple variable. Our actual4-page admin regression PASS. Lead also removed stale Place admin controls/false editing promise and supplied new locale labels; independently asserted.
- DB22-05 (database specialist source finding, attributed): deleting voter reactions bypassed visible counter refresh, and full deletion removed Place votes before shared helper could collect affected heads. Lead collects affected IDs/refreshes surviving heads in both paths. Our actual four-type helper and finalizer tests PASS.

Reviewer did not modify application code. No remaining confirmed blocker in this bounded tested scope. Scope does not establish complete application/browser/production readiness.

## Classification of earlier evidence

Lead-provided prechange core3/3 and baseline61/61 PASS are attributed, not independently launched here. Lead first combined23 run:22PASS/1ERROR due reviewer fixture relying on seeded EDU category after TransactionTestCase flush; reviewer added explicit get_or_create, no assertions weakened. Our intermediate `independent-own-20261003-a`15/15PASS preceded later app changes.

Lead focused malformed-ID RED exposed genuine lazy-user500 before intended malformed-ID assertion; remediation/focused GREEN belonged to lead. Lead admin focused1/1PASS followed browser500 remediation. Reviewer corrected fixture-only language assumptions: default admin is RU, not AZ; explicit locale tests also need django_language cookie, because request header/translation override alone left root html RU. Our `independent-final-20261003-b` ran19 with2 subtest failures in one admin case,0errors, cleanupPASS; translated-label assertions were retained and root html-language assertion strengthened, not removed. Final c replay above is successful fresh evidence.

Seeded migration0128 first failed on PostgreSQL pending FK trigger events before CREATE INDEX; separately assigned database reviewer reproduced it, lead fixed transaction boundary, and that actual reviewer reports unchanged seeded fixture1/1PASS and cleanupPASS. See `22-database-review.md`; our empty-DB migration PASS alone does not prove seeded preservation. Browser evidence belongs to `22-browser-review.md`, not this reviewer's execution.

## Snapshot integrity

Bounded19-file SHA256 manifests: `scratch/task33-stage22-integration/final-source-hashes.json` and `final-source-hashes-post.json`. All Windows/Linux copies equal, and before/after manifests byte-equivalent as parsed JSON. These are bounded reviewed files, not a claim to hash every dirty application/static file. Source-only hashes below contain no credentials, fixture rows or logs.

| Path | SHA256 |
| --- | --- |
| locale/az/LC_MESSAGES/django.po | `4277abf194a71831b43569861e383efe460bcdab5222dc14daa1d8f7f36d2f6d` |
| locale/en/LC_MESSAGES/django.po | `ae063f1ace1f704cdc8f519c48c4cff23413e4d794aa72222bd6f45654dc4b38` |
| locale/ru/LC_MESSAGES/django.po | `65af888e0ac976e686c8b1b65dd475653d3b4808b44c6e49108fc680426fae71` |
| src/catalog/controllers/typed_reviews.py | `3a369d3c05b2c907e6fe556f3b5fd35298776451f7aceb3e21f619395e31a1f6` |
| src/catalog/domain_admin/review_versions.py | `cd5f043cf42b0d11e2569a97970a14932acb87fdf90fdc77aab0761c70471aa6` |
| src/catalog/migrations/0128_task33_review_versions.py | `124cd7f8cdfef5621def7c1dbd5def1634537b5dce5cd863048788942cecfe1d` |
| src/catalog/migrations/0129_task33_review_versions.py | `d880a6a4ff53c0c4dff569fb3c5637ceed91d9696489750afd3e043efe35fc38` |
| src/catalog/migrations/0130_task33_review_versions.py | `f767bb6f1fda87dc09d8b956f7582a9dc4d6eb65b7755446d91a9057235b175b` |
| src/catalog/models/place.py | `3b13f4c409d987d295f7303689d84916601d7fd8c322d8e06f215cc7249c3007` |
| src/catalog/models/review.py | `02ea6e1fbc145229795c986e88ff54e27de6ff824fb618bf7d63dde80c6291f8` |
| src/catalog/models/review_versions.py | `441436f33cfea92695cb2d172070d6fd2d9c634db8f642ae092cb157e50aca0a` |
| src/catalog/models/specialist.py | `ed54022bd02fb06d45dac0a793a24a4ba22b59c82497b4995035dd60e5d9d53e` |
| src/catalog/services/account_deletion.py | `8d3c7925da66abbabefccc5e7c492d18caeb92a56a7f590e24252ac83deb2041` |
| src/catalog/services/place_review_submission.py | `1130d772302d9abe43acf06ea11823f81d8d8b361fa1bddd2d8589d35ec3eec2` |
| src/catalog/services/reactions.py | `60b76238232678d670257bc5f726998eb2395fddb9d94a205ff8b0eb551a8dbc` |
| src/catalog/services/review_retention.py | `48cfc6eb881a8bc35d50854abacdab17d4afea9ed9e3f45d42a8a6387071affe` |
| src/catalog/services/review_versions.py | `df377059cc2c4fe008149d48aa9911c0f56eb7fab405a6663aa5f4db2d1dfe99` |
| src/catalog/templates/admin/catalog/placereview/change_form.html | `cc2e1a9e1b8b40a460b8c8008ba7787fdb3135b23d112e639ceaaa0a244e33fc` |
| src/catalog/testcases/test_task33_review_independent.py | `1df31c61e9face9ce2637916dcda11d90dcb1a836edfe53dc2c5ac60aa4996b7` |

## Named handoff and limits

`kidsmap-orchestrator` / lead `/root`: receive this fresh19-case PASS and execute combined scoped regressions on same source before stage completion. `database-reviewer`: owns seeded migration/constraint preservation evidence. `browser-qa`: owns rendered AZ/RU/EN, viewport/console/network/flow evidence. Full application suite, external providers and production NOT RUN by this specialist. No stage23+ action authorized by this handoff. Actual app source changes require refreshed relevant tests; unrelated static/browser claims must use browser evidence.
