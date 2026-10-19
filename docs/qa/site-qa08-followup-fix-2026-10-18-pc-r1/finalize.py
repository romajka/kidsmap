import csv,hashlib,json,re,struct,subprocess,urllib.request
from datetime import datetime,timezone
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site08-pc-followup-r1';F=O.parent/'site-qa08-fix-2026-10-18-pc-r1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();write=lambda n,d:(O/n).write_text(json.dumps(d,ensure_ascii=False,indent=2))
assert not (O/'artifact-manifest.json').exists()
entry=read(O/'source-entry.json');sources=read(O/'source-applied.json')['sources'];candidate=read(O/'candidate-manifest.json');applied=read(O/'applied.json')
assert len(sources)==1033 and all(sha(R/p)==h for p,h in sources.items()) and applied['other_existing_sources_unchanged']==1032
assert sha(O/'implemented.diff')==sha(F/'followup/proposed.diff')==candidate['diff_sha256']
for p,d in candidate['files'].items():assert entry['sources'][p]==d['before_sha256'] and sha(R/p)==d['candidate_sha256']
assert (O/'browser-message-red.js').read_bytes().replace(b'red-alert-',b'green-alert-')==(O/'browser-message-green.js').read_bytes()
names=['browser-message-green','browser-acceptance-green','browser-readonly-green','browser-sentinels-green','browser-json-error-snapshots','browser-file-error-central','browser-permissions','browser-saved-message-az','browser-saved-message-ru','browser-saved-message-en']
data={n:read(O/'evidence'/(n+'.json')) for n in names};counts={}
for n,d in data.items():
 assert not d.get('error') and not d.get('pageerrors') and not d.get('local_errors'),n
 values=[v for row in d['rows'] for v in row['checks'].values()];assert values and all(type(v)is bool for v in values) and all(values),(n,[(r['id'],k) for r in d['rows'] for k,v in r['checks'].items() if not v]);counts[n]={'rows':len(d['rows']),'checks':len(values),'pass':values.count(True),'fail':values.count(False)}
 assert 'addStyleTag' not in (O/(n+'.js')).read_text() and 'classList.add' not in (O/(n+'.js')).read_text()
expected={'browser-message-green':(5,11),'browser-acceptance-green':(162,1134),'browser-readonly-green':(18,126),'browser-sentinels-green':(12,60),'browser-json-error-snapshots':(18,126),'browser-file-error-central':(12,72),'browser-permissions':(2,7),'browser-saved-message-az':(50,630),'browser-saved-message-ru':(50,630),'browser-saved-message-en':(50,630)}
for n,(rows,checks) in expected.items():assert counts[n]=={'rows':rows,'checks':checks,'pass':checks,'fail':0},(n,counts[n])
for n in ['browser-acceptance-green','browser-readonly-green','browser-sentinels-green']:assert data[n]['no_fixture_write']
red=read(O/'evidence/browser-message-red.json');green=data['browser-message-green'];assert red['rows'][2]['geometry']['document']==366 and green['rows'][2]['geometry']['document']==360
assert sum(v is False for r in red['rows'] for v in r['checks'].values())==1
assert red['rows'][2]['geometry']['alert_display']=='flex' and green['rows'][2]['geometry']['alert_display']=='block'
redsent=read(O/'evidence/browser-sentinels-red.json');assert redsent['no_fixture_write'] and all(all(r['checks'].values()) for r in redsent['rows'])
saved=[r for lang in ['az','ru','en'] for r in data['browser-saved-message-'+lang]['rows'] if 'button' in r];assert len(saved)==144
known_exit=[r for r in saved if r['button']=='_save'];assert len(known_exit)==72
for r in saved:
 chain=r['redirect_chain'];assert [s['status'] for s in chain]==([302,302,200] if r['button']=='_save' else [302,200]);assert chain[-1]['path']==chain[0]['path']
write('evidence/SITE22-observed-navigation.json',{'status':'OPEN/P3; separate backend scope','cases':72,'all_observed_POST302_changelist302_same_editor200':True,'rows':[{'id':r['id'],'chain':r['redirect_chain']} for r in known_exit],'exit_behavior_fixed_or_accepted':False})
commands=read(O/'evidence/acceptance-commands.json');assert len(commands)==9 and all(x['exit']==0 for x in commands)
browser_commands=[json.loads(s) for s in (O/'evidence/browser-commands.jsonl').read_text().splitlines()];assert all(x['exit']==0 for x in browser_commands)
static=read(O/'evidence/static-runtime.json');assert static['source_count']==1033 and len(static['branches'])==18 and static['actual_template_compiled'] and static['CSS_HTTP_status']==200 and static['CSS_HTTP_sha256']==sha(R/'static/admin/css/pages/kidsmap_settings_forms.css') and static['integrations_disabled'] and static['current3root_locales_verified']
def get(path):
 with urllib.request.urlopen('http://127.0.0.1:33590/qa/site08/'+path+'/',timeout=10) as response:return json.load(response)
