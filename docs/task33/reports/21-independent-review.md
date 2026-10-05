# Stage 21 — independent integration review

Reviewer: actual specialist `/root/stage21_integration`, canonical `.agents/agents/integration-reviewer/agent.md`; date 2026-10-03. Mode **AUDIT**, parent-approved implementation scope is stage 21 only. Reviewer changes only this report and ignored scratch checks; no application, migration, production, commit or push operations.

Snapshot: Windows `C:/kidsmap`, branch `task33-progress`, LOCAL HEAD `015d031d8eb17114bd860159dde805b38df3c13c`; reviewed dirty application source mirrored to `/root/kidsmap-task33`. HEAD alone does not identify the implementation. Production **NOT CONTACTED / UNKNOWN**.

Codebase Memory was callable; `list_projects` identified `C-kidsmap`, graph search located `available_languages` and `canonical_language`. Index generation `2026-10-03T07:34:24Z`; exact coverage for public languages/presentation, sitemap, SEO, controllers and context processor was `coverage_unavailable / metadata_changed`. Relevant conclusions were verified against actual source and isolated tests; graph completeness is UNKNOWN. Context7 unavailable in parent runtime.

**Final independent integration verdict: PASS on the final hashed source below.** Fresh isolated `independent-offer-final-20261003`: exit 0, **33 tests PASS**, 0 failures/errors/skips, 7.982s test execution; Django check and makemigrations check PASS; 161 applied / 0 unapplied migrations; network guard active, external credentials absent, cleanup PASS and temporary run/socket roots removed. Twelve reviewer-authored checks plus twenty-one lead-authored stage-21 contracts executed independently. This is not a full-site or production readiness claim.

Reopening history: earlier `independent-final-contract-20261003` passed 32 tests on its old snapshot. Subsequent lead regression identified ambient gettext leaking into `schema_offers` default title evaluation when explicit EN reader is called under AZ. Lead confirmed a meaningful RED case and introduced bounded `override(lang)` evaluation for primary/required-fee product titles only. Reviewer checked the actual function delta and extended an existing independent case to compare explicit EN schema offers under AZ and EN ambient locales, including an actual required registration-fee fixture. The final 33-test run confirmed identical explicit-EN schemas, default Lesson title and AZN currency under both ambient locales. Pricing amounts/filtering/relationships were unchanged. Earlier 32-test PASS is retained as historical evidence, superseded by the 33-test verification.

## Evidence and provisional findings

- Approved-content resolution: `public_presentation.present` resolves current approved Program inheritance or detached approved snapshots; pending revision payloads are not read. New language eligibility uses this resolver for Activity, own translated name/description for Place/Organization, and AZ canonical fallback. Navigation language URLs remain separate from indexable head alternates.
- `seo._serialize_json_ld` preserves script terminators as escaped JSON data. Organization/Course payloads contain approved textual facts and current provider only; no invented rating, dates or location were introduced.
- Approved operating-state `closed` differs from unpublished/inactive; closed public Place retains detail access and explicit notice, ordinary public queryset excludes it, SEO omits current offers/opening hours. Unpublished objects retain 404.
- **IR21-P2-01: new Activity sitemap query amplification**, verified before remediation. `ActivitySitemap.get_languages_for_item` calls `available_languages`, which computes RU/EN through the complete `present` reader. Django invokes eligibility repeatedly; contact, group/plan and pricing reads occur even though only translated text is needed. Isolated fixture profile: 1 Activity → 2 URLs / **68 SQL queries**; 5 Activities → 10 URLs / **260 SQL queries**. Confidence high, LOCAL WORKTREE only; no production timing claim. Owner: stage-21 lead. Recommendation: per-generation reuse and bounded approved-content batch resolution, preserving fresh affiliation and snapshot trust; avoid a persistent/global cache. Remediation/recheck pending.

## Independent executions

Exact invocation (fresh output per run):

```powershell
& 'C:/Program Files/WSL/wsl.exe' -d Ubuntu-24.04 -u root --exec /bin/bash -lc 'cd /root/kidsmap-task33 && .venv/bin/python /mnt/c/kidsmap/scratch/stage21-independent/run.py --mode all --output /tmp/task33-stage21-independent-offer-final-20261003 --label catalog.testcases.test_independent21'
```

The ignored adapter imports unchanged QA04 launcher, prepends only its scratch path to the launcher's sanitized environment, and adds reviewer tests to canonical discovery. Original settings/network/libpq guards, disposable PostgreSQL container (`network=none`, socket only, tmpfs database), local cache/email/media, checks/migrations and ownership cleanup remain active. Adapter and fixtures are retained outside Git; raw evidence never copied to tracked report.

