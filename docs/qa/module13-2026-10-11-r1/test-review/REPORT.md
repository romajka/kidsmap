# Module13: fresh full-suite evidence

Role: integration-reviewer; execution identity: /root/cross_tests; 2026-10-11; AUDIT ONLY. Definition: `.agents/agents/integration-reviewer/agent.md`. Assigned ownership: this folder and its ignored scratch. Parent owns rendered browser acceptance, final findings, journal and handoff.

Snapshot: `C:/kidsmap`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, branch `task33-progress`, active_run `NONE`. Dirty application WORKTREE preserved. Application source digest `e13c36f2af3aca03513ff860a1dee7c02a8cb2ab8214c89bcffd7dd5fe5914b1`; 2,788 files unchanged against parent entry snapshot. Python 3.12.15, Django 6.0.2, Node v24.14.0, PostgreSQL17.11. Production and actual GitHub execution: NOT RUN.

## 1. Состояние области

Completed broad `catalog` discovery plus all11 otherwise omitted non-test-prefixed modules, 2,090 unique methods, no duplicate IDs. Fresh normalized unit matrix: **2,036 PASS /11 FAIL /43 NOT RUN**. The latter includes42 bodies blocked by guarded legacy/POSIX environment and one Windows streaming-file cleanup error; raw framework outcome remains FAIL (exit1). Two Windows encoding errors recovered by exact rerun with `-X utf8`, 2/2 PASS, exit0. No assertions changed or guards bypassed.

Raw full run: 2,034 PASS,20 direct FAIL,28 ERROR,62 failed subtest observations across8 methods; these are not62 independent methods. Duration1570.313s, exit1. Across full/UTF8/frozen/GNU profiles:2,114 method slots, 2,223 observation rows, 2,090 distinct methods. [Counts](counts.json), [complete normalized methods and module matrix](results.json), [raw full results](full-results.json).

## 2. Сильные стороны

Existing JS:20 scripts exit0,115 named Node tests plus2 bare-file wrappers (117 entries), no failures/skips. [JS commands/counts](js-results.json). Existing standalone Python tests: Windows13 PASS/3 `/bin/bash` environment ERROR; the same3 backup bodies subsequently PASS in WSL with synthetic files and mocked Docker/compressor. First WSL CRLF attempt retained and excluded as intended-boundary proof; two nominal negative PASS rows did not reach their intended failure boundary. Retry adapts LF only in copied own fixture. [Standalone](standalone-results.json), [WSL replay](wsl-backup-results.json), [first WSL attempt](wsl-backup-results.attempt1.json).

Tests preserve source KidsMapTestRunner cache/language reset, real PostgreSQL constraints/locks where applicable, isolated `test_module13` /`test_module13_head` /`test_module13_head_compiled`, LocMem cache/email, separate unit media/private-media, blocked external socket connections. Initial fixtures are fictional. Django Client/JS stubs are not rendered browser or real integration evidence.

## 3. Реальные проблемы

**CROSS-QA-02, P2: CI command discovery omits tracked tests.** Actual manage.main argument wiring in DISCOVERY ONLY forwards no labels and finds618 tests; tests_executed0/database_createdfalse. Fresh HEAD tracked donor has2,070 methods, so1,452 tracked cases are omitted by the configured command. Current dirty WORKTREE has2,090:1,472 omitted =1,452 tracked-source+20 foreign untracked-source methods. Do not infer these20 are present in GitHub. Explicit wrapper `full -> catalog` discovers1,930 HEAD /1,950 WORKTREE, omitting140 methods in11 modules.

Root cause: `test_catalog.py:7` imports only `catalog.tests`; `src/` has no `__init__.py`, so default root filesystem discovery reaches the bridge, not all app test modules. `src/catalog/tests.py` imports11 legacy groups. `.github/workflows/deploy.yml:78` uses `python manage.py test --parallel 1`; `scripts/run_kidsmap_tests.sh:58` full uses catalog. Five cited files match HEAD after CRLF normalization. Expected: declared full quality gate discovers the current tracked suite and explicitly handles guarded platform profiles. Actual: the local configured command silently omits1,452 tracked cases. Impact: domain/security/concurrency regression coverage can be skipped by a successful gate. Owner: integration-reviewer +release-reviewer; requires safe portable/full Linux profile and a domain-approved baseline, no guard weakening. Actual GitHub execution NOT RUN.