catalog=get('state');site=get('form-state');initial=red['initial'];original_catalog=read(O/'fixture-entry.json')
assert all(catalog[k]==original_catalog[k] for k in ['districts_json','metro_stations_json','seo_pages_json'])
assert all(site[k]==initial[k] for k in ['brand_name','footer_email','logo','logo_size','media','gallery'])
assert site['admin_log_count']==catalog['admin_log_count']==158 and initial['admin_log_count']==0
write('fixture-final.json',{'catalog':catalog,'site':site,'native_restoration_verified':True,'media_filenames_bytes_and_gallery_exactly_unchanged':True,'expected_native_LogEntries':158,'accounting':{'red_setup_restore':4,'green_same_test_setup_restore':4,'responsive_saved_cases':144,'three_language_native_restores':6}})
# Historical105 backend tests are retained evidence, not a fresh execution of this CSS run.
backend=read(F/'evidence/green-backend.json');assert backend['exit']==0 and 'Ran 105 tests in 33.566s' in backend['summary'] and 'OK' in backend['summary']
assert all(h==sources[p] for p,h in entry['sources'].items() if p.endswith('.py'))
write('evidence/backend-historical.json',{'execution':'NOT RUN in this CSS-only followup','prior_package':F.name,'tests':105,'seconds':33.566,'exit':0,'prior_evidence_sha256':sha(F/'evidence/green-backend.json'),'Python_source_unchanged_vs_entry':True,'fresh_validation':'Native browser forms/save/validation/static-template probes; normal/test isolation retained'})
preserve=subprocess.run(['python3',str(O/'preserve.py')],capture_output=True,text=True);(Q/'final-preservation.log').write_text(preserve.stdout+preserve.stderr);assert preserve.returncode==0,preserve.stderr[-700:]
for n in ['qa_settings.py','runtime.py','qa_urls.py','seed.py','proxy.py','playwright.json','test_site19_candidate.py']:(O/n).write_bytes((Q/n).read_bytes())
(O/'prepare_entry.py').write_bytes((R/'.tmp/prepare_site08_followup.py').read_bytes());(O/'prepare_suites.py').write_bytes((R/'.tmp/prepare_site08_followup_suites.py').read_bytes())
png={}
for p in sorted((O/'png').glob('*.png')):
 b=p.read_bytes();assert b[:8]==b'\x89PNG\r\n\x1a\n';w,h=struct.unpack('>II',b[16:24]);png[p.relative_to(O).as_posix()]={'sha256':sha(p),'width':w,'height':h}
