import csv,hashlib,json,re,struct,subprocess,urllib.request
from datetime import datetime,timezone
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site08-pc-plan-r1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
write=lambda n,d:(O/n).write_text(json.dumps(d,ensure_ascii=False,indent=2))
assert not (O/'artifact-manifest.json').exists()
entry=read(O/'source-entry.json');assert len(entry['sources'])==1032 and all(sha(R/p)==h for p,h in entry['sources'].items())
priorfiles=0
for pkg,files in entry['prior_packages'].items():
 for p,h in files.items():assert sha(R/'docs/qa'/pkg/p)==h,(pkg,p);priorfiles+=1
assert len(entry['prior_packages'])==33 and priorfiles==6536
assert all(sha(R/p)==h for p,h in entry['shared_mo'].items()) and sha(R/'.cbmignore')==entry['cbmignore']
git=lambda *a:subprocess.check_output(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a],text=True).strip()
assert git('rev-parse','HEAD')==entry['git']['head'] and git('branch','--show-current')==entry['git']['branch'] and git('rev-parse','task33-progress')==entry['git']['task33_ref']
assert not git('diff','--cached','--name-only') and sha(R/'.git/index')==entry['git']['index_sha256']
assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
old={x.split()[1]:(x.split()[0],x.split()[2]) for x in entry['containers']};now={x.split()[1]:(x.split()[0],x.split()[2]) for x in subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines()};assert all(now.get(k)==v for k,v in old.items())
setup=read(O/'evidence/setup.json');assert subprocess.check_output(['docker','inspect','--format','{{.Id}}',setup['app']],text=True).strip()==setup['container_id']
cand=read(O/'candidate-manifest.json');assert len(cand['files'])==2 and cand['not_applied']
for p,d in cand['files'].items():
 assert sha(O/'candidate'/p)==d['candidate_sha256']
 if d['new']:assert not (R/p).exists()
 else:assert sha(R/p)==d['before_sha256']
assert sha(O/'proposed.diff')==cand['diff_sha256']
patch=subprocess.run(['git','-C',str(R),'apply','--check',str(O/'proposed.diff')],capture_output=True,text=True);assert patch.returncode==0,patch.stderr
diff=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True);assert diff.returncode==0,diff.stderr
js=subprocess.run(['node','--check',str(O/'browser-acceptance.js')],capture_output=True,text=True);assert js.returncode==0,js.stderr
acceptance=(O/'browser-acceptance.js').read_text();assert 'addStyleTag' not in acceptance and 'classList.add' not in acceptance and '__CANDIDATE_CSS__' not in acceptance
datasets={};summary={}
for n in ['browser-discovery','browser-prototype-pilot','browser-prototype-pilot2','browser-prototype','browser-readonly-prototype','browser-prototype-final','browser-readonly-prototype-final']:
 d=read(O/'evidence'/f'{n}.json');assert not d.get('pageerrors') and not d.get('local_errors') and not d.get('error')
 datasets[n]=d;values=[v for r in d['rows'] for v in r['checks'].values()];s={'rows':len(d['rows']),'controls_pass':sum(v is True for v in values),'controls_fail':sum(v is False for v in values)}
 if 'baseline' in d['rows'][0]:
  for phase in ['baseline','prototype','rollback']:
   values=[v for r in d['rows'] for v in r[phase]['checks'].values()];s[phase]={'pass':sum(v is True for v in values),'fail':sum(v is False for v in values)}
 summary[n]=s
superdata=datasets['browser-prototype-final'];viewer=datasets['browser-readonly-prototype-final'];assert len(superdata['rows'])==162 and len(viewer['rows'])==18
from itertools import product
models=['sitebrandingsettings','siteaboutsettings','sitecontactssettings','sitefootersettings','siteemptystatesettings','sitevisibilitysettings','siteanalytics','catalogcontentsettings','sitegalleryimage']
assert {(r['model'],r['lang'],r['width']) for r in superdata['rows']}==set(product(models,['az','ru','en'],[360,390,768,1024,1280,1440]))
for n,checks,controls in [('browser-prototype-final',810,486),('browser-readonly-prototype-final',90,54)]:
 s=summary[n];assert s['prototype']=={'pass':checks,'fail':0} and s['controls_pass']==controls and s['controls_fail']==0
 assert s['baseline']==s['rollback'] and datasets[n]['no_fixture_write']
