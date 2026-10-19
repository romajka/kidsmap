import collections,hashlib,json,re,shutil,struct,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site20-pc-plan-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
entry=read(O/'source-entry.json');assert len(entry['sources'])==1034 and all(sha(R/p)==h for p,h in entry['sources'].items())
candidate=read(O/'candidate-manifest.json')
for p,d in candidate['files'].items():
 assert sha(O/'candidate'/p)==d['candidate_sha256']
 assert (sha(R/p) if (R/p).exists() else None)==d['before_sha256']
red=read(O/'evidence/red-backend.json');assert red['exit']==1 and len(red['failures'])==29 and not red['errors']
failed_methods={f.split(' (')[0] for f in red['failures']};assert len(failed_methods)==3
assert any('Ran 8 tests in 2.582s' in s for s in red['summary'])
native=read(O/'evidence/browser-baseline.json');rows=native['rows'];checks=[v for r in rows for v in r['checks'].values()]
assert len(rows)==75 and len(checks)==498 and checks.count(True)==375 and checks.count(False)==123
assert native['no_fixture_write'] and not native['pageerrors']
assert native['before']==native['after'] and native['after']['media']['admin_log_count']==0
assert len(native['local_errors'])==3 and all(e['status']==403 and e['path']=='/admin/catalog/catalogcontentsettings/1/change/' for e in native['local_errors'])
assert set(native['blocked'])=={'fonts.googleapis.com'}
failure_counts=collections.Counter(k for r in rows for k,v in r['checks'].items() if not v)
assert dict(failure_counts)=={'permission_actions':60,'no_empty_action_card':54,'editable_marker':6,'mobile_add_actions':3}
assert len([r for r in rows if r.get('native_post')])==3
shutil.copyfile(Q/'candidate-render.json',O/'evidence/candidate-render.json');render=read(O/'evidence/candidate-render.json');assert render['passed'] and render['checks']==180
# The first audit used a guessed +5 newline count. Correct only that audit metric;
# candidate bytes, native checks and permission assertions remain identical.
shutil.copyfile(O/'evidence/static-apply.json',O/'evidence/static-apply-initial.json')
p='src/catalog/templates/admin/catalog/shared_settings_change_form.html';old=(R/p).read_bytes();new=(O/'candidate'/p).read_bytes()
newline={'original_CRLF':old.count(b'\r\n'),'candidate_CRLF':new.count(b'\r\n'),'added_lines':4,'no_lone_LF':new.count(b'\n')==new.count(b'\r\n'),'original_bytes_outside_exact_diff_preserved':True}
assert newline['candidate_CRLF']==newline['original_CRLF']+4 and newline['no_lone_LF']
static=read(O/'evidence/static-apply.json');static['original_CRLF_preserved']=True;static['newline_audit']=newline;static['audit_correction']='Initial guessed +5 count was false; actual four inserted template lines independently audited. No candidate/assertion changes.'
(O/'evidence/static-apply.json').write_text(json.dumps(static,indent=2))
for pkg,files in entry['prior_packages'].items():
 for p,h in files.items():assert sha(R/'docs/qa'/pkg/p)==h,(pkg,p)
assert len(entry['prior_packages'])==39 and sum(map(len,entry['prior_packages'].values()))==8134
assert all(sha(R/p)==h for p,h in entry['shared_mo'].items()) and sha(R/'.cbmignore')==entry['cbmignore']
git=lambda *a:subprocess.check_output(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a],text=True).strip()
assert git('rev-parse','HEAD')==entry['git']['head'] and git('branch','--show-current')==entry['git']['branch'] and git('rev-parse','task33-progress')==entry['git']['task33_ref'] and not git('diff','--cached','--name-only') and sha(R/'.git/index')==entry['git']['index_sha256']
assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
old_containers={s.split()[1]:(s.split()[0],s.split()[2]) for s in entry['containers']};now={s.split()[1]:(s.split()[0],s.split()[2]) for s in subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines()};assert all(now.get(k)==v for k,v in old_containers.items())
setup=read(O/'evidence/setup.json');assert subprocess.check_output(['docker','inspect',setup['app'],'--format','{{.Id}}'],text=True).strip()==setup['container_id']
for name in ('qa_settings.py','qa_urls.py','runtime.py','seed.py','proxy.py','playwright.json'):(O/name).write_bytes((Q/name).read_bytes())
(O/'evidence/test-isolation.json').write_bytes((Q/'test-isolation.json').read_bytes())
pngs={}
for f in (O/'png').glob('*.png'):
 b=f.read_bytes();assert b[:8]==b'\x89PNG\r\n\x1a\n';w,h=struct.unpack('>II',b[16:24]);assert w in (390,1440) and h>0;pngs[f.name]={'sha256':sha(f),'width':w,'height':h}
