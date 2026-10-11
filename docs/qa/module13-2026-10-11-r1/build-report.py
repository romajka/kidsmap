"""Assemble fresh evidence; raw attempts remain intact. No application mutations."""
from pathlib import Path
import json,csv,hashlib,collections,shutil
P=Path(__file__).resolve().parent;R=P.parents[2]
def read(name):return json.loads((P/name).read_text(encoding='utf-8'))
def write(name,data):(P/name).write_text(json.dumps(data,ensure_ascii=False,indent=2),encoding='utf-8')
snap=read('snapshot.json');historical=read('reconciliation/historical-findings.json');tests=read('test-review/counts.json');browser=read('browser-review/counts.json')
excluded=[];rows=[]
skip={
 'gallery-network.result.txt':{'simulated-save-network-failure-keeps-input','failed-network-write-not-persisted'},
 'specialist-flow.result.txt':{'author-cannot-person-edit'},
 'final-lifecycle.result.txt':{'native-branch-detach','network-employee-access-revoked-by-detach','cancelled-event-removed-from-upcoming'},
 'lifecycle-readback.result.txt':{'cancelled-event-removed-from-default-list-fresh-session'},
 'error-final.result.txt':{'final-native-error-summary'},
}
for f in sorted(P.glob('*.result.txt')):
 d=json.loads(f.read_text(encoding='utf-8'))
 for i,raw in enumerate(d.get('rows',[])):
  x=dict(raw);scenario=x.get('scenario',x.get('id',f.stem+':'+str(i)));x['scenario']=scenario
  reason=None
  if scenario in skip.get(f.name,set()):reason='Invalid/overstrict QA oracle or blocked validation setup; see fresh corrections and raw attempt. Not an application finding.'
  if f.name=='lifecycle-readback.result.txt' and x.get('status')=='FAIL':reason='Cancelled entries intentionally remain with visible cancelled badge; contract-readback supersedes removal assumption.'
  if reason:excluded.append({'result':f.name,'row':i,'scenario':scenario,'raw_status':x.get('status'),'reason':reason});continue
  x['evidence_result']=f.name;x.setdefault('role','specialist' if f.name=='specialist-flow.result.txt' else 'owner');x.setdefault('lang','ru');x.setdefault('width',1440)
  x['module']='13';x['snapshot']=snap['source_digest'];x['execution_identity']='/root';x['evidence_kind']='fresh rendered native UI with saved/readback checks as specified'
  x['language_proof']='requested locale; effective HTML not captured in every root transition (explicit-language visual proof is separate browser matrix)'
  if scenario=='fresh-draft-error-navigation-visible':x['evidence_kind']='Transient in-viewport rect sample during smooth scroll; complete settled/unobstructed proof is navigation-settled.result.txt.'
  if f.name=='gallery-network.result.txt' and scenario=='approved-gallery-public-loaded':x['width']=1440;x['metadata_correction']='Actual context viewport1440; raw width390 label was wrong.'
  rows.append(x)
# The first completed loading probe remains proof; its premature smooth-scroll assertion does not.
old=read('error-loading.result.attempt1.txt')
for i,x in enumerate(old['rows']):
 if x['scenario']=='error-jump-visible-focus':excluded.append({'result':'error-loading.result.attempt1.txt','row':i,'raw_status':x['status'],'reason':'Smooth scrolling sampled prematurely; navigation-final fresh draft passes visible focus after bounded completion.'});continue
 x=dict(x);x.update(evidence_result='error-loading.result.attempt1.txt',module='13',snapshot=snap['source_digest'],execution_identity='/root',language_proof='explicit owner RU route');
 if x['scenario']=='delayed-save-recovers-honestly':x['width']=390
 rows.append(x)
functional=list(rows)
for raw in read('browser-review/matrix.json')['rows']:
 x=dict(raw);x['module']='13';x['snapshot']=snap['source_digest'];x['execution_identity']='/root/cross_browser';x['evidence_result']='browser-review/'+x.get('evidence_result','matrix.json')
 if x.get('screenshot'):x['screenshot']='browser-review/'+x['screenshot']
 rows.append(x)
excluded.extend(read('browser-review/matrix.json')['excluded_invalid_oracles'])
counts=collections.Counter(x['status'] for x in rows);fc=collections.Counter(x['status'] for x in functional)
write('matrix.json',{'basis':'Fresh module13 assertions only; historical matrices and raw invalid attempts are not counted','rows':rows,'excluded_invalid_oracles':excluded})
with(P/'matrix.csv').open('w',encoding='utf-8-sig',newline='')as out:
 fields=['module','scenario','role','lang','width','status','snapshot','execution_identity','url','evidence_result','screenshot','shot','classification','language_proof'];w=csv.DictWriter(out,fieldnames=fields,extrasaction='ignore');w.writeheader();w.writerows(rows)
