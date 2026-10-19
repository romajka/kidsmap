import csv,hashlib,json,re,struct,subprocess,urllib.request
from datetime import datetime,timezone
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site22-pc-fix-r1';P=O.parent/'site-qa22-recheck-2026-10-18-pc-r1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();write=lambda n,d:(O/n).write_text(json.dumps(d,ensure_ascii=False,indent=2))
assert not (O/'artifact-manifest.json').exists();entry=read(O/'source-entry.json');sources=read(O/'source-applied.json')['sources'];applied=read(O/'applied.json');candidate=read(O/'approved-candidate-manifest.json')
assert len(sources)==1034 and all(sha(R/p)==h for p,h in sources.items()) and applied['application_refinements']==0 and applied['other_existing_sources_unchanged']==1031
for p,d in candidate['files'].items():assert sha(R/p)==d['candidate_sha256']
assert sha(O/'implemented.diff')==sha(P/'proposed.diff')==candidate['diff_sha256']=='e60661fd4053bc76c501282f788a72351c8ea0d9f1f54ee7439343c260143e97'
red=read(O/'evidence/red-backend.json');assert red['exit']==1 and red['failure_observations']==20 and not red['errors']
backend=read(O/'evidence/green-backend.json');assert backend['exit']==0 and not backend['failures'] and not backend['errors'] and len(backend['test_ids'])==len(set(backend['test_ids']))==114 and 'Ran 114 tests in 33.601s' in backend['summary'] and 'OK' in backend['summary']
isolation=read(O/'evidence/green-test-isolation.json');assert isolation['testing'] and isolation['test_DB']=='test_m10s22_fix_green_r1' and isolation['own_separate_test_cache'] and isolation['normal_fixture_storage_not_used']
names=['browser-focused-green','browser-saves-az','browser-saves-ru','browser-saves-en','browser-readonly-green','browser-sentinels-green','browser-json-error-snapshots','browser-file-error-central','browser-stale-email','browser-access','browser-neighbor-destinations','browser-console'];data={n:read(O/'evidence'/(n+'.json')) for n in names};counts={}
for n,d in data.items():
 assert not d.get('error') and not d.get('pageerrors') and not d.get('local_errors'),(n,d.get('error'),d.get('pageerrors'),d.get('local_errors'))
 values=[v for row in d['rows'] for v in row['checks'].values()];assert values and all(type(v)is bool for v in values) and all(values),(n,[(r['id'],k) for r in d['rows'] for k,v in r['checks'].items() if not v]);counts[n]={'rows':len(d['rows']),'checks':len(values),'pass':values.count(True),'fail':values.count(False)}
 text=(O/(n+'.js')).read_text();assert 'addStyleTag' not in text and not re.search(r'\b(?:route|r)\s*\.\s*fetch\s*\(',text) and 'classList.add' not in text