[Actual manage wiring/IDs](manage-discovery.json), [WORKTREE discovery](discovery-audit.json), [HEAD discovery](head-discovery.json), [tracked/untracked qualification](discovery-corpus-qualification.json), [source verification](discovery-source-verification.json). Parent owns the individual CROSS-QA-02 repair prompt.

All11 failed assertion methods reproduce on the frozen-runtime HEAD donor, exit1,36.11s. Fresh GNU gettext built from HEAD `.po`, selected before django.setup, yields9 PASS/2 FAIL, exit1,39.203s. Nine failures are attributable to the frozen runtime gettext assets for this comparison; no app code was changed. **The native browser runtime remains unchanged and failing assertions remain FAIL in its original profile.** This control does not close historical locale UI defects. The other2 are a legacy Specialist test expecting200 where the canonical redirect returns302, and a copied unchanged foreign untracked PlaceNature localization assertion whose expected labels also differ from freshly compiled HEAD.

| Existing method | Classification | Frozen HEAD | GNU HEAD |
| --- | --- | --- | --- |
| catalog.testcases.test_event_admin_readiness.EventAdminReadinessTests.test_global_russian_labels | RUNTIME_GETTEXT_ARTIFACT_FAILURE_FRESH_HEAD_COMPILE_PASSES | FAIL | PASS |
| catalog.testcases.test_event_admin_readiness.EventAdminReadinessTests.test_shared_translation_consumers | RUNTIME_GETTEXT_ARTIFACT_FAILURE_FRESH_HEAD_COMPILE_PASSES | FAIL | PASS |
| catalog.testcases.test_organization_admin_labels.OrganizationAdminLabelRequestTests.test_add_and_change_in_one_process_follow_each_request_language | RUNTIME_GETTEXT_ARTIFACT_FAILURE_FRESH_HEAD_COMPILE_PASSES | FAIL | PASS |
| catalog.testcases.test_organization_form_copy.OrganizationFormCopyTests.test_all_visible_and_hidden_form_labels_use_current_language | RUNTIME_GETTEXT_ARTIFACT_FAILURE_FRESH_HEAD_COMPILE_PASSES | FAIL | PASS |
| catalog.testcases.test_organization_form_copy.OrganizationFormCopyTests.test_create_required_error_label_is_localized_and_preserves_input | RUNTIME_GETTEXT_ARTIFACT_FAILURE_FRESH_HEAD_COMPILE_PASSES | FAIL | PASS |
| catalog.testcases.test_organization_form_copy.OrganizationFormCopyTests.test_repeated_conflict_preserves_loser_winner_and_original_cas_in_each_language | RUNTIME_GETTEXT_ARTIFACT_FAILURE_FRESH_HEAD_COMPILE_PASSES | FAIL | PASS |
| catalog.testcases.test_public_section_switches.PublicSectionSwitchTests.test_admin_section_controls_follow_selected_language | RUNTIME_GETTEXT_ARTIFACT_FAILURE_FRESH_HEAD_COMPILE_PASSES | FAIL | PASS |
| catalog.testcases.test_specialist_identity_date_label.SpecialistIdentityDateLabelTests.test_add_and_change_show_localized_readonly_identity_date | RUNTIME_GETTEXT_ARTIFACT_FAILURE_FRESH_HEAD_COMPILE_PASSES | FAIL | PASS |
| catalog.testcases.specialists.TestSpecialistsFeatureFlag.test_feature_enabled_by_default | PRE_EXISTING_HEAD_COMPILED_BASELINE_CONTRACT_FAILURE | FAIL | FAIL |
| catalog.testcases.test_organization_admin_labels.OrganizationLabelLanguageTests.test_reused_form_follows_language_switch_after_import | RUNTIME_GETTEXT_ARTIFACT_FAILURE_FRESH_HEAD_COMPILE_PASSES | FAIL | PASS |
| catalog.testcases.test_task33_place_nature_localization.PlaceNatureLabelsTests.test_runtime_choices_in_all_languages | PRE_EXISTING_HEAD_COMPILED_BASELINE_CONTRACT_FAILURE | FAIL | FAIL |

