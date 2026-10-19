import ast,hashlib,json,re,shutil,struct,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site20-pc-fix-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text())
entry=read(O/'source-entry.json');applied=read(O/'source-applied.json');candidate=read(O/'approved-candidate-manifest.json');green=read(O/'evidence/green-backend.json')
assert green['exit']==0 and len(green['test_ids'])==len(set(green['test_ids']))==122 and not green['failures'] and not green['errors']
assert any('Ran 122 tests in 58.451s' in s for s in green['summary'])
suites=['browser-layout-az','browser-layout-ru','browser-layout-en','browser-negative','browser-saves','browser-add-green','browser-stale-email','browser-json-error-snapshots','browser-file-error-central','browser-sentinels-green','browser-console','browser-delete-navigation','browser-keyboard','browser-statistics-message','browser-delete-route']
results={};failed=[]
for name in suites:
 d=read(O/'evidence'/f'{name}.json');assert d.get('rows') and not d.get('error') and not d.get('pageerrors'),name
 checks=[v for row in d['rows'] for v in row['checks'].values()];results[name]={'rows':len(d['rows']),'checks':len(checks),'PASS':checks.count(True),'FAIL':checks.count(False)}
 for row in d['rows']:
  bad=[k for k,v in row['checks'].items() if v is False]
  if bad:failed.append({'suite':name,'id':row['id'],'failed':bad,'preexisting_continue403':row.get('known_existing_continue403',False)})
 if name.startswith('browser-layout-'):assert d['no_fixture_write'] and d['CSS200'] and not d['local_errors']
 if 'no_fixture_write' in d:assert d['no_fixture_write'],name
add_failures=[r for r in failed if r['suite']=='browser-add-green'];statistics_failures=[r for r in failed if r['suite']=='browser-saves'];delete_failures=[r for r in failed if r['suite']=='browser-delete-navigation']
assert len(failed)==12 and len(add_failures)==6 and len(statistics_failures)==3 and len(delete_failures)==3,failed
assert all(r['failed']==['landing200'] and r['preexisting_continue403'] for r in add_failures),add_failures
assert all(r['failed']==['no_overflow'] and r['id'].startswith('siteanalytics-') and r['id'].endswith('-360-_save') for r in statistics_failures),statistics_failures
assert all(r['failed']==['correct_route'] and r['id'].endswith('-1440') for r in delete_failures),delete_failures
assert all(results[n]['rows']==120 and results[n]['checks']==1320 and not results[n]['FAIL'] for n in suites if n.startswith('browser-layout-'))
assert results['browser-saves']['rows']==135 and results['browser-saves']['FAIL']==3
baseline=read(O/'evidence/browser-add-baseline.json');assert len(baseline['rows'])==2 and sum(v is False for r in baseline['rows'] for v in r['checks'].values())==1 and baseline['rows'][1]['known_existing_continue403']
for name in ['browser-saves','browser-json-error-snapshots','browser-file-error-central','browser-sentinels-green']:
 assert not read(O/'evidence'/f'{name}.json').get('local_errors'),name
audit=read(O/'evidence/fixture-audit.json');assert audit['native_upload_bytes_exact'] and audit['expected_added_gallery_rows']==14 and audit['original_gallery_display_rows_unchanged']==10
r=subprocess.run(['python3',str(O/'preserve.py')],capture_output=True,text=True);assert r.returncode==0,r.stderr
preservation=read(O/'evidence/preservation.json')
for name in ['qa_settings.py','runtime.py','qa_urls.py','seed.py','proxy.py','playwright.json','test_site19_candidate.py']:(O/name).write_bytes((Q/name).read_bytes())
ast.parse((R/'src/catalog/testcases/test_site_qa20_permission_actions.py').read_text())
old=(O/'entry-source/src/catalog/templates/admin/catalog/shared_settings_change_form.html').read_bytes();new=(R/'src/catalog/templates/admin/catalog/shared_settings_change_form.html').read_bytes()
assert new.count(b'\r\n')==old.count(b'\r\n')+4 and new.count(b'\n')==new.count(b'\r\n')
png={}
for p in (O/'png').glob('*.png'):
 b=p.read_bytes();assert b[:8]==b'\x89PNG\r\n\x1a\n';w,h=struct.unpack('>II',b[16:24]);assert w>0 and h>0;png[p.name]={'sha256':sha(p),'width':w,'height':h}