expected={'browser-focused-green':(6,78),'browser-saves-az':(86,1362),'browser-saves-ru':(86,1362),'browser-saves-en':(86,1362),'browser-readonly-green':(18,126),'browser-sentinels-green':(12,72),'browser-json-error-snapshots':(18,126),'browser-file-error-central':(12,72),'browser-stale-email':(24,150),'browser-access':(30,129),'browser-neighbor-destinations':(39,225),'browser-console':(18,54)}
for n,(rows,checks) in expected.items():assert counts[n]=={'rows':rows,'checks':checks,'pass':checks,'fail':0},(n,counts[n])
for n in ['browser-readonly-green','browser-sentinels-green','browser-console']:assert data[n]['no_fixture_write']
focused_red=read(O/'evidence/browser-focused-red.json');fv=[v for r in focused_red['rows'] for v in r['checks'].values()];assert (len(fv),fv.count(True),fv.count(False))==(78,72,6)
assert {k for r in focused_red['rows'] for k,v in r['checks'].items() if not v}=={'correct_target','correct_target_marker','direct_one_redirect'}
sentred=read(O/'evidence/browser-sentinels-red.json');assert sentred['no_fixture_write'] and all(all(r['checks'].values()) for r in sentred['rows'])
recovery=read(O/'evidence/browser-restore-null.json');assert all(all(r['checks'].values()) for r in recovery['rows']) and recovery['failed_run_log_delta']==85 and recovery['after']['values']['public_favorites_minimum'] is None
failed=read(O/'initial-restore-failure/evidence/acceptance-commands.json');assert len(failed)==1 and failed[0]['exit']!=0 and 'Cannot type text into input[type=number]' in (O/'initial-restore-failure/evidence/browser-saves-az-cli.txt').read_text()
assert read(O/'evidence/QA-null-restore-correction.json')['preserved_failed_PNG']==80
main=[r for lang in ['az','ru','en'] for r in data['browser-saves-'+lang]['rows'] if 'button' in r];assert len(main)==240 and sum(r['length']=='long' for r in main)==24
assert len([r for r in main if r['length']=='short'])==216 and len([r for r in main if r['button']=='_save'])==120
assert all(len(r['redirect_chain'])==2 and r['redirect_chain'][1]['path']==('/admin/catalog/sitesettings/' if r['button']=='_save' else '/admin/catalog/'+r['model']+'/1/change/') for r in main)
commands=read(O/'evidence/acceptance-commands.json');assert len(commands)==10 and all(c['exit']==0 for c in commands)
static=read(O/'evidence/static-runtime.json');assert static['source_count']==1034 and len(static['branches'])==18 and static['actual_template_compiled'] and static['hub_template_compiled'] and static['CSS_HTTP_status']==static['hub_CSS_HTTP_status']==200 and static['CSS_HTTP_sha256']==sha(R/'static/admin/css/pages/kidsmap_settings_forms.css') and static['hub_CSS_HTTP_sha256']==sha(R/'static/admin/css/pages/kidsmap_site_settings.css') and static['current3root_locales_verified'] and static['integrations_disabled']
def get(path):
 with urllib.request.urlopen('http://127.0.0.1:33610/'+path,timeout=10) as response:return json.load(response)
site=get('qa/site08/form-state/');sections=get('qa/site22/values/');catalog=get('qa/site08/state/');initial_sections=focused_red['initial'];initial_site=data['browser-stale-email']['initial'];initial_catalog=read(O/'fixture-entry.json')
normalization=read(O/'evidence/text-normalization.json');assert normalization['source_outside_exact_response_hook_byte_identical_to_prepatch'] and all(d['actual_matches_form_cleaned_seed'] and d['strip'] for d in normalization['about_fields'].values())
expected_sections=dict(initial_sections['values']);expected_sections['about_text_ru']=normalization['about_fields']['about_text_ru']['cleaned_seed'];assert sections['values']==expected_sections
assert all(site[k]==initial_site[k] for k in ['brand_name','footer_email','logo','logo_size','gallery'])
cache=read(O/'evidence/derivative-cache.json');assert cache['original_paths_hashes_unchanged'] and cache['manifest_verified'] and all(site['media'].get(k)==h for k,h in initial_site['media'].items()) and set(site['media'])-set(initial_site['media'])==set(cache['new_cache_files'])
assert all(catalog[k]==initial_catalog[k] for k in ['districts_json','metro_stations_json','seo_pages_json'])
good_expected=sum(data[n].get('expected_successful_native_posts',0) for n in names);expected_logs=focused_red['expected_successful_native_posts']+85+recovery['expected_successful_native_posts']+good_expected
assert good_expected==327 and expected_logs==419 and site['admin_log_count']==sections['admin_log_count']==catalog['admin_log_count']==expected_logs
write('fixture-final.json',{'site':site,'sections':sections,'catalog':catalog,'scoped_values_restored_via_native_form_validation':True,'about_text_normalization':'Existing CharField(strip=True) removes one trailing blank in all3language ORM-seeded about texts; actual DB equals form-cleaned seed. Evidence text-normalization.json; no raw trailing-space restoration claimed.','original_media_names_bytes_and_gallery_display_values_unchanged':True,'generated_responsive_cache_files':cache['new_cache_files'],'expected_native_successful_logs':419,'accounting':{'source_RED_focused':6,'interrupted_first_AZ_run_log_delta_only_not_counted_as_PASS':85,'explicit_nullable_recovery':1,'successful_acceptance_native_posts':327},'metadata':'Normal update timestamps, own synthetic LogEntries and5validated generated responsive-image cache files intentionally retained; no byte-identical DB/media inventory restoration claim.'})
preserve=subprocess.run(['python3',str(O/'preserve.py')],capture_output=True,text=True);(Q/'final-preservation.log').write_text(preserve.stdout+preserve.stderr);assert preserve.returncode==0,preserve.stderr[-600:]
png={}
for p in sorted((O/'png').glob('*.png')):
 b=p.read_bytes();assert b[:8]==b'\x89PNG\r\n\x1a\n';w,h=struct.unpack('>II',b[16:24]);png[p.relative_to(O).as_posix()]={'sha256':sha(p),'width':w,'height':h}
