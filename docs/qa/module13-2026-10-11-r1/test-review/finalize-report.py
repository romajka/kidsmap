"""Normalize only outcome identity and environment attribution; preserve raw exits."""
import ast,collections,hashlib,json,re,sys
from pathlib import Path
P=Path(__file__).resolve().parent;ROOT=P.parents[3]
load=lambda name:json.loads((P/name).read_text(encoding='utf-8'))
full=load('full-results.json');initial=load('initial-classification.json');target=load('target-results.json');frozen=load('baseline-results.json');compiled=load('baseline-compiled-results.json');js=load('js-results.json');meta=load('metadata.json');qual=load('discovery-corpus-qualification.json');head=load('head-discovery.json')
def method_rows(rows):
    result=collections.defaultdict(list)
    for row in rows:result[row['id'].split(' (',1)[0]].append(row)
    return result
def outcome(rows):
    return 'FAIL' if any(r['status'] in ('FAIL','ERROR','SUBTEST_FAIL') for r in rows) else 'PASS'
fr=method_rows(frozen['records']);co=method_rows(compiled['records']);ta=method_rows(target['method_observations']);raw=method_rows(full['method_observations'])
normalized=[]
for test_id in load('full-inventory.json')['ids']:
    label=initial['by_method'][test_id]
    status='NOT RUN';classification=label
    if label=='PASS':status='PASS';classification='EXECUTED'
    elif label=='ENVIRONMENT_ENCODING_RERUN' and test_id in ta and outcome(ta[test_id])=='PASS':status='PASS';classification='ENCODING_ERROR_RECOVERED_FRESH_UTF8'
    elif label=='FAILED_BASELINE_PENDING':
        status='FAIL'
        if test_id in fr and outcome(fr[test_id])=='FAIL':
            classification='PRE_EXISTING_FROZEN_RUNTIME_BASELINE_FAILURE'
            if test_id in co and outcome(co[test_id])=='PASS':classification='RUNTIME_GETTEXT_ARTIFACT_FAILURE_FRESH_HEAD_COMPILE_PASSES'
            else:classification='PRE_EXISTING_HEAD_COMPILED_BASELINE_CONTRACT_FAILURE'
        else:classification='ATTRIBUTION_UNKNOWN'
    normalized.append({'id':test_id,'status':status,'classification':classification,'original_observation_statuses':[r['status'] for r in raw.get(test_id,[])],'frozen_head':outcome(fr[test_id]) if test_id in fr else 'NOT RUN','compiled_head':outcome(co[test_id]) if test_id in co else 'NOT RUN','utf8_rerun':outcome(ta[test_id]) if test_id in ta else 'NOT RUN'})