Five independent checks cover pending RU candidates not becoming public/schema/hreflang, detached approved snapshot resisting later live Program edits, hidden Program/Organization text/provider exclusion, AZ/RU/EN review/media URLs and direct legacy redirects, and sitemap SQL measurement. Importing the stage-21 fixture class also executes its 16 contract tests: **21 total**.

Earlier executions retained truthfully:

| Run | Result | Classification |
|---|---|---|
| `independent-20261003` | exit 1 before tests | Reviewer adapter ENVIRONMENT_FAILURE: missing exported `commands.dump`; fixed adapter only |
| `independent-rerun-20261003` | 21 tests, 1 failure, 0 errors/skips; checks/migration/cleanup PASS | Reviewer fixture referenced a nonexistent media file, excluded by gallery reader; fixed by saving an actual tiny JPEG into isolated media, preserving URL assertion |
| `independent-fixture-20261003` | exit 0; **21 PASS**, 0 failures/errors/skips, 6.694s test execution | Fresh run after compiled locale resources and corrected isolated media fixture; checks/migrations/cleanup PASS |

Before-remediation run had check/makemigrations PASS, 161 applied / 0 unapplied migrations, network guard true, external credentials absent, cleanup PASS and run/socket roots removed. Parent evidence is not presented as this reviewer's independent execution.

Raw evidence retained at `/root/task33-evidence/independent-fixture-20261003`; query profile reproduced 68 / 260 SQL counts. Parent has acknowledged the performance finding and is implementing bounded remediation with a meaningful pre-fix query-budget test. This supersedes the earlier source freeze; final review rerun pending.

Additional source-observed acceptance gap sent to lead: related/grouped AZ fallback text in `public_offerings.html` and parent/Organization links lacks per-field `lang`, inheriting RU/EN page language. Unlike untranslated shell URLs, this can label displayed fallback text incorrectly. Schedule/teacher facts need preservation rather than guessed language detection. Lead scope decision and fresh verification pending.

Lead requested expanded independently authored acceptance tests. `independent-field-red-20261003` executed **27 tests / 6 failures / 0 errors / 0 skips**, child exit 6; system checks/migration drift PASS, 161 applied / 0 unapplied, cleanup PASS. Five newly authored failures independently reproduce: group name/conditions inherit RU instead of AZ; custom price title/conditions inherit RU; related Place/Organization names inherit RU; EN default lesson title is Russian `Занятие`; EN visible fallback breadcrumbs show AZ `Ana səhifə` instead of UI `Home`. Sixth failure is the imported lead-authored five-Activity query-budget test, 174 queries exceeding 80. The root already proved that test RED separately. Relevant methods live in ignored `scratch/stage21-independent/test_independent21.py`; raw evidence `/root/task33-evidence/independent-field-red-20261003`.

Classification: grouped/related markers and fuzzy gettext lesson catalog are existing source acceptance gaps, not attributed as a new application regression; visible breadcrumbs are a new stage-21 regression caused by using canonical content locale for both SEO and UI navigation. Exact effective DOM language was checked with HTMLParser inheritance. No assertions were weakened. Remediation by the lead remains inside localization/SEO scope; reviewer application edits remain none.

Additional negative pending: published Activity shell whose hidden Program leaves no substantive approved name/description must remain detail 200 without being newly advertised by Activity sitemap. Parent requested this bounded reader/sitemap check; publication/status behavior is not changed.

The first empty-Activity fixture failed its prerequisite: automatic approved Program snapshot remained after Program became draft. This confirmed the historical snapshot contract rather than a sitemap defect. Corrected legacy fixture explicitly cleared snapshot/own text fields while preserving published Activity status; `independent-empty-fixture-red-20261003` then proved detail 200 with empty approved name/body and failed because sitemap advertised one AZ URL. Checks/migrations/cleanup PASS; raw evidence retained outside repository.

Post-remediation `independent-final-20261003`: **32 tests / 1 failure / 0 errors/skips**, exit 1, test elapsed 10.605s. Every newly reproduced locale/DOM/query/cache/sitemap criterion passed. Remaining failure was an earlier reviewer assertion demanding AZ hreflang for hidden Program/Organization with no substantive Activity text, contrary to the now-explicit empty-language contract. Reviewer changed this assertion to require empty approved name/body **and no alternate URLs**; this adds stricter prerequisites instead of deleting the negative check. Fresh `independent-final-contract-20261003` then passed all 32 tests. Source snapshot remained unchanged during this reviewer-only alignment.