assert len(png)==442,len(png);write('png-manifest.json',png);visual=read(O/'visual-review.json');assert visual['inspection_completed'] and all((O/'png'/p).exists() for p in visual['inspected'])
with (O/'matrix.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['suite','id','model','role','lang','width','button','check','pass'])
 for n,d in {**data,'browser-focused-red':focused_red,'browser-sentinels-red':sentred,'nullable-recovery':recovery}.items():
  for r in d['rows']:
   for k,v in r['checks'].items():w.writerow([n,r['id'],r.get('model'),r.get('role'),r.get('lang'),r.get('width'),r.get('button'),k,v])
for n in ['qa_settings.py','runtime.py','qa_urls.py','seed.py','proxy.py','playwright.json','test_site19_candidate.py']:(O/n).write_bytes((Q/n).read_bytes())
for name,path in [('prepare_native.py','.tmp/prepare_site22_native_scripts.py'),('prepare_support.py','.tmp/prepare_site22_fix_support.py'),('repair_native_restore.py','.tmp/repair_site22_native_restore.py'),('extend_neighbor_asset_probe.py','.tmp/extend_site22_neighbor_asset_probe.py')]:(O/name).write_bytes((R/path).read_bytes())
write('graph-evidence.json',{'project':'C-kidsmap','generation':'2026-10-16T18:56:53Z','nodes':51523,'edges':280457,'status':'ready but stale','coverage':'site.py/hubCSS metadata_changed/coverage_unavailable; new test missing at entry','actual_source_verified':'Exact approved3file candidate; original6consumers from source and fresh runtime registry;18template branches/CSSHTTP/allsource1034 verified','index_cache_or_ignore_mutations':False})
total=sum(v['checks'] for v in counts.values());assert total==5118 and sum(v['rows'] for v in counts.values())==435
result={'utc':datetime.now(timezone.utc).isoformat(),'status':'SITE22/P3 CLOSED LOCAL; exact3file patch applied; backend/native acceptance PASS','application_files':applied['approved_files'],'application_refinements':0,'source_count':1034,'other_existing_sources_unchanged':1031,'backend':{'methods':114,'seconds':33.601,'exit':0,'failures':0,'errors':0,'RED_methods':9,'RED_failed_methods':3,'RED_failure_observations':20},'native':{'rows':435,'acceptance_checks':5118,'pass':5118,'fail':0,'main_save_states':240,'regular_states':216,'long_states':24,'languages':['az','ru','en'],'widths':[360,390,768,1024,1280,1440],'main_direct_hub_exits':120,'both_save_actions':True,'suites':counts,'focused_RED':{'pass':72,'expected_fail':6},'nullable_fixture_recovery':{'pass':4,'failed_main_run_not_counted':True},'pageerrors_recorded':0,'unexpected_local_HTTP_errors_recorded':0,'console_scope':'18read-only hub/footer/visibility cells; blocked externalfont errors retained; no whole-matrix console-clean claim','PNG':442,'no_transport_or_style_simulation':True},'preservation':read(O/'evidence/preservation.json'),'git':entry['git'],'fixture':'Scoped sixsection scalars/JSON/gallery display values restored natively;media filenames+bytes unchanged;419expected synthetic logs/update timestamps retained','module10':'13OPEN (9P2/4P3); full module acceptance pending','retained_LOCAL_closures':['SITE01','SITE15','SITE06','SITE19','SITE21','SITE08','module09 composite'],'separate_OPEN':['SITE20 readonly desktop actions','SITE11 localization','remaining canonical module10 findings'],'production':'UNKNOWN; not contacted','NOT_RUN':['full module10/global/module11 acceptance','production/release/deploy','full WCAG/cross-browser/physical devices','controlled public JSON dependency'],'execution':'/root inline; no independent-agent claim'}
write('verification.json',result);write('source-final.json',{'sources':sources,'application_files':applied['approved_files'],'application_refinements':0,'other_existing_sources_unchanged':1031,'git':entry['git']})
report='''# SITE-QA-22 — применено и проверено локально, 2026-10-18

**SITE22/P3 CLOSED LOCAL.** «Сохранить и выйти» из шести разделов ведёт прямо к существующим «Настройкам сайта» за один redirect; «Сохранить и продолжить» остаётся в редакторе. На hub длинное уведомление корректно переносится. Module10 теперь **13OPEN(9P2/4P3)**; полная приёмка модуля остаётся pending. Production UNKNOWN/не контактировали.

[Authorization](authorization.json): user «применяем» одобрил exactthree-file plan/diff. Execution /root inline, canonical Django/admin UI scope, no independent-agent claim. LOCAL HEAD852938d96764ae315b92859e3651e5ea62054a36, branch codex/module09-transfer-2026-10-16-r1, dirty WORKTREE сохранён. [План](IMPLEMENTATION_PLAN.md) и approved-candidate-manifest — исторические approved input с NOTAPPLIED; текущие [applied](applied.json), [diff](implemented.diff), [verification](verification.json) подтверждают применение.

## Применено

Ровно src/catalog/domain_admin/site.py: base.response_post_save_change→existing settings hub; static/admin/css/pages/kidsmap_site_settings.css: hub-only normal message flow/overflow-wrap:anywhere; новый src/catalog/testcases/test_site_qa22_save_exit.py с meaningful integration regressions. Exact diff SHAe60661fd4053bc76c501282f788a72351c8ea0d9f1f54ee7439343c260143e97. Application refinements0,1034sources:2existing changed/1new test/1031others unchanged. Model/schema/ACL/revisions/PO/global shell и SITE08 formCSS074e3405 не менялись. Analytics/catalogue/gallery остаются со своими destinations.

## Свежие результаты

| Проверка | Факт |
| --- | --- |
| Backend RED против исходного кода |9methods,3failed/6PASS,20expectedfailure observations/0errors,4.502s |
| Actual-source backend GREEN |114unique methods,33.601s,OK,exit0 |
| Same native focused RED→GREEN |78checks:72PASS/6expectedFAIL →78/78PASS |
| Sixsection native saves,3langs×6widths×both actions |216states +24long states,4086checks incl18native scalar restores,PASS |
| Readonly mobile/desktop baseline |126PASS,known desktopSITE20 retained |
| Place/Event marker/formCSS/hubCSS absence +exact geometry parity |72PASS |
| Invalid mobile JSON/draft/focus |126PASS |
| Invalid files/visible linked summary/native anchor focus/no-write |72PASS |
| Native invalid-email/stale valid-file409/oldtoken/draft/reselection |150PASS |
| Proxy-only editor/viewer/denied/missing-CSRF |129PASS; existing ACL retained |
| Native analytics/catalogue/gallery own destinations |225PASS |
| Console/bootstrap3langs×2widths×hub/footer/visibility |54PASS; externalfont errors explicitly classified |

**5118/5118actual-source native acceptance checks,435rows PASS.**240main save states: `_save`120times directPOST302→hubGET200, `_continue`120times directPOST302→same editorGET200. Exact persistence/1LogEntry, target marker/lang, reloaded field/fresh signed revision, no overflow, visible/wrapped message/link/close, keyboardTab/Enter close. Extra role/neighbour/stale writes recorded separately. Both CSSHTTP200/exactSHA;18permission/model template roots and hub compiled/current3root locales/source1034guard. No transport response rewrite, route.fetch or style injection in acceptance. Read-only console coverage is18cells, not every save; expected blocked externalfonts/ERR_FAILED retained, no console-clean claim. Expected403/409 are distinguished from unexpectedlocalHTTP; recorded pageerrors0.

## QA failure retained

Первый AZ80state run завершился только при восстановлении nullable minimum: test helper отправлял String(null) в number input. Structured matrix не вернулась, **PASS этого прерванного прогона не заявляется**. Original script/CLI/commands и80PNG сохранены (`initial-restore-failure`, failed-v1 PNG). Source допускаетnull/blank; исправлено только представление empty widget, destination/DB equality assertions не ослаблялись. Own nullable value восстановлен nativePOST302/1log,4controlsPASS; полныйAZ набор повторён и дал1362/1362PASS. RU/EN тоже1362/1362PASS. Ни одного дополнительного application diff.

## Изоляция и сохранность

Fresh own33610 /m10s22-fix-r1-app, normal m10s22_fix_r1, REDtest_m10s22_fix_r1 и отдельный freshGREENtest_m10s22_fix_green_r1. Envclear/DJANGO_TESTING=1/isolated normal-test cache/media/private-media/email/currentlocales/integrationsdisabled/ROrepo. Backend test data не используют normal fixture storage. Перезапущен только свой source-loaded server после проверки fullcontainerID/cmdline; все чужие стенды сохранены.

Изначальные6section scalar values,3JSON иgallery display values восстановлены native saves; logo/media filenames+bytes неизменны.419expected synthetic LogEntries:6REDfocused +85logdelta interruptedAZ +1nullable recovery +327successful acceptancePOST. Timestamps и журналы оставлены на own stand; byte-identical DB rollback не заявляется. Public SSR brand/footer exact readback прошёл; public JSON consumer dependency не предмет scope.

Уточнение восстановления: ORM seed содержал один конечный пробел в about_text_ru/az/en. Native About form использует существующий CharField(strip=True), поэтому эти3текста восстановлены к form-cleaned seed. [Read-only normalization proof](evidence/text-normalization.json) подтверждает актуальную форму/все3значения и byte-identical form code вне нового response hook. Это вывод о ранее существовавшей нормализации по неизменённому source, не наблюдение prepatch native About. Первоначальный final guard сравнивал с raw ORM seed; квалифицирован только этот доказанный trailing-blank случай, остальные values/media/route assertions сохранены. Raw trailing-whitespace restoration не заявляется.

Оригинальные10media files сохранили имена/байты. Native gallery caption save штатно вызвал существующий post_save prepare_responsive_photos→generate_variants и создал4WebP derivatives+manifest в собственном responsive-images cache. [Read-only cache audit](evidence/derivative-cache.json) сопоставил весь добавленный набор с source image, размерами и manifest. Эти5служебных файлов оставлены в own QA media; отсутствие новых cache files не заявляется. Исходники signals/responsive_images входят в1031unchanged; первоначальный inventory-equality guard ошибочно считал cache additions изменением оригиналов. Проверки исходных байтов, отсутствия удалений, gallery values и остальных полей сохранены.

38priorpackages/7576files/sharedMO/.cbmignore/refs/index bytes/empty staging/activeNONE/73foreigncontaineridentities-state проверены.442PNG incl80failed, [matrix](matrix.csv), [visual-review](visual-review.json), exact commands/exits/IDs/manifests сохранены. Guide/MASTER append-only. SITE01/15/06/19/21/08 иmodule09 LOCAL closures retained; SITE20/SITE11 иостальные canonical findings OPEN. Полный module10/global/production/cross-browser/a11y/physical device acceptance NOTRUN. Без commit/push/deploy/production/нового module11/чужого cleanup.
'''
(O/'REPORT.md').write_text(report)
note='''\n\n## SITE-QA-22 CLOSED LOCAL — 2026-10-18 pc-r1

**Approved exact3file SITE22 diff APPLIED; SITE22/P3 CLOSED LOCAL.** [REPORT]({prefix}{name}/REPORT.md), [verification]({prefix}{name}/verification.json), [exact diff]({prefix}{name}/implemented.diff). Sixsubsection normalSave→existinghub onehop;continue/editor/errors200/stale409/ACL/revisions preserved;hub-onlymessage wrapping +newbehavior test. Apprefinements0/source1034/2existingchanged+1newtest/1031others unchanged. Freshbackend9RED3failed/20observations→114uniqueGREEN33.601sOK; no assertions weakened. Nativefocused78checks72PASS6expectedFAIL→78PASS. Fresh435rows5118/5118acceptancePASS:216regular+24long6section save states,3langs/6widths/bothbuttons; directsavehub120times,continue120times;keyboardclose/data1log/reload/revision/public scalarreadback. Readonly126/neighborPlaceEvent72/JSONerror126/centralfileerror72/staleemail150/ACL129/otherdest225/console54PASS. FirstAZnullable String(null) restore failure retained80PNG/CLI; properempty widgethelper +native recovery4PASS, fullAZ/RU/EN1362eachPASS;failedpartialmatrixNOTCOUNTED.442PNG. Scopedscalars/JSON/gallery display values restored/media bytes unchanged;419expected synthetic logs/timestamps retained.38priorpackages/7576files/MO/.cbmignore/refs-index/activeNONE/73foreignruntimes preserved;docsappendonly. **Module10 now13OPEN(9P2/4P3), fullacceptancepending**. SITE01/15/06/19/21/08/module09 closures retained; SITE20/SITE11/othercanonicalOPEN retained. No commit/push/deploy/production/global/module11;inline/no independent-agent claim.\n'''
docs={}
for rel,h in entry['documents'].items():
 p=R/rel;before=p.read_bytes();assert sha(p)==h and before==(Q/'documents'/rel).read_bytes();p.write_bytes(before+note.format(prefix='../qa/' if rel.endswith('MASTER_AUDIT.md') else '',name=O.name).encode());assert p.read_bytes().startswith(before);docs[rel]={'original_bytes':len(before),'original_sha256':h,'append_only':True,'final_sha256':sha(p)}
write('document-preservation.json',docs)
post=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True);assert post.returncode==0 and sha(R/'.git/index')==entry['git']['index_sha256'] and all(sha(R/p)==h for p,h in sources.items());write('evidence/final-checks.json',{'post_append_native_git_diff_check_exit':0,'source1034hashes_match':True,'index_bytes_unchanged':True,'candidate_exactly_applied':True,'other_existing_sources_unchanged':1031})
manifest={p.relative_to(O).as_posix():sha(p) for p in O.rglob('*') if p.is_file() and p.name!='artifact-manifest.json'};write('artifact-manifest.json',manifest);assert all(sha(O/p)==h for p,h in manifest.items());print(json.dumps({'status':result['status'],'backend':result['backend'],'native_acceptance_PASS':total,'PNG':len(png),'sealed_entries':len(manifest),'module10':result['module10']},indent=2))