fresh={
 'SITE-QA-01':('P1','GLOBAL-MEDIA-ACL','acl-native.result.txt','staff','/admin/catalog/sitegalleryimage/ and ajax-upload/','Staff actor has0 model permissions. Open global media editor, upload fictional PNG through its native chooser, reload and visit home.','403 and no global media write.','Page200, upload200 and public logo changes; current synthetic stand only.'),
 'ANALYTICS-QA-01':('P2','GLOBAL-ANALYTICS-ACL','acl-native.result.txt','staff','/admin/catalog/siteanalytics/','Same permissionless staff opens site analytics.','Model-authorized access only;403.','200 with global analytics surface.'),
 'ANALYTICS-QA-03':('P2','ANALYTICS-ORIGIN-PORT','redirect-counters.result.txt','guest','/ru/events/track/','Open fictional ready Place1 on localhost:8831, reveal phone and invoke native tracked phone action.','Accepted legitimate same-origin event;200 with documented delta.','Native request returns403. No Origin proxy/adapter applied; rejected delta cannot establish a recorded click.'),
 'ORG-QA-02':('P2','NETWORK-GRANT-UI','cross-effects.result.txt','owner','/ru/account/organizations/1/','Invite fictional employee EDITOR/all_network; recipient accepts via notifications; then find native revoke action in organization team.','Existing network employee permissions can be revoked through authorized cabinet.','UI contains invitation/refresh controls but no employee or grant revoke action. Detach does remove effective branch-editor rights; this is a separate successful check.'),
 'ACCESS-QA-03':('P2','NETWORK-GRANT-UI','cross-effects.result.txt','owner','/ru/account/organizations/1/','Repeat ORG-QA-02 network employee-management inspection.','Native grant management under current ACL/CAS contract.','Same missing surface as ORG-QA-02; preserve both historical IDs, count one cause and one repair scope.'),
 'SOCIAL-QA-01':('P2','REVIEW-RATING-READBACK','social-private.result.txt','outsider','native review forms for Place2, Activity1, Specialist1 and Event1','Choose rating4 and fictional literal HTML text, submit pending review, reload editor.','Saved rating4 selected while content remains escaped.','Persisted candidate content survives but all four editor rating controls reopen empty. Public approved text escapes correctly.'),
 'PLACE-QA-06':('P2','COMPILED-LOCALE-FRESHNESS','browser-review/locale-check.result.json','admin','/admin/catalog/place/2/change/ and /en/admin/catalog/place/2/change/','Open AZ and EN admin Place forms at all six widths on the attested native runtime.','Map-disabled explanatory message uses active language.','12 cells show Russian message. Active correct AZ/EN PO entries exist, compiled runtime MO keys are absent. Runtime assets unchanged; historical isolated-builder repair claim does not prove they were selected on this PC.'),
}
by_id={x['id']:x for x in historical['findings']}
for fid,(sev,cause,evidence,role,url,steps,expected,actual)in fresh.items():
 old=by_id[fid];source='\n'.join(old.get('source_cause',[]));source_refs=', '.join(old.get('source_refs',[]))
 text=f'''# {old['title']} — fresh module13 corroboration

ID **{fid}**, {sev}; root cause group **{cause}**. Role: {role}. LOCAL `http://localhost:8831{url}`; checkout `C:/kidsmap`, HEAD `{snap['head']}`, dirty WORKTREE `{snap['source_digest']}`. PRODUCTION NOT RUN.

**Steps:** {steps}

**Expected:** {expected}

**Actual:** {actual}

**Fresh evidence:** [{evidence}](../{evidence}); [normalized matrix](../matrix.json), [screenshot manifest](../screenshots-manifest.json). [Original ID/source analysis](../../../{old['run']}/findings/{fid}.md) is historical context, not fresh runtime proof.

**Cause / confidence:** fresh trigger is confirmed; prior source analysis below is retained with attribution. Source references: {source_refs}. No exact clean-HEAD UI replay for this trigger; introduction/regression date UNKNOWN. PLACE-QA-06 specifically classifies generated-runtime-assets failure; the separate donor test comparison does not change the browser runtime.

{source}

**Priority:** {sev}; {'permissionless staff can alter shared branding, so the effect crosses object ownership' if sev=='P1' else 'bounded incorrect UI, permission surface, readback or event collection contract; no production exploitation or critical data loss proven'}.

**Fix scope / dependencies:** retain prior canonical source references and business contracts; review current dirty edits first. Network grant aliases share one implementation. Generated catalogs and missing source translations have different causes. [Standalone repair prompt]({fid}-repair.txt). Audit findings do not authorize implementation.
'''
 # Relative original link from findings/ to another module folder is ../../, not ../../../.
 actual_original='../../'+Path(old['finding']).relative_to(Path('docs/qa')).as_posix()
 text=text.replace('../../../'+old['run']+'/findings/'+fid+'.md',actual_original)
 (P/'findings'/f'{fid}.md').write_text(text,encoding='utf-8')
 prompt=f'''Работай в C:/kidsmap (на другом ПК сначала найди checkout). Прочитай AGENTS.md, канонические .agents, docs/qa/module13-2026-10-11-r1/REPORT.md и findings/{fid}.md в том же run. Задача: {fid}, {old['title']}, {sev}. Сохрани чужие изменения, active_run и стенды. Без commit/push/deploy/production.

Подтверждённый trigger: {steps}
Ожидание: {expected}
Факт: {actual}
Свежие доказательства: docs/qa/module13-2026-10-11-r1/{evidence}; matrix.json; screenshots-manifest.json. Source refs: {source_refs}.
Группа причины: {cause}. {'ORG-QA-02 и ACCESS-QA-03 исправляются одним scope, без дублирования.' if cause=='NETWORK-GRANT-UI' else ''}

Сначала проверь текущий source и составь конкретный план исправления с файлами, зависимостями и meaningful regression проверками. Согласно audit scope реализацию выполняй только после согласования этого плана. Не меняй существующие assertions ради green. Применимые проверки: DJANGO_TESTING=1, собственные DB/cache/media/private-media/email, вымышленные данные, внешние интеграции выключены. После согласованного исправления повтори реальный UI trigger, сохранение/reload и PC/mobile RU/AZ/EN; сохраняй candidate/live и ACL. Отдельно классифицируй source translation, generated assets, baseline и environment failures. Сохрани свежий отчёт, точные команды/counts/exit codes/screenshots и NOT RUN ограничения.
'''
 (P/'findings'/f'{fid}-repair.txt').write_text(prompt,encoding='utf-8')