[Frozen baseline](baseline-results.json), [fresh compiled HEAD control](baseline-compiled-results.json), [donor/source and frozen .mo hashes](baseline-source.json). The donor is HEAD tracked app plus3 current untracked runtime .mo assets; one foreign untracked test was added unchanged after pristine HEAD discovery. No confirmed new application regression is inferred from these11 failures.

## 4. Tech debt

Discovery bridge and shell full wrapper describe different suites. Forty-one existing guards require specific historical QA04 settings/DB/name/Unix socket/guard module, so the new isolated Windows TCP profile cannot execute their bodies. Default Windows encoding affects stdout and CSV fixture writes; `-X utf8` fixes the test environment. Private streaming response cleanup hits WinError32; not a demonstrated private-data leak. Nine runtime locale failures demonstrate generated gettext assets need provenance and source correspondence; exact original asset provenance remains UNKNOWN.

## 5. Risks

Raw full suite is not green. Do not deploy, fix assertions, fake QA04 markers or reinterpret environment failures as product success. Passing fresh HEAD gettext does not establish current browser locale correctness, current WORKTREE `.po` compilation correctness, production capability or new clean-checkout CI success. Root must deduplicate historical locale causes only where source and rendered evidence match. No P0/P1 demonstrated by this subtask.

## 6. Dead/legacy candidates

Legacy wrappers/guards retained as active compatibility/test infrastructure. No removal inference or changes. Source/graph absence is not deletion evidence. Codebase Memory was available and ready, but cited paths reported metadata_changed/coverage_unavailable; direct source and fresh runtime discovery are authoritative here.

## 7. Tests gaps

| Environment category | Method count |
| --- | --- |
| ENVIRONMENT_CLEANUP_ERROR | 1 |
| ENVIRONMENT_POSIX_PATH_NOT_RUN | 1 |
| ENVIRONMENT_GUARD_NOT_RUN | 41 |

Three stock Playwright scripts remain NOT RUN: they require dedicated synthetic `sessionid`, `127.0.0.1`, special config and review cooldown3 fixtures incompatible with the parent stand's current session profile. Parent's fresh browser acceptance is separate. Real Google OAuth/GA/Maps SDK, real SMTP/IndexNow, production restore and actual GitHub CI remain NOT RUN. No claims about RU/AZ/EN viewport rendered PASS are made from these backend/jsdom checks.

## 8. Recommendations

After separately approved scope, make the CI and full wrapper enumerate the same tracked suite. Establish a genuinely disposable Linux legacy profile for hardcoded QA04 guarded bodies, retaining negative isolation checks and assertions. Reproduce failures with authoritative locale builds, compare contracts before changing legacy expectations, close streaming test responses in a later test-only fix plan. Root retains historical finding IDs and uses fresh rendered evidence for locale defect disposition.

Commands and exact per-script argv are in [counts.json](counts.json) and [js-results.json](js-results.json). Full runner as launched is [full-runner-at-launch.py](full-runner-at-launch.py); later own harness change affects I/O capture only. [Raw full log](full-django.log), [UTF8 replay](utf8-rerun.log), [frozen donor log](baseline-django.log), [GNU donor log](baseline-compiled-django.log), [GNU build](head-gettext-build.log). Ephemeral CSRF values in own failure traces masked; raw originals remain only in ignored own scratch. [Redaction record](redaction.json).

## 9. P0/P1/P2/P3 и handoff

P2 confirmed: CROSS-QA-02. No independently confirmed P0/P1 application defect; baseline/environment results are separated from product findings. Named handoff: **kidsmap-orchestrator /root** — integrate unique counts and raw exits, preserve runtime locale FAIL, deduplicate known locale causes against current screenshots, retain42 unavailable legacy bodies and Windows cleanup limitation, publish module13 report/journal and future repair decision text. No application/source/assertion changes, commit/push/deploy or production interaction.