Final independently measured SQL profile: **6** (1 Activity / 2 URLs) and **22** (5 Activities / 10 URLs), versus pre-remediation 68/260. The extracted approved-text resolver preserves Program/current-affiliation/snapshot semantics; per-generation language cache resets before the next `get_urls` call. Reused same sitemap instance followed by hidden/empty source returned no URLs in the independent negative check. No global/persistent cache was added. Full-volume timing/load benchmark NOT RUN.

Raw final evidence and actual reviewer helpers retained at `/root/task33-evidence/independent-offer-final-20261003` outside Git; the earlier 32-test evidence is also retained. All 17 source/locale paths were SHA256-equal between Windows and Linux before the final 33-test execution and again afterward; Windows manifest verified no changes since the last freeze. The reviewer never modified these application artifacts.

## Boundaries and handoff

No independent full application suite, production/CI, external providers, production media storage or rendered browser run. Browser acceptance belongs to the separately assigned real browser reviewer. Locale source inspection does not establish browser correctness. No migrations or persistence rules changed in reviewer scope; publication concurrency was not independently exercised because this stage changes read/presentation behavior only.

Handoff: `/root` (stage-21 lead), accept bounded independent integration review with **no remaining confirmed integration blocker** on the hashed snapshot; reconcile root regression/discovery and separate browser acceptance before stage completion. `/root/stage21_browser` owns actual media HTTP 200 and rendered multilingual verification. Earlier provisional/pending statements above are retained as chronological evidence and are superseded by this final verdict.

## Final dirty source identity

| Source artifact | SHA256 |
|---|---|
| locale/az/LC_MESSAGES/django.po | `8faa6f87080ced299a2e4293f8c640d0abb9bcea81ee8f4b05316be3c2aea1b4` |
| locale/en/LC_MESSAGES/django.po | `89ec7942fee5b15ca0afbe4f438cd6a8922d5faad21793daec6acfd613e46558` |
| src/catalog/context_processors.py | `1592beedd1140ea2aa1449c61110dc9ac3958145e15bb3548362d25aa691ad76` |
| src/catalog/controllers/public_details.py | `0c5b9bc54a0e277e3dc7913425bc78051c82415421ec6258eb8ff8c615f28b9e` |
| src/catalog/services/public_languages.py | `31056395e16df31f570fa7e8ce0b4614f41e3e08e2d15e58f7e76df676645fd3` |
| src/catalog/services/public_presentation.py | `dd06ee23de45f403179d0bd262239cc1ee972462f55f505016027875cfcc13f0` |
| src/catalog/services/seo.py | `0f569c1f1f7e82bc4dfc12e62995acafab92f4508123df4686d7024c3926d2f6` |
| src/catalog/sitemaps.py | `7f5fd80461b4a40baceb52dafaa9f7314ee3d0978fc2957410d90cdb1da973cd` |
| src/catalog/templates/catalog/includes/breadcrumbs.html | `1900ec14d2c0d45f285b0701a29e34f9f121d0fe36291cc79ef9c6e5b43cab5f` |
| src/catalog/templates/catalog/includes/public_offerings.html | `7903649cc253f2ea553af23c4e0679646f05c7d0645e3c08799f32a976e72c97` |
| src/catalog/templates/catalog/place_detail.html | `8f8a85f618d51ad2b3303d1573c6066442c92444b085542e78074d04e00a08cc` |
| src/catalog/templates/catalog/public_entity_detail.html | `4ed64b6e1a9227e2151529d6a9cd0812730ab553dac5f65c9f2df07a7648ccbe` |
| src/catalog/templates/includes/header.html | `b6e8001bbab2334e70b63ddf2c9690a96807fb2a4b9be8a84e3d6945a4c3bf34` |
| src/catalog/testcases/test_localized_place_seo.py | `e682f29e77095d79c6f3c588606cfc98f4edfdf973829ec664f4e0a12454ca79` |
| src/catalog/testcases/test_task33_localization.py | `96380fb25c7b65c3cf2de2d93b28f05a166af2c2a6296bfd2305f2c35e17567e` |
| src/catalog/testcases/test_task33_public_details.py | `ac0774609b74bd8cbf1dbed54b65be9b936ef8714ffe1f366c8e35a769dbf508` |
| src/config/urls.py | `f9ada311a82098f5e5b6adce99230284f84617a1b3fdef48c97da7ae02f1b476` |