# New IDs retain the independently produced evidence locations.
new=[('CROSS-QA-01','P2','RESCHEDULED-ORG-EVENT','Future rescheduled event disappears from organization','findings/CROSS-QA-01.md','findings/CROSS-QA-01-repair.txt'),('CROSS-QA-02','P2','FULL-SUITE-DISCOVERY','Configured CI discovery omits1452 tracked HEAD tests','findings/CROSS-QA-02.md','findings/CROSS-QA-02-repair.txt'),('CROSS-QA-03','P3','RU-DISTRICT-SOURCE-TRANSLATION','RU district placeholder uses AZ text','browser-review/CROSS-QA-03.md','browser-review/CROSS-QA-03-repair.txt')]
fresh_list=[{'id':fid,'severity':x[0],'cause':x[1],'finding':f'findings/{fid}.md','prompt':f'findings/{fid}-repair.txt','fresh_status':'FAIL'}for fid,x in fresh.items()]+[{'id':x[0],'severity':x[1],'cause':x[2],'finding':x[4],'prompt':x[5],'fresh_status':'FAIL'}for x in new]
write('fresh-findings.json',{'confirmed_ids':len(fresh_list),'distinct_causes':len({x['cause']for x in fresh_list}),'severity_ids':dict(collections.Counter(x['severity']for x in fresh_list)),'items':fresh_list,'regression_status':'No new app regression established by exact baseline controls; new audit IDs are not proof of newly introduced bugs.'})
findex='# Fresh findings and standalone repair prompts\n\n10 IDs /9 root causes; ORG-QA-02 + ACCESS-QA-03 share one repair scope. No app fixes authorized by this audit.\n\n| ID | Priority | Finding | Copyable prompt |\n| --- | --- | --- | --- |\n'
for x in fresh_list:findex+=f"| {x['id']} | {x['severity']} | [finding]({x['finding']}) | [prompt]({x['prompt']}) |\n"
(P/'FINDINGS.md').write_text(findex,encoding='utf-8')
observations={'combined_browser_assertions':dict(counts),'root_functional_assertions':dict(fc),'delegated_browser_assertions':browser['counts'],'native_delegated_pages':browser['page_observations'],'native_section_pages':216,'excluded_invalid_qa_oracles':len(excluded),'django':tests,'fresh_findings':{'ids':10,'causes':9,'P0':0,'P1_ids':1,'P2_ids':8,'P3_ids':1}}
if(P/'screenshots-manifest.json').exists():
 manifest=read('screenshots-manifest.json');observations['screenshots']={k:manifest[k]for k in ['all_retained_png','derived_contact_sheets','root_png']};observations['screenshots']['delegated_completed_native']=browser['native_png_complete'];observations['screenshots']['delegated_retained_native']=browser['native_png_retained']