matrix=collections.defaultdict(collections.Counter)
for row in normalized:matrix[row['id'].rsplit('.',2)[0]][row['status']]+=1
counts={'django_unique_methods':full['unique_count'],'django_normalized':dict(collections.Counter(r['status'] for r in normalized)),'django_classifications':dict(collections.Counter(r['classification'] for r in normalized)),'raw_full':{'exit_code':full['exit_code'],'duration_seconds':full['elapsed_seconds'],'unique_methods':full['unique_count'],'observation_counts':full['statuses'],'observation_rows':len(full['method_observations']),'failed_subtest_rows':full['statuses']['SUBTEST_FAIL'],'methods_with_failed_subtests':sum(any(r['status']=='SUBTEST_FAIL' for r in v) for v in raw.values()),'raw_parent_ids_missing_only_due_subtest_reporting':full['not_observed_ids']},'utf8_rerun':{'methods':target['unique_count'],'counts':target['statuses'],'exit_code':target['exit_code'],'duration_seconds':target['elapsed_seconds']},'frozen_head_baseline':{'methods':len(fr),'counts':dict(collections.Counter(outcome(v) for v in fr.values())),'exit_code':frozen['exit_code'],'duration_seconds':frozen['duration_seconds'],'scope':frozen['profile'],'supplemental_foreign_untracked_test':'src/catalog/testcases/test_task33_place_nature_localization.py unchanged only for comparison'},'fresh_gnu_head_baseline':{'methods':len(co),'counts':dict(collections.Counter(outcome(v) for v in co.values())),'exit_code':compiled['exit_code'],'duration_seconds':compiled['duration_seconds'],'scope':compiled['profile'],'browser_runtime_changed':False},'django_method_slots_all_profiles':full['unique_count']+target['unique_count']+len(fr)+len(co),'raw_observation_rows_all_django_profiles':len(full['method_observations'])+len(target['method_observations'])+len(frozen['records'])+len(compiled['records']),'js':{'scripts':len(js['results']),'script_counts':dict(collections.Counter(r['status'] for r in js['results'])),'node_entries':js['aggregate_node_counts'],'bare_file_wrappers':sum(r['bare_assertion_script'] for r in js['results']),'named_node_tests':js['aggregate_node_counts']['tests']-sum(r['bare_assertion_script'] for r in js['results']),'stock_browser_scripts_not_run':len(js['browser_scripts'])},'standalone_windows':{'counts':load('standalone-results.json')['counts'],'exit_code':load('standalone-results.json')['exit_code']},'standalone_backup_wsl_posix_copy':{'methods':len(load('wsl-backup-results.json')['records']),'exit_code':load('wsl-backup-results.json')['exit_code'],'counts':dict(collections.Counter(r['status'] for r in load('wsl-backup-results.json')['records']))},'discovery':{'worktree_ci_no_label':618,'worktree_catalog':1950,'worktree_full':2090,'worktree_missing':qual['local_worktree_ci_missing'],'missing_tracked_source':qual['local_missing_from_tracked_tests'],'missing_foreign_untracked_source':qual['local_missing_from_untracked_tests'],'head_ci_no_label':head['head_no_label_count'],'head_catalog':head['head_catalog_count'],'head_full':head['head_explicit_full_count'],'head_ci_missing':head['head_ci_missing_count'],'head_wrapper_missing':head['head_wrapper_missing_count'],'github_execution':'NOT RUN'},'snapshot':meta,'commands':{'full':'.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/test-review/full-suites.py full','utf8':'.venv/Scripts/python.exe -X utf8 docs/qa/module13-2026-10-11-r1/test-review/full-suites.py target','frozen':'.venv/Scripts/python.exe -X utf8 docs/qa/module13-2026-10-11-r1/test-review/baseline-run.py','compiled':'.venv/Scripts/python.exe -X utf8 docs/qa/module13-2026-10-11-r1/test-review/baseline-run.py --compiled-head','js':'.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/test-review/run-js.py','standalone':'.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/test-review/standalone-python.py','backup_wsl':'wsl.exe --exec python3 /mnt/c/kidsmap/docs/qa/module13-2026-10-11-r1/test-review/wsl-backup-tests.py','discovery':'.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/test-review/manage-discovery.py'},'no_application_or_assertion_changes':meta['source_unchanged_since_parent_snapshot']}
(P/'counts.json').write_text(json.dumps(counts,indent=2),encoding='utf-8')
(P/'results.json').write_text(json.dumps({'counts':counts,'normalized_methods':normalized,'module_matrix':{k:dict(v) for k,v in sorted(matrix.items())},'finding':'CROSS-QA-02; root owns individual finding and repair prompt','not_run':{'stock_browser_scripts':js['browser_scripts'],'integration_boundaries':['Real Google OAuth/GA/Maps','Real SMTP and IndexNow','Production restore','Actual GitHub CI','Linux QA04 Unix-socket guarded migration/conversion/crash bodies on Windows TCP profile']},'classification_limits':['Frozen donor is HEAD tracked application plus actual WORKTREE .mo files, not pristine generated gettext baseline','One foreign untracked test module copied unchanged into donor after pristine HEAD discovery','Fresh GNU HEAD profile is a separate unit control; actual native browser runtime remains unchanged','Nine artifact failures require rendered runtime recheck by root; passing GNU control does not close historical UI findings','Historical locale IDs require root deduplication; do not create eleven duplicate product defects']},indent=2),encoding='utf-8')
failed=[r for r in normalized if r['status']=='FAIL']
failure_table='\n'.join('| '+r['id']+' | '+r['classification']+' | '+r['frozen_head']+' | '+r['compiled_head']+' |' for r in failed)
notrun_table='\n'.join('| '+category+' | '+str(number)+' |' for category,number in counts['django_classifications'].items() if category.startswith('ENVIRONMENT_') and category!='ENCODING_ERROR_RECOVERED_FRESH_UTF8')
report=f'''# Module13: fresh full-suite evidence

Role: integration-reviewer; execution identity: /root/cross_tests; 2026-10-11; AUDIT ONLY. Definition: `.agents/agents/integration-reviewer/agent.md`. Assigned ownership: this folder and its ignored scratch. Parent owns rendered browser acceptance, final findings, journal and handoff.

Snapshot: `C:/kidsmap`, HEAD `{meta['head']}`, branch `{meta['branch']}`, active_run `{meta['active_run']}`. Dirty application WORKTREE preserved. Application source digest `{meta['source_digest']}`; 2,788 files unchanged against parent entry snapshot. Python {meta['python']}, Django {meta['django']}, Node {meta['node']}, PostgreSQL17.11. Production and actual GitHub execution: NOT RUN.

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
{failure_table}

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
{notrun_table}

Three stock Playwright scripts remain NOT RUN: they require dedicated synthetic `sessionid`, `127.0.0.1`, special config and review cooldown3 fixtures incompatible with the parent stand's current session profile. Parent's fresh browser acceptance is separate. Real Google OAuth/GA/Maps SDK, real SMTP/IndexNow, production restore and actual GitHub CI remain NOT RUN. No claims about RU/AZ/EN viewport rendered PASS are made from these backend/jsdom checks.

## 8. Recommendations

After separately approved scope, make the CI and full wrapper enumerate the same tracked suite. Establish a genuinely disposable Linux legacy profile for hardcoded QA04 guarded bodies, retaining negative isolation checks and assertions. Reproduce failures with authoritative locale builds, compare contracts before changing legacy expectations, close streaming test responses in a later test-only fix plan. Root retains historical finding IDs and uses fresh rendered evidence for locale defect disposition.

Commands and exact per-script argv are in [counts.json](counts.json) and [js-results.json](js-results.json). Full runner as launched is [full-runner-at-launch.py](full-runner-at-launch.py); later own harness change affects I/O capture only. [Raw full log](full-django.log), [UTF8 replay](utf8-rerun.log), [frozen donor log](baseline-django.log), [GNU donor log](baseline-compiled-django.log), [GNU build](head-gettext-build.log). Ephemeral CSRF values in own failure traces masked; raw originals remain only in ignored own scratch. [Redaction record](redaction.json).

## 9. P0/P1/P2/P3 и handoff

P2 confirmed: CROSS-QA-02. No independently confirmed P0/P1 application defect; baseline/environment results are separated from product findings. Named handoff: **kidsmap-orchestrator /root** — integrate unique counts and raw exits, preserve runtime locale FAIL, deduplicate known locale causes against current screenshots, retain42 unavailable legacy bodies and Windows cleanup limitation, publish module13 report/journal and future repair decision text. No application/source/assertion changes, commit/push/deploy or production interaction.
'''
(P/'REPORT.md').write_text(report,encoding='utf-8')
print(json.dumps({'normalized':counts['django_normalized'],'classification':counts['django_classifications'],'js':counts['js'],'baseline_frozen':counts['frozen_head_baseline']['counts'],'baseline_gnu':counts['fresh_gnu_head_baseline']['counts'],'report':str(P/'REPORT.md')},indent=2))