assert len(png)==224,len(png);write('png-manifest.json',png)
visual=read(O/'visual-review.json');assert visual['inspection_completed'] and all((O/'png'/p).exists() for p in visual['inspected'])
with (O/'matrix.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['suite','id','model','lang','width','button','check','pass'])
 for n,d in {**data,'browser-message-red':red,'browser-sentinels-red':redsent}.items():
  for r in d['rows']:
   for k,v in r['checks'].items():w.writerow([n,r['id'],r.get('model'),r.get('lang'),r.get('width'),r.get('button'),k,v])
write('graph-evidence.json',{'project':'C-kidsmap','generation':'2026-10-16T18:56:53Z','nodes':51523,'edges':280457,'status':'ready but stale','coverage':'CSS not_tracked and base template metadata_changed; coverage_unavailable','source_fallback':'Exact approved plan; read current CSS and base message source before mutation;1033source hashes/runtime compile18branches9forms/CSS HTTP verified','index_cache_or_ignore_mutations':False})
total=sum(c['checks'] for c in counts.values());assert total==3426
result={'utc':datetime.now(timezone.utc).isoformat(),'status':'SITE-QA-08 CLOSED LOCAL; exact one-CSS followup applied and responsive acceptance PASS','application_files':applied['approved_files'],'application_refinements':0,'source_count':1033,'other_source_files_unchanged':1032,'native':{'rows':sum(c['rows'] for c in counts.values()),'checks':total,'pass':total,'fail':0,'saved_message_cases':144,'languages':['az','ru','en'],'widths':[360,390,768,1024,1280,1440],'both_native_save_actions':True,'keyboard_close_checked':144,'public_scalar_readbacks':144,'SITE22_known_exit_chains_recorded_open':72,'suites':counts,'actual_source_RED':{'checks':11,'pass':10,'expected_geometry_fail':1,'document':366},'same_actual_source_GREEN_document':360,'pageerrors_recorded':0,'unexpected_local_HTTP_errors_recorded':0,'monitoring_scope':'All instrumented suites; negative permission probe records expected status/no-write without pageerror listener','negative_permissions_HTTP':'expected403 explicitly checked','external_fonts':'nonloopback blocked; ERR_FAILED classified; no console-clean claim','PNG':len(png)},'backend':'Historical105/33.566s/OK; NOT rerun in this CSS-only package','fixture_restoration':'Native original scalars restored;JSON/media filenames+bytes/gallery unchanged;158expected synthetic logs retained','preservation':read(O/'evidence/preservation.json'),'git':entry['git'],'module10':'14canonical OPEN (9P2/5P3); full module acceptance pending','separate_OPEN':['SITE22/P3 save-and-exit navigation','SITE20 readonly desktop actions','SITE11 copy','other canonical OPEN findings'],'retained_LOCAL_closures':['SITE01','SITE15','SITE06','SITE19','SITE21','module09 composite'],'production':'UNKNOWN; not contacted','NOT_RUN':['SITE22 repair','full WCAG/accessibility audit','controlled public JSON dependency','full module10 acceptance','global/module11/production'],'execution':'/root inline; no independent-agent claim'}
write('verification.json',result);write('source-final.json',{'sources':sources,'application_files':applied['approved_files'],'application_refinements':0,'other_existing_sources_unchanged':1032,'git':entry['git']})
report=f'''# SITE-QA-08 — CSS followup применён и проверен, 2026-10-18

**SITE08 CLOSED LOCAL.** Согласованное дополнение в одном CSS применено без расширения scope. Уведомление после сохранения больше не расширяет мобильную страницу: native actual-source RU360 **366→360px**, тот же тест11checks:10PASS/1expectedFAIL до →11PASS после. Production UNKNOWN/не контактировали. Module10: **14OPEN (9P2/5P3)**, полная приёмка модуля остаётся pending.

User «дальше» прямо продолжает вопрос о применении конкретного followup: [authorization](authorization.json). [IMPLEMENTATION_PLAN](IMPLEMENTATION_PLAN.md) и candidate-manifest — точные исторические копии на момент одобрения, содержащие прежний NOTAPPLIED; текущее применение подтверждают [applied](applied.json), [verification](verification.json), [implemented.diff](implemented.diff). Execution /root inline, canonical frontend-admin/orchestrator scope; independent specialist review NOT RUN.

## Изменение

Только static/admin/css/pages/kidsmap_settings_forms.css: scoped `body:has(.km-settings-form-page) #content > .alert` получает normal block flow, min-width0/max-width100% и overflow-wrap:anywhere. Переносится текст со ссылкой на объект; overflow не скрывается. SHA baf70032e5b918a783c136b4fa9449855c6eafb18df13f015a7ff144c7367f83 →074e3405a541bc9c0ce6eaefea013388d48e810d2d9a48eb3a4bb7c940d7474c. Exact diff SHA da5563bc9a2e2d75f6cdf8ffa2b7c1992c440ff2ccbc0d5a2eb8678cd77dde99. Остальные1032source files сохранены; template e3791aa31eba0d31ecd14ce559cfca8745185b9ba3950dcc4aa92d224e5cbe29. До/после проверялись сохранённые source bytes, без DOM/style injection.

## Свежая проверка

| Native suite | Cases | PASS |
| --- | ---: | ---: |
| Identical saved-message RU360 RED→GREEN | 5 | 11 |
| 9forms ×3languages ×6widths | 162 | 1134 |
| Readonly catalogue/mobile hidden Save | 18 | 126 |
| Place/Event no marker/CSS +exact geometry parity | 12 | 60 |
| Invalid JSON/draft/focus/viewport | 18 | 126 |
| Invalid file/visible linked summary/native anchor focus/no-write | 12 | 72 |
| ViewerPOST403/deniedGET403/no writes | 2 | 7 |
| Saved messages/short+unbroken long/both buttons +restores | 150 | 1890 |

**3426/3426checks PASS,379rows** в новом actual-source acceptance. Отдельные RED/baseline59checks:58PASS/1ожидаемый geometryFAIL; не включены в GREEN total.144native saved states: AZ/RU/EN,360/390/768/1024/1280/1440, branding/footer, short/long, `_continue`/`_save`. Exact scalar persistence и1LogEntry на операцию, видимые message/link/close, viewport bounds, отсутствие перекрытия формы, keyboard Tab/Enter dismissal и public SSR readback. Лого и галерея в этом followup не изменялись; их paths/bytes/rows сохранены.224PNG, [матрица](matrix.csv), [визуальный обзор](visual-review.json), команды/exit и scripts сохранены. В наборах с мониторингом pageerror/неожиданных localHTTP нет; permission probe проверяет expected403/no-write без pageerror listener. Внешние ресурсы блокировались, font ERR_FAILED диагностирован; console-clean не заявляется.

18permission/model branches actual template compiled;9consumers, current3root locales, CSS_HTTP200 с exactcandidateSHA и1033source guard. Backend105tests/33.566s/OK из родительского пакета — **исторический baseline, не новый запуск**. Python source unchanged; новый CSS не требовал повторения backend suite. Проверены native POST/validation/render states. Все проверки на отдельном стенде33590, DJANGO_TESTING=1, env очищен перед setup, отдельные normal/test DB/cache/media/private-media/email/locales, integrations disabled.158ожидаемых synthetic LogEntries; исходные scalar значения восстановлены native save, JSON иmedia filenames/bytes/gallery exactunchanged. No positive API business POST.

## Отдельные незакрытые пункты

**SITE22/P3 остаётся OPEN:**72native `_save` цепочки POST302→changelist302→same editor200 записаны отдельно; correct persistence не означает correct exit. CSS не меняет этот backend. SITE20/SITE11 и прочие canonical findings также OPEN. Public district filters DB-derived; controlled JSON→public dependency UNVERIFIED, не предмет этого исправления. Полный accessibility/global/module10 acceptance/модуль11 не заявляются.

## Сохранность

HEAD {entry['git']['head']}, branch {entry['git']['branch']}, dirty WORKTREE сохранён.35prior packages/7127files, sharedMO/.cbmignore/refs/index bytes/empty staging/active_runNONE и71foreign runtime IDs/states проверены. Перезапущен только собственный новый source-loaded server после проверки containerID иcmdline. CRLF сохранён; nativeGitdiff--check иreverseexactpatchcheck exit0. Guide/MASTER append-only; SITE01/15/06/19/21 иmodule09 LOCAL closures retained. Без commit/push/deploy/production/cleanup чужих стендов. [Полная проверка](verification.json), [preservation](evidence/preservation.json).
'''
(O/'REPORT.md').write_text(report)
note='''\n\n## SITE-QA-08 CLOSED LOCAL — 2026-10-18 followup pc-r1

**Approved exact one-CSS followup APPLIED; SITE08 CLOSED LOCAL.** [REPORT]({prefix}{name}/REPORT.md), [verification]({prefix}{name}/verification.json), [exact diff]({prefix}{name}/implemented.diff). Native actual-source RU360366→360px, identical11checks10PASS/1expectedFAIL→11PASS; no injection. Fresh actual-source acceptance3426/3426PASS/379rows:9form layout1134, readonly126, Place/Event exact parity60, JSONerror126, central file-error/native focus72, permission7, focused11,144responsive saved-message states+6native restores1890.3langs/6widths/short+long/bothbuttons, keyboardclose/public scalar readback.224PNG;18runtime permission/model branches/currentlocales/CSSHTTP200/exactcandidate074e3405/source1033verified,1032others unchanged. Prior105backend33.566sOK historical NOT rerun for this CSS-only followup.158expected native synthetic logs;originalscalars restored,JSON/media bytes/gallery unchanged. SITE22/P3 remainsOPEN:72known Saveexit302→302→sameeditor200; not a CSS regression or claimed exit repair. SITE20/SITE11 and other canonical OPEN retained. **Module10 now14OPEN (9P2/5P3), full acceptance pending.** SITE01/15/06/19/21/module09LOCAL closures retained.35priorpackages/7127files/MO/.cbmignore/refs-index/activeNONE/71foreignruntimes preserved;docsappendonly. No commit/push/deploy/production/global/module11;inline/no independent-agent claim. Next implementation requires its own concrete plan/authorized scope; no automatic SITE22 change.
'''
docs={}
for rel,h in entry['documents'].items():
 p=R/rel;before=p.read_bytes();assert sha(p)==h and before==(Q/'documents'/rel).read_bytes();prefix='../qa/' if rel.endswith('MASTER_AUDIT.md') else '';p.write_bytes(before+note.format(prefix=prefix,name=O.name).encode());assert p.read_bytes().startswith(before);docs[rel]={'original_bytes':len(before),'original_sha256':h,'append_only':True,'final_sha256':sha(p)}
write('document-preservation.json',docs)
diff=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True);assert diff.returncode==0 and sha(R/'.git/index')==entry['git']['index_sha256'] and all(sha(R/p)==h for p,h in sources.items())
write('evidence/final-checks.json',{'post_append_native_git_diff_check_exit':0,'source_hashes_match':1033,'index_bytes_unchanged':True,'exact_candidate_applied':True,'followup_not_applied_flag_in_copied_manifest_is_historical_approved_input':True})
manifest={p.relative_to(O).as_posix():sha(p) for p in O.rglob('*') if p.is_file() and p.name!='artifact-manifest.json'};write('artifact-manifest.json',manifest);assert all(sha(O/p)==h for p,h in manifest.items());print(json.dumps({'status':result['status'],'native_PASS':total,'PNG':len(png),'sealed_entries':len(manifest),'module10':result['module10']},indent=2))