write('counts.json',observations)
module_scopes={
 '01':('FAIL','owner/admin/guest','draft/reload/logout; moderation; mixed price live/candidate; gallery; locale','place-flow.result.txt;review-flow.result.txt;mixed-price.result.txt;gallery-network.result.txt;browser-review/locale-check.result.json'),
 '02':('FAIL','owner/outsider/employee/admin','empty organization; canonical connect/confirm; team invite; missing revoke UI','org-flow.result.txt;org-complete.result.txt;connection-program.result.txt;cross-effects.result.txt'),
 '03':('PASS','specialist/owner/admin/guest','proposal5-step; claim;2 practices; cooperation; private document authorization','specialist-flow.result.txt;specialist-confirm.result.txt;social-private.result.txt'),
 '04':('FAIL','owner/admin/guest','physical/online native publish; reschedule organizer projection; honest cancellation','event-create.result.txt;event-publish.result.txt;event-online.result.txt;event-cross.result.txt;contract-readback.result.txt'),
 '05':('PASS','owner/admin/guest','program moderation/conflict; groups20/80; hours separate; detach snapshot','program-create.result.txt;activity-flow.result.txt;cross-effects.result.txt;final-lifecycle.result.txt'),
 '06':('PASS','guest','rendered filled/empty catalog; native query submit; map API across OFF/ON; real SDK NOT RUN','browser-review/matrix.json;sections-search-map.result.txt'),
 '07':('FAIL','owner/employee/outsider/staff/specialist','login/logout; native invitations; editor denied after detach; private ACL; missing grant management','cross-effects.result.txt;lifecycle-readback.result.txt;social-private.result.txt;acl-native.result.txt'),
 '08':('PASS','admin/owner','native moderation/reject/correct/approve; admin Place/Event18 cells; volunteer-role complete path NOT RUN','review-flow.result.txt;specialist-confirm.result.txt;event-publish.result.txt;browser-review/matrix.json'),
 '09':('FAIL','outsider/admin/guest','four reviews candidate/public escaping; empty rating readback; favorite double press/reload; invitation inbox','social-private.result.txt;gallery-network.result.txt;cross-effects.result.txt'),
 '10':('FAIL','admin/staff/owner/guest','section OFF/ON menu/direct/search/map/data; permissionless global-logo write','sections.result.txt;sections-search-map.result.txt;data-preservation.json;acl-native.result.txt'),
 '11':('PASS','guest','old canonical URL redirect; language rendered surfaces; complete metadata/indexability reacceptance NOT RUN','redirect-counters.result.txt;browser-review/matrix.json'),
 '12':('FAIL','guest/staff','one logical place_view redirect delta; native phone Origin403; global analytics permissions','redirect-counters.result.txt;acl-native.result.txt'),
 '13':('FAIL','all assigned fake roles','final cross-module acceptance with current findings and mandatory gaps','REPORT.md;matrix.json;test-review/results.json'),
}
with(P/'module-coverage.csv').open('w',encoding='utf-8-sig',newline='')as out:
 fields=['module','name','cross_scenarios_status','roles','fresh_scope','snapshot','evidence','complete_module_reacceptance'];w=csv.DictWriter(out,fieldnames=fields);w.writeheader()
 for line in(P/'journal-entry.txt').read_text(encoding='utf-8').splitlines():
  if not line.startswith('| '):continue
  cells=[x.strip()for x in line.split('|')];mid=cells[1]
  if mid not in module_scopes:continue
  status,roles,scope,evidence=module_scopes[mid];w.writerow({'module':mid,'name':cells[2],'cross_scenarios_status':status,'roles':roles,'fresh_scope':scope,'snapshot':snap['source_digest'],'evidence':evidence,'complete_module_reacceptance':'Only final module13 scope executed'if mid=='13'else'NOT RUN; historical audit is separate'})