assert len(pngs)==27
(O/'png-manifest.json').write_text(json.dumps(pngs,indent=2))
(O/'visual-review.json').write_text(json.dumps({'execution':'/root inline, no independent-agent claim','reviewed':['all_viewer-catalogcontentsettings-ru-1440.png','gallery_adder-sitegalleryimage-ru-390.png'],'observed':['Readonly JSON plus active desktop Save buttons','Add-only gallery mobile form has no visible Save controls'],'candidate_visual':'NOT RUN'},indent=2))
graph={'project':'C-kidsmap','root':'C:/kidsmap','status':'ready','generation':'2026-10-16T18:56:53Z','nodes':51523,'edges':280457,'coverage':'site.py/shared template metadata_changed coverage_unavailable; previous new test not_tracked','navigation':'search_graph four bounded results, has_more=false; INHERITS trace base→six section admins, truncated=false; verified all six in current source','source_runtime':'four current template assignments; installed admin registry confirms nine consumers; current source and runtime override graph','caveat':'stale index, not exhaustive or completeness proof; no reindex/cache artifact'}
(O/'graph-evidence.json').write_text(json.dumps(graph,indent=2))
preservation={'sources_unchanged':1034,'application_changes':0,'prior_packages':39,'prior_files':8134,'shared_MO_cbmignore':True,'HEAD_branch_task33_index_empty_staging':True,'active_run_NONE':True,'foreign_runtime_identities_states':len(old_containers),'own_container_identity':True,'documents_append_only':True}
verification={'status':'SITE20/P3 CONFIRMED OPEN; exact2file PLAN READY, approval pending; NOT APPLIED','backend_RED':{'methods':8,'failed_methods':3,'passed_methods':5,'failure_observations':29,'errors':0,'seconds':2.582,'exit':1},'native_baseline':{'rows':75,'checks':498,'control_PASS':375,'expected_FAIL':123,'failure_categories':dict(failure_counts),'native_viewer_forbidden_posts':3,'no_row_log_media_write':True,'PNG':27,'pageerrors':0,'unexpected_local_HTTP':0,'expected403':3,'blocked_external_fonts':True},'candidate_render':{'checks':180,'runtime_consumers':9,'permission_truth_table':16,'PASS':True,'applied_or_native_GREEN':False},'static_apply_AST_CRLF':True,'preservation':preservation,'module10':'13OPEN (9P2/4P3); full module acceptance pending','retained_LOCAL':['SITE01','SITE15','SITE06','SITE19','SITE21','SITE08','SITE22','module09 composite'],'NOT_RUN':['application implementation/GREEN','candidate rendered-browser acceptance','full module10/global/release/production/module11/cross-browser/WCAG/physical devices'],'execution':'/root inline, no independent-agent claim'}
(O/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2))
(O/'source-final.json').write_text(json.dumps({'sources':entry['sources'],'git':entry['git'],'application_changes':0},indent=2))
plan='''# SITE20 — разрешённые действия редакторов: Implementation Plan

> **For agentic workers:** Execute inline task-by-task under the repository engineering contract. The approved scope is binding; no delegation or commits are requested.

**Goal:** В режиме просмотра убрать недоступное сохранение и пустую карточку действий; сохранить разрешённые сохранение, добавление и удаление.

**Architecture:** Использовать переданные Django `has_change_permission`, `has_add_permission`, `has_delete_permission` и `add` в общем шаблоне девяти редакторов. Save и editable marker разрешены при change либо add+add permission. Блок действий присутствует при разрешённом сохранении или существующем разрешённом delete. Серверная авторизация остаётся источником прав.

**Tech Stack:** installed Django 6.0.2, Jazzmin, Django templates, existing scoped CSS, PostgreSQL, Chromium1247 through Playwright CLI.

**Spec:** [Current finding and evidence](REPORT.md), [original SITE20](../site-qa19-fix-2026-10-18-pc-r1/findings/SITE-QA-20.md).

## Global Constraints

- LOCAL HEAD852938d96764ae315b92859e3651e5ea62054a36; branch codex/module09-transfer-2026-10-16-r1; dirty WORKTREE1034sources preserved. Production UNKNOWN.
- Status PLAN READY / NOT APPLIED. Human «дальше» authorizes this investigation/plan; application implementation awaits this separate scope decision under AGENTS.md. Earlier SITE22 approval covered only SITE22.
- Scope exactly2files in candidate-manifest.json. No CSS/JS/PO/model/schema/ACL/preset/revision/destination/public behavior edits. No commit/push/deploy/production/cleanup; no new module11.
- Tests DJANGO_TESTING=1 before setup, env cleared, own DB/cache/media/email, current three isolated locales, integrations disabled, read-only repository except explicit approved application patch.
- All source/QA packages/MO/.cbmignore/refs/index bytes/foreign runtimes preserved. Guide and MASTER append-only. No raw private records/secrets/logs/graph caches in artifacts.

### Task 1: Action visibility in the existing shared settings template

**Files:** Modify `src/catalog/templates/admin/catalog/shared_settings_change_form.html`; create `src/catalog/testcases/test_site_qa20_permission_actions.py`.

**Interfaces:** existing Django change-form context. Exact predicate for saves and editable marker: `has_change_permission or add and has_add_permission`; delete keeps `has_delete_permission and not add`. Nine consumers: six SiteSettings section proxies, SiteAnalytics, CatalogContentSettings, SiteGalleryImage. Add-only gallery must gain existing mobile editable styling; delete-only plus view retains its existing delete link and gains no save controls.

- [ ] Revalidate all before/candidate hashes and diff SHA from candidate-manifest; confirm unchanged snapshot/prior closure evidence.
- [ ] Prepare a fresh own profile `m10s20-fix-r1-app`, loopback33630, normal DB `m10s20_fix_r1`, RED `test_m10s20_fix_r1`, own separate media/cache/private-media/email. Build current isolated AZ/RU/EN locales before setup. Reuse isolated configuration patterns in this package, without executing scripts in any sealed prior package.
- [ ] Copy the complete candidate regression below into own scratch module `test_site20_candidate`; fresh RED command: `docker exec m10s20-fix-r1-app python /mnt/c/kidsmap/.tmp/site20-pc-fix-r1/runtime.py test test_site20_candidate`. Expect8methods,3failed methods/29failure observations,0errors on this source snapshot. Current PLAN evidence proves this RED; do not claim fresh fix-profile RED until executed.
- [ ] Apply exactly proposed.diff after user scope approval; preserve CRLF and unrelated bytes. New test bytes must equal candidate hash. No test expectation changes to obtain GREEN.
- [ ] Run fresh GREEN with new disposable `test_m10s20_fix_green_r1`, same isolation and runtime test command using these labels: `catalog.testcases.test_site_qa20_permission_actions catalog.testcases.test_site_qa22_save_exit catalog.testcases.test_site_qa19_catalog_content catalog.testcases.public.TestCatalogContentSettingsWiring catalog.testcases.test_site_qa06_media_validation catalog.testcases.test_site_qa01_media_permissions catalog.testcases.test_site_qa15_settings_concurrency catalog.testcases.admin.TestSiteGalleryImageAdminMedia catalog.testcases.admin.TestAdminSidebarStructure catalog.testcases.test_public_section_switches`. Expected122unique methods (114existing+8new), no failures/errors. No GREEN run or application behavior claim in PLAN.
- [ ] Actual-source native browser acceptance after apply: all9consumers, viewer/change-only, AZ/RU/EN at360/390/768/1024/1280/1440; add-only gallery GET+valid native add/error/retry/both save actions, view+delete gallery link retained, denied users and forged viewer POST403 with row/log/media no-write. Test keyboard Tab/Enter has no unavailable save targets; allowed actions retain focus/labels. Check no overflow, current CSSHTTP200, no unexpected console/pageerrors/localHTTP. No injected classes/styles/transport rewrite in acceptance.
- [ ] Preserve SITE22 one-hop hub exits for six sections and `_continue` editor behavior, SITE15 invalid/stale no-write, SITE06 media validation, SITE19 JSON saves/errors, SITE08 responsive layout. Place/Event neighbor form controls/geometry must remain unchanged. Observe existing mobile delete visibility separately; do not claim a redesign of delete-only mobile controls.
- [ ] Verify exact original/scoped fixtures or explicitly qualified form normalization/cache derivatives; retain synthetic logs/timestamps. Report all failures, recovery and NOT RUN. Preserve prior packages; append guide/MASTER; seal artifacts. Only then consider scoped SITE20 CLOSED LOCAL; full module10 acceptance remains separate.

## Exact reviewable patch

```diff
'''+(O/'proposed.diff').read_text()+'''```

## Evidence and risk

Current8method RED:3failed methods/29observations,5passed/0errors. Current actual-source75native rows:375controlsPASS/123expected action failures;3native viewer POST403/no writes. Candidate180isolated render/truth-table checks PASS, which prove template logic/compilation only. Candidate not applied; native candidate geometry, keyboard and add/save persistence still require approved implementation acceptance. Changed template is shared by9consumers; exact scope covers all their permission states. Existing deletion permission semantics remain Django's. Remaining SITE11 and other module10 findings stay open.
'''
(O/'IMPLEMENTATION_PLAN.md').write_text(plan)
report='''# SITE-QA-20 — следующий точный план, 2026-10-18

**SITE20/P3 CONFIRMED OPEN; exact2file PLAN READY / approval pending, NOT APPLIED.** [План](IMPLEMENTATION_PLAN.md), [точный diff](proposed.diff), [before/candidate hashes](candidate-manifest.json), [verification](verification.json).

LOCAL HEAD852938d96764ae315b92859e3651e5ea62054a36 / codex/module09-transfer-2026-10-16-r1; dirty1034sources unchanged. Режим bounded audit/plan; /root inline по canonical frontend-admin + Django permission verification, без independent-agent claim. User «дальше» продолжает module10; прошлое «применяем» относилось к SITE22, не к новому scope. Production UNKNOWN/не контактировали.

## Подтверждённая причина и влияние

`src/catalog/templates/admin/catalog/shared_settings_change_form.html:126` выводит обе Save buttons без проверки `has_change_permission`; строка15 добавляет mobile editable marker только при change permission. Backend уже передаёт нужные permission flags. Source assignment/inheritance и runtime registry подтвердили9потребителей:6section proxies, SiteAnalytics, CatalogContentSettings, SiteGalleryImage. Граф C-kidsmap ready, но generation2026-10-16T18:56:53Z и relevant coverage unavailable/metadata_changed; выводы проверены текущими исходниками/installed runtime, не графом.

Существующий view-only пользователь видит desktopSave, native click→403. У view+delete gallery лишнее Save; у add-only gallery настоящая форма добавления на mobile без Save из-за отсутствия editable marker. Это одна область представления разрешённых действий; server authorization bypass не обнаружен. Новых ACL/ролей/политик патч не вводит. P3: недоступные действия/непоследовательный UI, production impact UNKNOWN.

## Свежие проверки

- Новый стенд33620/m10s20-plan-r1-app, own normal/test DB, envclear/DJANGO_TESTING=1/current3locale before setup, RO source/ownRW scratch/separate test media-cache-email, integrations disabled. Existing QA PG/network identity/internal/no published PG verified; foreign app containers untouched.
- Backend8methods in2.582s/exit1:3failed methods/29failure observations,5passed,0errors. Readonly9consumers×3locales, delete-only and add-only marker fail as expected. Direct viewer/denied POST403, deniedGET, change-only actions, singleton forbiddenadd and gallery add-only denial of existing object PASS. Test bodies unchanged after observed RED.
- Actual-source75native rows/498checks:375controlPASS,123expectedRED. Failure breakdown:60permission_actions (54view-only+6delete/view),54empty-action-card,6missing add-only marker,3hidden mobile add-only Save. Roles/languages/currentGET200/no-overflow/deletion count controls preserved.3native catalog viewerPOST403/no row/log/media changes; baseline settings/gallery/media hashes/logcount identical after; adminLog0.27freshPNG,2visual samples reviewed.
- Pageerrors0; only3expected local403; expected blocked fonts.googleapis.com produces ERR_FAILED console diagnostics; no blanket console-clean claim.
- Candidate renderer uses actual20role/model contexts +16permission truth-table cases,180checksPASS; compiled only, no applied-source/native candidate GREEN. git apply --check and candidate testAST PASS. Initial static audit guessed +5CRLF insertion count and returned false; retained result, independent byte audit proves exactly4newCRLF lines/no loneLF. Candidate/test/native assertion bytes unchanged by audit correction.

## Предлагаемое изменение

Ровно2файла: existing shared template +new8method regression. Save groups/root marker follow change or add+add permission; omit empty action sidebar for pure view; preserve independent existing delete guard. Existing CSS handles mobile once correct marker supplied. No backend/ACL/model/schema/PO/CSS/JS/destination changes. Exact content in [diff](proposed.diff); candidate remains solely under QA package.

## Сохранность и границы

1034sources unchanged;39priorpackages/8134files/sharedMO/.cbmignore/HEAD/branch/task33/index bytes/empty staging/activeNONE/foreign container identities-state verified. Own settings/catalog/gallery/media state restored by being unchanged; only own login/language sessions and negative requests used, no successful native application writes. Synthetic migration/seed fixtures remain on own profile. Guide/MASTER append-only.

**Module10 remains13OPEN(9P2/4P3), full acceptance pending.** SITE01/15/06/19/21/08/22 and module09 LOCAL closures retained. SITE11/othercanonical findings remain OPEN. NOT RUN: implementation/GREEN/nativecandidate, fullmodule/global/release/production/module11/crossbrowser/WCAG/physicaldevices. No commit/push/deploy/production/cleanup. Next: user decision on exact2file plan, then fresh fix-profile RED→apply→122backend/native acceptance.
'''
(O/'REPORT.md').write_text(report)
append='\n\n## SITE-QA-20 PLAN READY — 2026-10-18 pc-r1\n\n**SITE20/P3 CONFIRMED OPEN; exact2file PLAN READY / approval pending; NOTAPPLIED.** [REPORT](LINKREPORT), [PLAN](LINKPLAN), [diff](LINKDIFF), [verification](LINKVERIFY). Sharedtemplate unconditionalSave verified9runtimeconsumers; proposed only permission-gated save/empty action sidebar and add-only editable mobile marker +new8method regression; existing delete semantics retained. Fresh8RED3failedmethods/29observations/5PASS/0errors,2.582s. Native75rows498checks:375controlsPASS123expectedRED;3nativeviewerPOST403/no settings/gallery/media/logwrite,27PNG/0pageerrors/onlyexpected403 and blocked externalfontconsole. Candidate20actual role/model contexts+16truth-tablecases180checksPASS; compile/applycheck/AST/CRLF PASS, notapplied/nativecandidateGREEN NOTRUN. Initial guessed +5CRLF audit corrected to4addedlines with originalfalse result retained; candidate/assertionsunchanged. Source1034unchanged/app0changes;39priorpackages8134files/MO/.cbmignore/refs-index/activeNONE/foreignruntimes preserved;docsappendonly. **Module10 remains13OPEN(9P2/4P3), fullacceptancepending**; SITE01/15/06/19/21/08/22/module09LOCALclosures retained. Next separate exactscope decision then freshown RED→apply→122backend/native acceptance. No commit/push/deploy/production/global/module11;inline/no independent-agent claim.\n'
for doc,h in entry['documents'].items():
 path=R/doc;backup=Q/'documents'/doc;assert sha(path)==h and path.read_bytes()==backup.read_bytes()
 prefix='' if doc.startswith('docs/qa/') else '../qa/'
 text=append
 for key,target in [('LINKREPORT','REPORT.md'),('LINKPLAN','IMPLEMENTATION_PLAN.md'),('LINKDIFF','proposed.diff'),('LINKVERIFY','verification.json')]:text=text.replace(key,prefix+O.name+'/'+target)
 path.write_bytes(path.read_bytes()+text.encode());assert path.read_bytes().startswith(backup.read_bytes())
diff=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True);assert diff.returncode==0,diff.stderr
assert all(sha(R/p)==h for p,h in entry['sources'].items()) and sha(R/'.git/index')==entry['git']['index_sha256']
(O/'evidence/final-checks.json').write_text(json.dumps({'git_diff_check_exit':0,'source1034_unchanged':True,'index_unchanged':True,'candidate_NOT_APPLIED':True,'documents_append_only':True},indent=2))
files={p.relative_to(O).as_posix():sha(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name!='artifact-manifest.json'}
(O/'artifact-manifest.json').write_text(json.dumps(files,indent=2));assert all(sha(O/p)==h for p,h in files.items())
print(json.dumps({'status':verification['status'],'sources_unchanged':1034,'prior_packages':39,'prior_files':8134,'native':verification['native_baseline'],'artifact_files':len(files)},indent=2))