assert summary['browser-prototype-final']['baseline']['fail']>0
static=read(O/'evidence/static-runtime.json');compiled=read(O/'evidence/candidate-static.json')
assert static['sources_verified']==1032 and static['template_compiled'] and static['testing'] and static['current3root_locales_verified'] and static['external_integrations_disabled'] and {r['model'] for r in static['consumers']}==set(models)
assert compiled['candidate_compile'] and len(compiled['branches'])==18 and compiled['candidate_not_applied']
with urllib.request.urlopen('http://127.0.0.1:33570/qa/site08/all-state/',timeout=10) as response:fixture=json.load(response)
assert fixture==datasets['browser-discovery']['before']==superdata['before']==viewer['after'] and fixture['admin_log_count']==0
write('fixture-final.json',fixture)
png={}
for p in sorted((O/'png').glob('*.png')):
 b=p.read_bytes();assert b[:8]==b'\x89PNG\r\n\x1a\n';w,h=struct.unpack('>II',b[16:24]);png[p.relative_to(O).as_posix()]={'sha256':sha(p),'width':w,'height':h}
assert len(png)==136;write('png-manifest.json',png)
with (O/'matrix.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['suite','id','model','lang','width','phase','check','pass'])
 for n,d in datasets.items():
  for r in d['rows']:
   for phase in ['baseline','prototype','rollback','control']:
    checks=r['checks'] if phase=='control' else r.get(phase,{}).get('checks',{})
    for k,v in checks.items():w.writerow([n,r['id'],r.get('model'),r.get('lang'),r.get('width'),phase,k,v])
visual=read(O/'visual-review.json');assert visual['inspection_completed'] and all((O/'png'/p).exists() for p in visual['inspected'])
write('graph-evidence.json',{'project':'C-kidsmap','index_status':'ready','generation':'2026-10-16T18:56:53Z','nodes':51523,'edges':280457,'freshness':'stale metadata_changed for template/site.py/models/site.py/shell CSS; new proposed CSS absent by design','coverage':'template/base/site.py/models coverage_unavailable; shell CSS partial recorded3074/3106','search':'BM25 shared settings discovery20matches first8, narrowed SiteBrandingSettingsAdmin/_BaseSiteSettingsSectionAdmin2matches has_morefalse','trace':'inbound CALLS0 for base class not treated as absence of inheritance/consumers','source_verification':'Actual current admin registry9consumers, template/static origins and1032hash guard; literal CSS/source review. No reindex/cache mutation.'})
write('source-final.json',{'sources':entry['sources'],'application_changes':0,'unchanged':1032,'git':entry['git']})
result={'utc':datetime.now(timezone.utc).isoformat(),'status':'SITE-QA-08/P2 CONFIRMED OPEN; exact2file PLAN READY / APPROVAL PENDING','mode':'PLAN','application_changes':0,'source_count':1032,'candidate_files':2,'candidate_applied':False,'actual_source_GREEN':'NOT RUN','native':{'final_super_cells':162,'final_readonly_cells':18,'prototype_geometry_pass':900,'prototype_geometry_fail':0,'controls_pass':540,'controls_fail':0,'rollback_verified':180,'sets':summary,'pageerrors':0,'unexpected_local_http_errors':0,'console_diagnostics':len(superdata.get('console_errors',[]))+len(viewer.get('console_errors',[])),'blocked_external_requests':len(superdata['blocked'])+len(viewer['blocked']),'png':136},'static':{'candidate_compile':True,'permission_model_branches':18,'active_consumers':9,'current3root_locales_verified':True,'git_apply_check_exit':patch.returncode,'native_git_diff_check_exit':diff.returncode,'prepared_future_no_injection_JS_syntax_exit':js.returncode},'preservation':{'all1032_sources':True,'prior_packages':33,'prior_files':priorfiles,'shared_MO':True,'cbmignore':True,'refs_index_bytes_empty_staging':True,'active_run_NONE':True,'foreign_container_identities_states':len(old),'synthetic_settings_hash_adminlog_unchanged':True},'git':entry['git'],'module10':'14canonical OPEN (10P2/4P3); SITE08 remains OPEN; full acceptance pending','closed_local_retained':['SITE01','SITE15','SITE06','SITE19','SITE21','module09 composite'],'separate_open_limits':['SITE20','SITE11'],'execution':'inline, no independent-agent claim','not_run':['actual-source GREEN','backend105 regression rerun','native saves/uploads/invalidPOST/retry','public consumer readback','full accessibility','production/global/module11'],'harness_limits':['v1 file/Select2 prototype failures retained','v2 full matrix17analytics overflow failures retained; diagnostic proved boolean helper flex:none width1095.66; final stronger checks include help blocks','first candidate full inherited render missing request context; complete compile +root fragment branch harness passed; no app/assertion weakening']}
write('verification.json',result)
baseline=summary['browser-prototype-final']['baseline'];readonly=summary['browser-readonly-prototype-final']['baseline']
report=f'''# SITE-QA-08: свежая проверка и конкретный план — 2026-10-18

**SITE08/P2 CONFIRMED OPEN; exact2file PLAN READY / approval pending. Приложение не изменено.** Модуль10 остаётся14OPEN (10P2/4P3), full acceptance pending. [План](IMPLEMENTATION_PLAN.md), [точный diff](proposed.diff), [кандидат/SHA](candidate-manifest.json), [проверки](verification.json).

Lead frontend-admin, сверка kidsmap-orchestrator выполнены /root inline по canonical definitions; независимого исполнения специалистами не было. Scope: заполненные общие settings forms, их responsive bounds и доступность штатных mobile actions у editable. LOCAL HEAD `{entry['git']['head']}`, branch `{entry['git']['branch']}`, исходная точка — dirty WORKTREE. Production UNKNOWN/не контактировали.

## Что подтверждено

На новом source-guarded стенде33570, текущих3root locale и синтетической fixture RU360 branding document.scrollWidth=1097 при viewport360; input600px, file widget1029.9px. Существующий shell grid/fieldset сохраняет auto minimum. Файловая clear-checkbox попадает под boolean `:has(input[type=checkbox])` rules (`flex:none !important`, `max-width:none !important`); Select2 имеет intrinsic/inline ширину322px и min-width200px. У boolean help блока аналитики это же правило даёт1095.66px. В root остальных shared consumers отсутствует Bootstrap col-12; активный base оборачивает его в flex.row. На≤760 shell скрывает action card, а общей форме не добавляет alternative mobile buttons. Исторические26 FAIL не выдаются за текущий счёт.

Source: shared_settings_change_form.html:6–8/15/86–119/125–139; kidsmap_admin_form_shell.css:634–646/936–1000/3112–3195; actual registry в evidence/static-runtime.json содержит9потребителей. Graph C-kidsmap ready, generation2026-10-16, metadata_changed/coverage_unavailable и partial CSS; использован как подсказка, критические связи проверены source/runtime, graph CALLS0 не интерпретирован как отсутствие потребителей.

## Предлагаемое изменение

Ровно2application files: общий шаблон получает собственный CSS link, marker и col-12; новый `static/admin/css/pages/kidsmap_settings_forms.css` ограничивает intrinsic/grid/file/Select2/boolean-helper размеры и переносы. Штатные mobile buttons показываются только через marker от Django has_change_permission. Общая shell CSS, Place/Event templates, JS, backend, права, модели, schema, PO и revision/save semantics остаются прежними. SITE21 column для каталога сохраняется. Readonly mobile hidden state сохранён; SITE20 desktop readonly buttons и SITE11 copy остаются отдельными OPEN.

## Выполненные проверки

Native Chromium/Playwright CLI,9active forms ×AZ/RU/EN ×360/390/768/1024/1280/1440 =162editable cases, плюс18readonly catalogue. После actual-source baseline временно добавлялись ровно marker/col-12 и CSS кандидата; затем полный rollback с точным повторным сравнением геометрии. **Это DOM-прототип, не applied-source GREEN.**

| Набор | Результат |
| --- | --- |
| Final editable baseline,5геометрических checks/cell | {baseline['pass']} PASS /{baseline['fail']} FAIL из810 |
| Final temporary editable prototype | 810/810 PASS |
| Final readonly baseline | {readonly['pass']} PASS /{readonly['fail']} FAIL из90 |
| Final readonly prototype | 90/90 PASS; mobile actions остаются скрытыми |
| HTTP/language/точный rollback controls | 540/540 PASS |
| Rollback geometry | 180/180 совпадений с baseline |
| Static candidate compile /permission-model roots | 18/18 PASS,9actual consumers |

В final suites нет pageerrors/неожиданных local HTTP4xx. Внешние fonts.googleapis.com блокированы; diagnostic ERR_FAILED сохранены, console-clean не заявляется. Состояние SiteSettings/CatalogContentSettings подтверждено одинаковым hash; admin_log_count0. Auth/setlang работали только на синтетических локальных sessions. 136PNG включают discovery, неудачные прототипы и final. [Визуальный review](visual-review.json), [команды](commands.md), matrix.csv, png-manifest.json.

Первый прототип не устранил file flex:none/Select2; diagnostics и candidate сохранены в prototype-v1. Второй прошёл8pilot cells, но полная162cell матрица оставила17analytics overflow checks; prototype-v2-full и native results сохранены. По диагностике добавлены shrink/caps для boolean help, final assertions усилены проверкой visible help blocks. App fixes не применялись, FAIL не скрывались/не ослаблялись. Первый static inherited render требовал missing request context Jazzmin; harness исправлен на full compile +точный root fragment и не выдаётся за runtime render.

## Целостность, риски и следующий шаг

Все1032source files unchanged, кандидат только внутри QA-пакета;33previous sealed packages/6536files, shared MO/.cbmignore/refs/index/empty staging/active_run NONE и foreign container identities/states сохранены. Guide/MASTER append-only. Нет commit/push/deploy/production. Действуют retained SITE01/15/06/19/21 и module09 composite LOCAL closures.

Собственная normal/test DB/cache/media/private-media/email, env clear до setup, read-only repo bind, текущие3locale в own path, внешние integration выключены. Browser prototype не проверяет реальную загрузку нового static asset, native save/upload/error/retry/public values или backend regressions: всё это **NOT RUN** сейчас и включено в точный future acceptance в плане. Full accessibility/global/module11 также NOT RUN. Самостоятельного разрешения на иные fixes этот отчёт не даёт.

Следующий шаг: одобрить конкретный proposed.diff/2files, затем fresh own source RED→exactapply→actual-source GREEN, native mobile saves/errors/files/Select2/ACL и105backend regression methods. AGENTS.md требует «Future implementation requires a concrete plan and user approval for its scope». Текущее «дальше» продолжает recheck/PLAN; прошлое одобрение SITE21 не распространяется на этот scope.
'''
(O/'REPORT.md').write_text(report)
print('All PLAN checks passed; appending documentation and sealing.',flush=True)
note='''\n\n## SITE-QA-08 PLAN READY — 2026-10-18 pc-r1

**SITE08/P2 CONFIRMED OPEN; exact2file PLAN READY / approval pending.** [REPORT]({prefix}{name}/REPORT.md), [PLAN]({prefix}{name}/IMPLEMENTATION_PLAN.md), [diff]({prefix}{name}/proposed.diff), [verification]({prefix}{name}/verification.json). App0changes/source1032unchanged/candidate NOTAPPLIED/actual-sourceGREEN NOTRUN. Fresh33570 synthetic/current3locale: mobile360 branding doc1097; inherited fieldset/grid auto minimum, file clear-checkbox boolean flex:none/maxnone, Select2 intrinsic sizing, boolean helper1095.66px and hidden mobile actions proven by source/native diagnostics. Proposed only sharedtemplate root/link/permission marker +new scoped settings CSS, not global Place/Event shell. Final162editable+18readonly cases:900prototypegeometry PASS +540HTTP/language/rollback controlsPASS,180exactrollbacks,136PNG; full candidate compile18permission/model roots/9runtime consumers. Temporary DOM classes/styles only; not applied-sourceGREEN/save proof. Original v1 and v2 failures retained, diagnostics-driven final stronger help bounds. Readonly mobile state retained; SITE20/SITE11 remain separate.33priorpackages/6536files/MO/.cbmignore/refs-index/activeNONE/foreign runtimes preserved; guide/MASTER append-only. **Module10 still14OPEN (10P2/4P3), full acceptance pending**; SITE01/15/06/19/21 and module09 LOCAL closures retained. Next explicit approval of exact2files then fresh own RED→apply→no-injectionGREEN/mobile saves/errors/files/Select2/ACL/public/105backend regressions. No commit/push/deploy/production/global/module11; inline execution, no independent-review claim.
'''
docs={}
for rel,h in entry['documents'].items():
 p=R/rel;before=p.read_bytes();assert sha(p)==h and before==(Q/'documents'/rel).read_bytes();prefix='../qa/' if rel.endswith('MASTER_AUDIT.md') else ''
 p.write_bytes(before+note.format(prefix=prefix,name=O.name).encode());assert p.read_bytes().startswith(before)
 docs[rel]={'original_bytes':len(before),'original_sha256':h,'append_only':True,'final_sha256':sha(p)}
write('document-preservation.json',docs)
post=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True);assert post.returncode==0 and sha(R/'.git/index')==entry['git']['index_sha256'] and all(sha(R/p)==h for p,h in entry['sources'].items())
write('evidence/final-checks.json',{'git_apply_check_exit':patch.returncode,'native_git_diff_check_exit':diff.returncode,'prepared_JS_syntax_exit':js.returncode,'post_append_diff_check_exit':post.returncode,'all_source_hashes_unchanged':1032,'index_bytes_retained':True,'line_ending_advisories':'Known LF/CRLF warnings; no whitespace errors or normalization'})
for n in ['bootstrap.py','prepare_probe.py']:
 if (Q/n).exists():(O/n).write_bytes((Q/n).read_bytes())
(O/'prepare_entry.py').write_bytes((R/'.tmp/prepare_site08_plan.py').read_bytes())
manifest={p.relative_to(O).as_posix():sha(p) for p in O.rglob('*') if p.is_file() and p.name!='artifact-manifest.json'};write('artifact-manifest.json',manifest);assert all(sha(O/p)==h for p,h in manifest.items())
print(json.dumps({'status':result['status'],'sources_unchanged':1032,'prior_packages':33,'prior_files':priorfiles,'prototype_geometry_pass':900,'controls_pass':540,'png':136,'sealed_entries':len(manifest),'module10':result['module10']},indent=2))