repair_order='''1. SITE-QA-01 global media permission boundary (P1); then ANALYTICS-QA-01 analytics authorization. Verify both permissionless staff and authorized admin separately.
2. CROSS-QA-02 full-suite discovery/profile declaration. Keep baseline failures visible; do not change assertions or emulate legacy guard markers to obtain green.
3. Compiled-catalog provenance/selection (PLACE-QA-06, shared dependency with PUBLIC-QA-03/EVENT-QA-01/SITE-QA-07). Rebuild only isolated outputs after approved scope. Missing active RU district key CROSS-QA-03 needs source translation work separately; rebuilding obsolete content will not fix it.
4. CROSS-QA-01 event projection, ORG-QA-02/ACCESS-QA-03 shared native grant-management surface, SOCIAL-QA-01 rating readback, ANALYTICS-QA-03 Origin authority/port matching. Retain ACL, canonical confirmation/CAS and moderation boundaries.
5. Review historical-only P1/P2 items and mandatory gaps before planning release. Evidence from earlier reports is not fresh; no production action is authorized.'''
master='''# Module13 MASTER_AUDIT — fresh and historical evidence separated

LOCAL audit only. One lead `/root`; source, reconciliation, integration and browser support were assigned disjoint folders, with at most3 specialists simultaneously. Production NOT RUN. This run does not overwrite `docs/agent-audits/MASTER_AUDIT.md`.

Fresh overall decision **FAIL**, not project acceptance. [Report](REPORT.md), [fresh counts](counts.json), [current findings/prompts](FINDINGS.md), [fresh scenario matrix](matrix.csv).

**10 fresh confirmed IDs /9 causes:** P0=0, P1=1ID, P2=8IDs (7 causes), P3=1ID. Seven IDs are freshly corroborated historical findings and three IDs are newly recorded in this run. New IDs do not establish recent regressions.

Historical ledger:81 unique IDs /77 grouped causes /86 occurrences. Seven PLACE repair claims are historical claims, not automatic closure;74 other historical IDs were unresolved in their own reports. Do not add these numbers to the fresh count. [All historical source/evidence reconciliation](reconciliation/historical-findings.json), [coverage20362 rows](reconciliation/coverage.csv), [routes/models/admin map](reconciliation/source-coverage.csv).

Dirty critical-place trigger was freshly replayed: reject reason display, native draft/reload/logout continuation, mixed price+name+address publication, gallery/reload and visible error focus passed their recorded cases. PLACE-QA-03 exact mixed price regression trigger passes6/6; this does not close every scenario in PLACE-QA-01–07. Current compiled map locale still fails PLACE-QA-06.

| Historical ID | Prior priority | Fresh module13 status | Original finding (historical) |
| --- | --- | --- | --- |
'''
for x in historical['findings']:
 status='FAIL — fresh corroboration'if x['id']in fresh else 'PASS exact mixed-price trigger; complete closure NOT RUN'if x['id']=='PLACE-QA-03'else 'NOT RUN for complete finding; see limited cross-module checks'
 master+=f"| {x['id']} | {x['severity']} | {status} | [{x['title']}]({('../../'+x['finding'])}) |\n"