(O/'png-manifest.json').write_text(json.dumps(png,indent=2))
summary={k:sum(d[k] for d in results.values()) for k in ['rows','checks','PASS','FAIL']}
verification={'status':'SITE20 permission presentation CLOSED LOCAL; exact2file patch applied; separate SITE23/SITE24 P3 OPEN; no blanket native GREEN','source_count':1035,'application_refinements':0,'backend':{'methods':122,'seconds':58.451,'exit':0,'failures':0,'errors':0,'RED_methods':8,'RED_failed_methods':3,'RED_observations':29,'initial_GREEN_environment_error':'20s QueryCanceled in unchanged public catalog test, retained; same source/expectations/timeouts fresh sequential retry122OK'},'native':{**summary,'suites':results,'retained_out_of_scope_failures':failed,'permission_matrix':{'states':360,'checks':3960,'PASS':3960},'new_synthetic_gallery_rows_retained':14,'PNG':len(png),'initial_screenshot_timeout':'No complete matrix returned, not counted PASS; original/CLI/PNG retained. Same assertions split3language batches, viewport images; own browser closed/reopened.'},'fixture':audit,'preservation':preservation,'module10':'14OPEN (9P2/5P3) =13entry -SITE20 +SITE23 +SITE24; full module acceptance pending','retained_LOCAL_closures':['SITE01','SITE15','SITE06','SITE19','SITE21','SITE08','SITE22','module09 composite'],'separate_OPEN':['SITE23 add-only Continue redirect403','SITE24 statistics dashboard saved-message overflow360','SITE11 localization','remaining canonical findings'],'NOT_RUN':['full module10/global/module11 acceptance','production/deploy/release','full WCAG/cross-browser/physical devices','successful deletion POST in new native checks'],'production':'UNKNOWN; not contacted','execution':'/root inline, no independent-agent claim'}
verification['status']='SITE20 permission presentation CLOSED LOCAL; exact2file applied; separate SITE23/SITE24/SITE25 P3 OPEN; no blanket native GREEN'
verification['module10']='15OPEN (9P2/6P3) =13entry -SITE20 +SITE23 +SITE24 +SITE25; full module acceptance pending'
verification['separate_OPEN'].insert(2,'SITE25 existing delete link wrong relative URL')
(O/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2));(O/'source-final.json').write_text(json.dumps({'sources':applied['sources'],'git':entry['git']},indent=2))
(O/'findings').mkdir(exist_ok=True)
finding='''# SITE-QA-23 — add-only Continue creates image then opens forbidden editor

**OPEN / P3 / LOCAL, 2026-10-18.** Separate pre-existing navigation contract, not an unauthorized write or SITE20 regression. [Fresh prepatch native baseline](../evidence/browser-add-baseline.json): add-only gallery actor can legally add; `_save` POST302→admin index200, `_continue` POST302→new object's change GET403, each exactly1new row/1adminLog/file. Original template already offered both actions on desktop.

[Actual applied-source matrix](../evidence/browser-add-green.json) reproduces6Continue403 paths:3languages×360/1440, after invalid-file200/no-write and valid retry. All12valid native additions persist exact bytes/caption and one log;6Save exits land200. The6landing200 failures are deliberately retained, not changed to green. New mobile editable marker exposes the same existing route behavior at360.

Source: installed Django6.0.2 ModelAdmin.response_add unconditionally redirects `_continue` to `obj_url`; `_changeform_view` requires change on POST and view/change on GET. `SiteGalleryImageAdmin` has no response_add override. [Installed source references](../evidence/library-contract.json). No source change to this path in approved SITE20 diff. Backend ACL remains correct: actor has add only and GET existing/new object is forbidden.

Impact: successful add is presented as403; retry may duplicate an image (duplicate retry impact not independently tested). Confidence high for native route/storage behavior. P3 navigation/usability; production UNKNOWN. Owner Django-reviewer/frontend-admin. Next separate concrete policy/plan: either offer only Save/exit to add-only actors or route successful Continue to an accessible destination. Do not grant change permission as a workaround. No fix of SITE23 authorized/applied here.

SITE20's view-only forbidden save presentation is closed within its approved exact scope. Shared-template controls/permissions tested separately from post-add navigation; no blanket all-native PASS. With separate SITE24 statistics message overflow, Module10 now14OPEN(9P2/5P3)=13−20+23+24, full acceptance pending.
'''
(O/'findings/SITE-QA-23.md').write_text(finding)
statistics_finding='''# SITE-QA-24 — saved message overflows statistics destination at360

**OPEN / P3 / LOCAL, 2026-10-18.** In native9model save acceptance, three analytics `_save` states (AZ/RU/EN,360) correctly POST302→statisticsGET200 with exact data/one log, but document no_overflow fails. Original three failures remain unchanged in [browser-saves](../evidence/browser-saves.json); [RU screenshot](../png/save-siteanalytics-360.png) shows the long brand-linked success message extending right of the viewport.

[Focused native save/dismiss/restore](../evidence/browser-statistics-message.json) records document/alert geometry before and after the real dismiss button, with no style/transport injection, and exact native brand restoration. These positive diagnostic checks are causal measurements, not a replacement for the original three FAIL results. Own extra synthetic logs retained.

Source wiring: src/catalog/domain_admin/site.py:SiteAnalyticsAdmin.changelist_view directly renders templates/admin/catalog/site_analytics.html, which extends admin/base_site.html and has km-statistics-page. The approved changed shared_settings_change_form.html is absent from this destination. Runtime has no settings-editor or settings-hub root there. Dashboard/site.py/base/CSS sources are in1033unchanged current-source hashes. Relevant graph coverage unavailable/metadata_changed; read source is authority. Prepatch native360statistics-toast measurement NOT RUN; pre-existing attribution is inference from unchanged destination/message source and bypass of the modified template, not a claimed historical observation. Existing SITE08 editor and SITE22 hub-only toast scopes remain closed locally.

P3: bounded success notification overflow; valid persistence and allowed navigation work. No production evidence. Owner frontend-admin/analytics-reviewer; next concrete bounded plan for statistics message wrapping/controls, AZ/RU/EN/360–1440/native long-success states and neighbor parity. Do not expand global alert CSS without measuring consumers. No application fix authorized/applied for SITE24.

Module10 now14OPEN(9P2/5P3)=13entry−SITE20+SITE23+SITE24. Full module acceptance pending.
'''
(O/'findings/SITE-QA-24.md').write_text(statistics_finding)
delete_finding='''# SITE-QA-25 — existing delete link resolves to nonexistent object path

**OPEN / P3 / LOCAL, 2026-10-18.** [Native AZ/RU/EN desktop checks](../evidence/browser-delete-navigation.json) retain3correct_route FAIL. View+delete gallery actor can see the retained Delete link; Tab/Enter opens the existing unified navigation confirmation. Confirming navigation (not deletion) goes to wrong address. [Focused native route](../evidence/browser-delete-route.json): raw href=delete/, resolved /admin/catalog/sitegalleryimage/1/change/delete/, then redirect to admin index with nonexistent object ID1/change warning. No deletion POST and original gallery/media/log state unchanged. Direct real /1/delete/ GET200 works, as tested360; this is a UI URL defect, not a server authority bypass.

Source: src/catalog/templates/admin/catalog/shared_settings_change_form.html contains existing href="delete/"; static/admin/js/kidsmap_admin_form_shell.js:2005 intercepts to an existing confirm and assigns the same href. Exact href bytes are present before/after approved SITE20 diff. Prepatch native deletion-link navigation NOT RUN; attribution to pre-existing path is source/URL-resolution inference, unlike SITE23's direct prepatch native proof. SITE20 explicitly preserved delete link and made no destination changes.

Initial QA helper incorrectly expected immediate navigation from the link, skipping existing unified modal; timeout/script/CLI retained. Current helper confirms navigation and retains actual wrong-route FAIL. Its metric called delete_confirmation200 checks HTTP200 only: it does not prove the landing page is a confirmation. The independent correct_route failure and diagnostic chain establish the defect. Server confirmation GET and UI link behavior remain separate.

Impact bounded authorized admin delete navigation fails with no data loss in tested paths. P3, production UNKNOWN. Owner frontend-admin with Django URL contract. Next separate exact plan: build existing admin delete URL from opts/original.pk via Django admin_urlname/admin_urlquote; preserve permission condition and unified modal, test multiple models/PKs/locales/negative roles. No application fix authorized/applied here.

Module10 now15OPEN(9P2/6P3)=13entry−SITE20+SITE23+SITE24+SITE25; full acceptance pending.
'''
(O/'findings/SITE-QA-25.md').write_text(delete_finding)
for path in [O/'findings/SITE-QA-23.md',O/'findings/SITE-QA-24.md']:
 text=path.read_text().replace('14OPEN(9P2/5P3)=13−20+23+24','15OPEN(9P2/6P3)=13−20+23+24+25').replace('14OPEN(9P2/5P3)=13entry−SITE20+SITE23+SITE24','15OPEN(9P2/6P3)=13entry−SITE20+SITE23+SITE24+SITE25')
 path.write_text(text)