# root file is run/; original repository paths resolve from run with ../../../, not ../../.
master=master.replace('](../../docs/qa/','](../')
master+='\n## Repair order and dependencies\n\n'+repair_order+'\n\n## Mandatory limits\n\n'+'''Native employee revoke remains NOT RUN because the UI control is absent (fresh finding); branch detach was confirmed to deny editor form and preserve program snapshot/groups/prices. Cancelled cards intentionally remain with cancelled badge; false removal expectations were excluded.

Fresh backend42 guarded/POSIX bodies +1 Windows streaming cleanup case NOT RUN; raw exit1 retained. Three stock browser fixtures NOT RUN. Real Google/Maps/OAuth/GA/SMTP/IndexNow, production, GitHub run, native Safari/Firefox/devices, screen readers, complete keyboard cycles and every state of every control across18 cells remain NOT RUN. Root RU error/network/conflict probes do not fill all54 delegated owner-state NOT RUN cells.

Operational ConversionRun/Mapping/healthz and release/recovery surfaces are unmapped or outside native end-user scope. Source/graph absence does not imply dead code. No deletion or cleanup recommendation is established.
'''
(P/'MASTER_AUDIT.md').write_text(master,encoding='utf-8')
table='''| Cross-module scenario | Roles | Result and fresh evidence |
| --- | --- | --- |
|01 Organization without branches|owner/admin|PASS draft/invalid URL/reload/reject-correct-approve; org-flow, org-complete, review-flow|
|02 Places + canonical connect/confirm|owner/outsider/admin|PASS partial native creation, materialize, reload/logout, reject/correct, independent recipient confirmation; place-flow, connection-program|
|03 Program/activity/groups/prices/schedule|owner/admin/guest|PASS native nested save/reload, separate place hours, grouped20/80 rates, shared candidate approve and guest live preservation; program-create, activity-flow, cross-effects|
|04 Specialist/claim/cooperation/practices|specialist/admin/owner/guest|PASS five-step draft/reload, invalid experience, claim review, reciprocal consent,2 practice rows, private identity approval/download ACL; specialist-flow, specialist-confirm, social-private|
|05 Physical + online events|owner/admin/guest|PASS native drafts/submission/admin publish, accessible organizer; event-create, event-publish, event-online|
|06 Moderation roundtrip|owner/admin/guest|PASS explicit rejection/reason/correction/resubmit/approve/public; review-flow|
|07 Published edit/two tabs|owner/admin/guest|PASS live unchanged until approval; stale Program POST409 retains loser input; mixed place price6/6; cross-effects, mixed-price|
|08 Detach/revoke/cooperation/reschedule/cancel|owner/employee/specialist/guest|Mixed: detach retains local program snapshot, groups/rates and denies employee editor; cooperation cancellation/private ACL PASS; explicit employee revoke NOT RUN/missing UI; reschedule organization projection FAIL CROSS-QA-01; cancelled-card honest state PASS|
|09 Sections OFF/ON|admin/owner/guest|PASS255 assertions:216 direct rendered pages across18 cells,36 menu observations, native save/reload + workspace;4 search/map projection assertions PASS; sections, sections-search-map, data-preservation|
|10 Media/private/reviews/favorites/redirect/view|owner/admin/outsider/guest|Gallery and private docs ACL, reviews escaped, native favorite double click/reload, canonical redirect and one place_view delta PASS; saved rating readback FAIL SOCIAL-QA-01; permissionless global media/stats FAIL; native phone event403 FAIL|
'''
report=f'''# Module13 — финальная межмодульная приёмка

2026-10-11 r1. Role/execution: **kidsmap-orchestrator `/root`**, actual definition `.agents/agents/kidsmap-orchestrator/agent.md`; named support and evidence attribution in their reports. **AUDIT ONLY; decision FAIL in the executed scope.** No overall project PASS.

LOCAL checkout **C:/kidsmap**. HEAD `{snap['head']}`, branch `{snap['branch']}`, active_run **{snap['active_run']}**. Foreign dirty WORKTREE retained:18 tracked entry changes and untracked previous QA/repair artifacts. Snapshot SHA over2788 source/runtime files: `{snap['source_digest']}`. [Entry snapshot](snapshot.json), [runtime attestation](runtime-final.json), [preservation entry](preservation-entry.json), [final verification](verification.json). PRODUCTION NOT RUN. Missing mandatory documents: **none** ([checked paths](documents.json)).

Own PostgreSQL17.11 container `kidsmap-module13-20261011-r1`, ID `3901fd73729774f5cccd1d58a18de5de544916fef4d3c53c8508fc6b1b5c1765`, local55444; database/role module13; anonymous volume `31d266ca1ab287854d9b6b68a76b9e52cc4f69ec99a5275a1626ba5bdbf12ed2`. HTTP **http://localhost:8831**, PID23204, `use_reloader=False`, DEBUGFalse, Python3.12.15/Django6.0.2. DJANGO_TESTING1, separate LocMem cache/media/private-media/email, six fictional actors, no inherited credentials. Browser and server block external transport. [Isolation](isolation.json), [stand inventory](stands-final.json), [exact commands](COMMANDS.md).

## 1. Состояние области

Only module13 was audited in this launch. Modules01–12 were read as historical checklists, not adopted as current PASS. [Fresh intersections by original module/role/snapshot](module-coverage.csv), [fresh matrix JSON](matrix.json), [scenario/role/language/width CSV](matrix.csv), [counts](counts.json), [MASTER_AUDIT](MASTER_AUDIT.md).

{table}
The transitions above were native form/button/confirmation actions. Initial synthetic actors, taxonomy and one ready Place were seeded before testing; seed data is not publication/transition proof. Candidate/live, saved records and reload were compared with native pages and read-only fake DB snapshots. [Final fake state](final-state.json), [section data preservation](data-preservation.json). Program text becomes a detached local snapshot (`program_id=null`); groups and20/80 tariffs remain.

Fresh combined browser assertions: **{counts.get('PASS',0)} PASS /{counts.get('FAIL',0)} FAIL /{counts.get('NOT RUN',0)} NOT RUN**, including root native assertions **{dict(fc)}** and delegated **{browser['counts']}**. These are observations, not unique accepted features; attempts/subtests/historical reports are not added. Two browser FAIL rows are SIMULATED unsaved placeholder visibility rechecks. Native delegated270 pages cover public10/owner3/admin2 surfaces, each role all18 RU/AZ/EN×360/390/768/1024/1280/1440. Native settings216 direct pages add both OFF and ON states. Root transition locales are usually RU; unprefixed admin effective language was not recorded in every root action, so full admin locale proof is only the explicit-route delegated matrix.

## 2. Сильные стороны

Creation/reload/logout continuation, explicit moderation, candidate/live isolation, stale two-tab409 input preservation, recipient confirmation, branch detach and private-document permission boundaries passed their fresh scenarios. Separate place opening hours and class schedule survived nested editing. Photos/gallery survive reload and public approval; fictional invalid file is visibly rejected. Native favorite double click leaves one persisted favorite. Canonical old slug records one logical place_view delta. Displayed fallback text is not counted as a saved translation.

Navigation error summary passes on a fresh draft ([summary](navigation-final.result.txt)); focused age field is fully visible and unobstructed after2200ms native smooth-scroll completion at390 and1440 ([settled navigation](navigation-settled.result.txt)). Actual draft-url transport abort retains input, preserves server copy, reload restores local input, retry recovers ([network](network-corrected.result.txt)). Loading delay is explicitly SIMULATED. Misconfigured intercepts, premature focus timing, wrong404 literal/200 redirect assertions and cancelled-removal assumptions were excluded with fresh corrections; raw attempts retained ([exclusions](matrix.json)).

Rendered browser checks include mobile drawers, open selectors/details, Tab/Shift+Tab/Escape and sampled focus, loaded images, overflow and local console/network. Long195-character text stress uses explicitly SIMULATED DOM text; persisted long descriptions are real. No additional layout/runtime failure confirmed in that delegated set. [Browser report](browser-review/REPORT.md), [contact sheets](browser-review/contacts.json), [all screenshot manifest](screenshots-manifest.json), [root visual review](visual-review.json).

## 3. Реальные проблемы

**10 freshly confirmed IDs /9 causes**:7 retained IDs and3 new CROSS IDs. [Individual findings and copyable repair prompts](FINDINGS.md). SITE-QA-01 P1 allows permissionless staff to alter global logo; ANALYTICS-QA-01 exposes global stats to the same staff. ORG-QA-02/ACCESS-QA-03 are one missing grant-management UI. SOCIAL-QA-01 loses selected saved rating in four review editors. ANALYTICS-QA-03 rejects native same-origin phone tracking with a port. PLACE-QA-06 remains a current compiled-catalog mismatch despite a historical isolated-builder repair claim.

New **CROSS-QA-01 P2**: a future rescheduled physical event remains public/listed but disappears from its organization due to the scheduled-only projection. New **CROSS-QA-02 P2**: configured no-label CI command discovers618 of2070 tracked HEAD tests, omitting1452; WORKTREE2090 adds20 foreign untracked tests, so its omitted1472 is not the GitHub corpus. `full -> catalog` wrapper additionally omits140 non-prefixed module cases. Actual GitHub execution NOT RUN. New **CROSS-QA-03 P3**: RU empty district text falls back to AZ; RU PO entry is obsolete, so compiling alone does not restore an active translation.

New audit IDs are not evidence of newly introduced regressions. Native clean-HEAD replay for each UI finding was not executed. Exact test baseline controls established11 original assertion failures reproduce on HEAD with frozen runtime MO; no new application regression is inferred from those tests. Nine pass with separately compiled HEAD GNU gettext;2 baseline contract/label failures remain. This control did not change current runtime assets or close UI defects.

## 4. Tech debt

Default discovery bridge and shell wrapper define different full suites. Forty-one legacy tests depend on historical settings/DB/socket/guard identity; the new stand cannot run their bodies without falsifying those preconditions. Compiled gettext needs explicit provenance/selection; source gaps and compiled gaps require separate repairs. Historical81 IDs are summarized by cause with prior evidence retained; old findings outside the fresh slice stay NOT RUN, not freshly open or closed.

Graph-first discovery used C-kidsmap; ready index had partial coverage and later metadata_changed/coverage_unavailable on critical dynamic paths. Direct routes/source/ORM relationships were verified. A graph result does not establish runtime coverage or deadness. [Source audit](source-review/REPORT.md), [inventory](source-review/inventory.json), [coverage limitations](source-review/graph-coverage.json).

## 5. Risks

The current suite is not green and mandatory native/device/integration gaps remain. Permissionless media writing is demonstrated only in this isolated fake stand; production exploitability was not assessed. Generated locale failures are actual current stand failures, not app-code regressions proven by this run. Actual private-doc HTTP403/404 boundaries and readonly aggregates do not establish all production policies. Stand/version/foreign changes must be re-attested before any later work.

## 6. Dead/legacy candidates

No deletion candidate is established. Operational ConversionRun/Mapping/healthz and legacy migration/recovery surfaces need separate coverage. No source/graph absence, empty fake DB or test-discovery omission justifies removal. Existing code, rules, migrations and assertions were preserved.

## 7. Tests gaps

Fresh Django **2036 PASS /11 FAIL /43 NOT RUN**,2090 unique methods; raw full **exit1**,1570.313s:2034 PASS,20 direct FAIL,28 ERROR,62 failed subtest observations over8 methods. Two exact UTF8 reruns PASS/exit0; frozen HEAD11 FAIL/exit1; isolated GNU HEAD9 PASS+2 FAIL/exit1. Remaining unavailable43 comprise41 guarded bodies+1 POSIX path+1 Windows streaming-file cleanup ERROR, separated in [test classifications](test-review/results.json). No guards or assertions weakened.

Existing JS20 scripts exit0:115 named tests+2 bare-file wrappers (117 entries). Standalone Python Windows13 PASS/3 bash ENV ERROR; same3 backup bodies later PASS in WSL synthetic/mocked fixture, copied LF normalization only. Initial CRLF false-boundary proof excluded. [Test report/counts/commands](test-review/REPORT.md), [counts](test-review/counts.json).

Native employee revoke NOT RUN due to missing control; detach effectiveness PASS is separate.72 delegated NOT RUN rows:18 external-map SDK and54 complete save/error/conflict cells across owner forms; root RU cases do not fill every other locale/width. Other explicit gaps:3 stock Playwright fixture scripts, actual GitHub/Google OAuth/GA/Maps/SMTP/IndexNow, native phones/tablets/Safari/Firefox, screen reader and full keyboard cycles, every control/state at18cells, production/indexing/recovery/migration guarded historical bodies. Full partial-failure connection batch with multiple conflicting rows was not repeated natively in this final slice; positive canonical batch and stale Program conflict are separate proof. [Mandatory historical gaps](reconciliation/mandatory-gaps.csv) remain checklist only.

## 8. Recommendations

{repair_order}

No implementation was performed or authorized by this audit. [Next-chat decision text](next-chat.txt) asks for a concrete scoped repair plan first. Existing copied prompts are independent, linked to fresh evidence and preserve original IDs.

## 9. P0/P1/P2/P3

Fresh P0=0; P1=1ID (SITE-QA-01); P2=8IDs/7 causes; P3=1ID (CROSS-QA-03). Historical priorities are preserved separately in MASTER_AUDIT; no production release conclusion. [Artifact/source/foreign preservation verification](verification.json) exit0 is an evidence-integrity result, not application PASS. Only journal row13 was updated after final verification; all13 audit rows are completed, while product acceptance remains FAIL with NOT RUN limits.
'''
(P/'REPORT.md').write_text(report,encoding='utf-8')
next_chat=f'''Продолжаем KidsMap. Аудиты модулей01–13 завершены; финальная приёмка13 имеет FAIL и явные NOT RUN ограничения. Работай в корне checkout (здесь C:/kidsmap; определи путь заново). Прочитай AGENTS.md, канонические .agents, docs/qa/module-acceptance-prompts.md, docs/qa/module13-2026-10-11-r1/REPORT.md, MASTER_AUDIT.md и FINDINGS.md в том же run.

Сначала зафиксируй новый HEAD/branch/dirty WORKTREE/active_run и версию стенда; не наследуй локальные PID/ports/volumes как доступные на другом ПК. Предыдущий snapshot HEAD {snap['head']}, branch {snap['branch']}, source digest {snap['source_digest']}, active_run NONE. Сохрани чужие изменения/стенды/документы. Без commit/push/deploy/production.

Подготовь конкретный план устранения подтверждённых проблем с файлами, приоритетами, зависимостями и meaningful проверками. Начни с SITE-QA-01 P1, затем authorization/discovery/generated locales; ORG-QA-02 и ACCESS-QA-03 имеют одну причину. Новые IDs CROSS-QA-01/02/03. Старые отчёты — чек-лист, не свежая проверка. 10 свежих IDs /9 причин; весь исторический список отдельно в MASTER_AUDIT. Полный backend был2036 PASS/11 FAIL/43 NOT RUN; assertions/guards не ослаблять.

Приложение пока не меняй: сначала представь план на согласование scope. После согласования — только выбранная область, собственный DJANGO_TESTING=1 стенд с отдельными DB/cache/media/private-media/email и вымышленными данными, blocked external integrations. Никаких production credentials. Дай свежий отчёт/команды/counts/exit codes/native UI save-reload/screenshots и явные NOT RUN.
'''
(P/'next-chat.txt').write_text(next_chat,encoding='utf-8')
commands='''# Exact execution commands and outcome locations

Run from C:/kidsmap in PowerShell. Commands below refer only to this run; do not reuse another PC's PID/session/volume. Credentials are created in ignored own scratch and never included in artifact commands.

```powershell
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/prepare.py
wsl.exe -- docker run -d --name kidsmap-module13-20261011-r1 -p 127.0.0.1:55444:5432 -e POSTGRES_USER=module13 -e POSTGRES_DB=module13 -e POSTGRES_HOST_AUTH_METHOD=trust postgres:17-alpine
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/run.py snapshot
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/run.py migrate
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/seed.py
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/run.py serve-public-safe
& 'C:/Program Files/nodejs/node.exe' 'C:/Users/Ramin/AppData/Local/npm-cache/_npx/31e32ef8478fbf80/node_modules/@playwright/cli/playwright-cli.js' -s=module13-r1 open http://localhost:8831/qa/version/ --config .tmp/module13-20261011-r1/playwright.json
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/read-state.py final-state.json
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/build-report.py
.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/verify-final.py
```

[Root native UI per-command UTC/command/CLI exit/duration/results](command-ledger.jsonl). Every listed native script was invoked as `.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/drive.py SCRIPT.js`; fixture/credential substitution occurs only in memory. CLI exit0 does not imply all scenario assertions PASS. Retried raw attempts are preserved. The root ledger contains actual executed exact commands; initialization snippet above documents the stand construction, not a command to replay against an occupied port.

[Browser exact commands](browser-review/REPORT.md), [browser ledger](browser-review/command-ledger.jsonl), [full backend/JS/standalone exact commands and raw exits](test-review/REPORT.md), [JS20 command arrays](test-review/js-results.json), [Django runner at launch](test-review/full-runner-at-launch.py). Native and test isolation profiles differ intentionally and are documented; no production transport occurs.
'''
(P/'COMMANDS.md').write_text(commands,encoding='utf-8')
print('Fresh browser observations',dict(counts),'root',dict(fc),'fresh findings10/9 causes','historical81 unchanged')