report=f'''# SITE-QA-20 — применён согласованный scope, 2026-10-18

**SITE20 permission presentation CLOSED LOCAL.** Exact2file diff applied, apprefinements0. Чистый просмотр больше не предлагает Save/пустой action card; change-only сохраняет обе кнопки, add-only gallery получает existing mobile editable layout, view+delete сохраняет delete link. **Отдельные OPEN/P3:** [SITE23](findings/SITE-QA-23.md) (add-only Continue→GET403, native before/after proof), [SITE24](findings/SITE-QA-24.md) (statistics saved-message overflow360) и [SITE25](findings/SITE-QA-25.md) (existing delete link wrong relative URL). Для24/25 pre-existing attribution — source inference; blanket native GREEN не заявляется.

[Authorization](authorization.json): human «принимаем» после точного2file плана. [Approved input plan](IMPLEMENTATION_PLAN.md), [implemented diff](implemented.diff), [applied hashes](applied.json), [verification](verification.json). Скопированный PLAN/manifest описывает исторический NOT APPLIED input; текущий applied.json — факт применения. LOCAL HEAD852938d96764ae315b92859e3651e5ea62054a36 / codex/module09-transfer-2026-10-16-r1 +preserved dirty WORKTREE. Production UNKNOWN/не контактировали. /root inline по canonical roles, без independent-agent claim.

## Изменение и доказательства

Ровно shared_settings_change_form.html +new test_site_qa20_permission_actions.py. Save/root editable marker: has_change_permission or add+has_add_permission; independent delete guard retained; no empty actions for pure view.9runtimeconsumers. No CSS/JS/PO/model/schema/ACL/roles/revisions/destinations edit.1035sources:1existing changed/1newtest/1033others unchanged; CRLF preserved; reverse-apply/diff-check0. Source graph generation2026-10-16 stale, coverage unavailable/metadata_changed/newtest not_tracked; relevant source/runtime verified rather than treating graph as proof.

Fresh8method RED:3failed/29observations/5PASS/0errors →122unique backend GREEN/58.451s/OK/exit0. Первый122run имел0assertionFAIL/1unchanged public catalog QueryCanceled at20s,159.788s; retained. Fresh own retry DB/same source/tests/20sstatement+2slock limits passed122; assertions not weakened. New regression8 +114existing cover media/permissions/JSON/public wiring/concurrency/sidebar/save destinations.

## Actual-source browser results

{summary['rows']}rows/{summary['checks']}checks: **{summary['PASS']}PASS/{summary['FAIL']}retained outside-scope FAIL (6SITE23/3SITE24/3SITE25)**. [Per-suite counts](verification.json).360permission states/3960checks allPASS:9consumers×view/change-only×3langs×6widths plus add-only/delete-only cases. Exact rows are in evidence. Full width set360/390/768/1024/1280/1440. Exact save controls/marker/card/delete link, allowed button visibility/bounds/labels, locale/root/document overflow and current CSS200 verified; no row/log/media write in GET matrix.

135native change saves/restores (108states+27restores), both actions3langs×360/1440 across9consumers: exact persistence/oneLog/onehop destination/keyboardEnter PASS;3statistics saved-message destination overflowFAIL retained as SITE24. Six sections retain SITE22 hub exits; analytics/catalog/gallery retain own routes. Direct viewer/denied/add-only existing-object requests and missingCSRF403/no-write PASS. Actual Tab navigation checked separately. Direct deletion confirmationGET200 works, but3desktop native Delete navigation checks fail because retained href=delete/ resolves under change/; SITE25 OPEN/no deletionPOST. Initial helper skipped existing unified modal and timed out; original CLI/script plus corrected actual modal path retained. HTTP200 alone is not a confirmation-page success. Old hidden delete-only mobile link explicitly recorded.

Gallery add-only:12invalid-file200/no-write/draft/error/focus controls and12native valid retry creates.6Save exits200;6Continue creates thenGET403. Fresh prepatch desktop baseline proves same Continue403 before application; [SITE23](findings/SITE-QA-23.md) kept OPEN. Invalid JSON, central file error/link/focus, invalid email, stale valid-file409/no-write/draft/oldtoken/reselection all checked. Place/Event exact native geometry equals fresh prepatch baseline; no settings marker/formCSS/hubCSS on neighbors.

Fresh{len(png)}PNG. Initial fullpage screenshot timed out30s after first RU frame; incomplete matrix not counted. Diagnostic1440×4630/fontsloaded/complete/buttonsabsent, own browser normalclose/reopen. Original script/CLI/PNG retained; same assertions split by language with viewport images. Viewport frames plus DOM checks are not full-page visual coverage. Core pageerrors0; expected403/409 and blocked fonts.googleapis.com ERR_FAILED diagnostics classified, no console-clean or fullWCAG claim.

## Изоляция, fixtures и сохранность

Own33630/m10s20-fix-r1-app, normalm10s20_fix_r1, isolated RED/freshGREEN/retry DBs/cache/media/private-media/email, envclear/DJANGO_TESTING=1/current3rootlocales before setup, integrationsdisabled; sourceRO/ownscratchRW/internalQA network/no publishedPG. Only own verified PID stopped/restarted for apply, browser profile closed/reopened for harness recovery; foreign runtimes unchanged. Bootstrap infrastructure completed then wrapper's s/socket collision failed only report-script write; saved recovery, no repeated setup/app change.

Original10gallery display rows and original{audit['original_media_paths_hashes_unchanged']}media names/bytes preserved.14own synthetic gallery rows/media retained from2prepatch+12postpatch additions, every upload byte matches the valid fixture; {audit['new_verified_responsive_cache_files']}newcachefiles validated against actual source/manifest/dimensions. Scoped scalars restored through native forms,3abouttexts normalize one terminal blank via existing CharField(strip=True); Catalog3JSON restored. {audit['logs_expected_and_actual']}expected synthetic adminLogs/timestamps retained. Exact full DB/media inventory rollback not claimed. [Read-only audit](evidence/fixture-audit.json).

40priorpackages/8205files/sharedMO/.cbmignore/refs/indexbytes/empty staging/activeNONE/foreign identities-state preserved; guide/MASTER append-only. **Module10 now15OPEN(9P2/6P3)=13entry−SITE20+SITE23+SITE24+SITE25; full acceptance pending.** SITE01/15/06/19/21/08/22/module09 LOCAL closures retained; SITE11/remaining canonical OPEN. NOT RUN fullmodule/global/module11/production/release/deploy/crossbrowser/physicaldevices/fullWCAG. No commit/push/production/foreigncleanup. Next separate policy/plan decision for SITE23/SITE24/SITE25 or other remaining findings.
'''
(O/'REPORT.md').write_text(report)
append=f'\n\n## SITE-QA-20 CLOSED LOCAL; SITE23 OPEN — 2026-10-18 pc-r1\n\n**Approved exact2file SITE20 applied; scoped permission presentation CLOSED LOCAL.** [REPORT](LINKREPORT), [verification](LINKVERIFY), [newSITE23](LINKFINDING). Sharedtemplate view-only noSave/noemptycard; change preservesSave; add-onlymobile marker; existingdelete retained. Apprefinements0/source1035/1existingchanged+1newtest/1033othersunchanged. Fresh8RED3failedmethods29observations→122uniqueGREEN58.451sOK; first122run1publicSQL20stimeout/0assertionFAIL retained, same source/tests/limits fresh retryPASS. Native{summary["rows"]}rows/{summary["checks"]}checks:{summary["PASS"]}PASS/{summary["FAIL"]}knownpreexistingSITE23landingFAIL; no blanketnativeGREEN.360permissionstates3960PASS,135native9modelwrites/restores,negativeACL/CSRF/stale409/errors/Tab/Enter/deleteconfirmation/PlaceEventparity/currentCSS checks. Freshprepatch add-only2nativePOST provedContinuecreates→GET403;6postpatchContinue same baselinefailure,6Saveexit200; SITE23/P3 remainsOPEN, no redirect/ACL workaround. {len(png)}PNG; initial30sscreenshottimeout/incomplete matrix retained, same assertions language batches+viewportframes; own browser normalclose/reopen. Original10galleryrows/media preserved,14synthetic newrows/uploads+verifiedcache/{audit["logs_expected_and_actual"]}logs retained; formcleanedaboutstrip/JSONrestoration explicit.40priorpackages8205files/MO/.cbmignore/refs-index/activeNONE/foreignruntimes preserved;docsappendonly. **Module10 remains13OPEN(9P2/4P3)=13−20+23, fullacceptancepending**; priorLOCALclosures retained. No commit/push/deploy/production/global/module11;inline/no independent-agent claim.\n'
append=append.replace('SITE-QA-20 CLOSED LOCAL; SITE23 OPEN','SITE-QA-20 CLOSED LOCAL; SITE23/SITE24 OPEN').replace('[newSITE23](LINKFINDING)','[newSITE23](LINKFINDING), [newSITE24](LINKFINDING24)').replace('knownpreexistingSITE23landingFAIL','retainedSITE23/SITE24FAIL').replace('SITE23/P3 remainsOPEN, no redirect/ACL workaround.','SITE23/P3 remainsOPEN, no redirect/ACL workaround. Three analytics360destination success-message overflow failures retained as SITE24/P3; unchanged destination source implies pre-existing, native prepatch toast measurement NOTRUN.').replace('Module10 remains13OPEN(9P2/4P3)=13−20+23','Module10 now14OPEN(9P2/5P3)=13−20+23+24')
append=append.replace('SITE23/SITE24 OPEN','SITE23/SITE24/SITE25 OPEN').replace('[newSITE24](LINKFINDING24)','[newSITE24](LINKFINDING24), [newSITE25](LINKFINDING25)').replace('retainedSITE23/SITE24FAIL','retainedSITE23/SITE24/SITE25FAIL').replace('14OPEN(9P2/5P3)=13−20+23+24','15OPEN(9P2/6P3)=13−20+23+24+25')
append+='\nAdditional SITE25/P3: retained existing delete href=delete/ resolves under change/, native3desktop correct_route FAIL; direct real confirmationGET200/no deletionPOST. Initial helper skipped unified modal, corrected full native modal path without changing route assertion. Pre-existing attribution from unchanged href/source, native prepatch delete path NOTRUN.\n'
for doc,h in entry['documents'].items():
 path=R/doc;backup=Q/'documents'/doc;assert sha(path)==h and path.read_bytes()==backup.read_bytes()
 prefix='' if doc.startswith('docs/qa/') else '../qa/';text=append
 for key,target in [('LINKREPORT','REPORT.md'),('LINKVERIFY','verification.json'),('LINKFINDING24','findings/SITE-QA-24.md'),('LINKFINDING25','findings/SITE-QA-25.md'),('LINKFINDING','findings/SITE-QA-23.md')]:text=text.replace(key,prefix+O.name+'/'+target)
 path.write_bytes(path.read_bytes()+text.encode());assert path.read_bytes().startswith(backup.read_bytes())
check=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True);assert check.returncode==0,check.stderr
assert all(sha(R/p)==h for p,h in applied['sources'].items()) and sha(R/'.git/index')==entry['git']['index_sha256']
(O/'evidence/final-checks.json').write_text(json.dumps({'source1035hashes_match':True,'candidate_exact':True,'other_existing_unchanged':1033,'index_unchanged':True,'documents_append_only':True,'native_git_diff_check_exit':0},indent=2))
manifest={p.relative_to(O).as_posix():sha(p) for p in sorted(O.rglob('*')) if p.is_file() and p.name!='artifact-manifest.json'}
(O/'artifact-manifest.json').write_text(json.dumps(manifest,indent=2));assert all(sha(O/p)==h for p,h in manifest.items())
print(json.dumps({'status':verification['status'],'backend122':'PASS','native':summary,'PNG':len(png),'artifact_files':len(manifest),'module10':verification['module10']},indent=2))
