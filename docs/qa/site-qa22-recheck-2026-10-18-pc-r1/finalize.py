import ast,csv,hashlib,json,re,struct,subprocess,urllib.request
from datetime import datetime,timezone
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site22-pc-plan-r1';F=O.parent/'site-qa08-followup-fix-2026-10-18-pc-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();read=lambda p:json.loads(p.read_text());write=lambda n,d:(O/n).write_text(json.dumps(d,ensure_ascii=False,indent=2))
assert not (O/'artifact-manifest.json').exists();entry=read(O/'source-entry.json');assert len(entry['sources'])==1033 and all(sha(R/p)==h for p,h in entry['sources'].items())
candidate=read(O/'candidate-manifest.json');assert len(candidate['files'])==3 and candidate['not_applied'] and sha(O/'proposed.diff')==candidate['diff_sha256']
for p,d in candidate['files'].items():
 assert sha(O/'candidate'/p)==d['candidate_sha256']
 if d['before_sha256']:assert sha(R/p)==d['before_sha256']
 else:assert not (R/p).exists()
 assert (p.endswith('.css') or ast.parse((O/'candidate'/p).read_text()))
assert (O/'candidate/src/catalog/testcases/test_site_qa22_save_exit.py').read_bytes()==(O/'test_site22_candidate.py').read_bytes()==(Q/'test_site22_candidate.py').read_bytes()
red=read(O/'evidence/red-backend.json');assert red['exit']==1 and red['failure_observations']==20 and not red['errors'] and len({f.split(' ')[0] for f in red['failures']})==3 and 'Ran 9 tests in 5.836s' in red['summary']
v1=read(O/'evidence/browser-destination-prototype.json');v2=read(O/'evidence/browser-destination-prototype-v2.json');counts={}
for n,d in [('prototype-v1',v1),('prototype-v2',v2)]:
 assert not d['pageerrors'] and not d['local_errors'];values=[v for r in d['rows'] for v in r['checks'].values()];counts[n]={'rows':len(d['rows']),'checks':len(values),'pass':values.count(True),'fail':values.count(False)}
assert counts=={'prototype-v1':{'rows':14,'checks':162,'pass':150,'fail':12},'prototype-v2':{'rows':14,'checks':162,'pass':162,'fail':0}}
assert not v1['transport_rewrites'] and all(k=='actual_hub_render' for r in v1['rows'] for k,v in r['checks'].items() if not v)
assert len(v2['transport_rewrites'])==13 and v2['initial']['admin_log_count']==26 and v2['final']['admin_log_count']==52
long_mobile=[r for r in v2['rows'] if r.get('width')==360 and r.get('length')=='long'];assert len(long_mobile)==3
assert {r['lang']:r['baseline']['document'] for r in long_mobile}=={'az':1039,'ru':1020,'en':1028}
assert all(r['prototype']['document']==360 and r['rollback']==r['baseline'] for r in long_mobile)
contract=read(O/'evidence/runtime-contract.json');assert contract['actual_consumers']==['siteaboutsettings','sitebrandingsettings','sitecontactssettings','siteemptystatesettings','sitefootersettings','sitevisibilitysettings'] and contract['integrations_disabled'] and contract['current3locales']
isolation=read(Q/'test-isolation.json');assert isolation['testing'] and isolation['test_DB']=='test_m10s22_plan_r1' and isolation['own_separate_test_cache'] and isolation['normal_fixture_storage_not_used'];write('evidence/test-isolation.json',isolation)
priorfiles=0
for pkg,files in entry['prior_packages'].items():
 for p,h in files.items():assert sha(R/'docs/qa'/pkg/p)==h,(pkg,p);priorfiles+=1
assert len(entry['prior_packages'])==36 and priorfiles==7436
assert all(sha(R/p)==h for p,h in entry['shared_mo'].items()) and sha(R/'.cbmignore')==entry['cbmignore']
git=lambda *a:subprocess.check_output(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a],text=True).strip()
assert git('rev-parse','HEAD')==entry['git']['head'] and git('branch','--show-current')==entry['git']['branch'] and git('rev-parse','task33-progress')==entry['git']['task33_ref'] and not git('diff','--cached','--name-only') and sha(R/'.git/index')==entry['git']['index_sha256']
assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
old={s.split()[1]:(s.split()[0],s.split()[2]) for s in entry['containers']};now={s.split()[1]:(s.split()[0],s.split()[2]) for s in subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines()};assert all(now.get(k)==v for k,v in old.items())
setup=read(O/'evidence/setup.json');assert subprocess.check_output(['docker','inspect',setup['app'],'--format','{{.Id}}'],text=True).strip()==setup['container_id']
check=subprocess.run(['git','-C',str(R),'apply','--check',str(O/'proposed.diff')],capture_output=True,text=True);assert check.returncode==0,check.stderr
diff=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True);assert diff.returncode==0,diff.stderr
with urllib.request.urlopen('http://127.0.0.1:33600/qa/site08/form-state/',timeout=10) as response:site=json.load(response)
with urllib.request.urlopen('http://127.0.0.1:33600/qa/site08/state/',timeout=10) as response:catalog=json.load(response)
initial=v1['initial'];assert site['admin_log_count']==catalog['admin_log_count']==52
assert all(site[k]==initial[k] for k in ['brand_name','footer_email','logo','logo_size','media','gallery'])
catalog_initial=read(O/'fixture-entry.json');assert all(catalog[k]==catalog_initial[k] for k in ['districts_json','metro_stations_json','seo_pages_json'])
write('fixture-final.json',{'site':site,'catalog':catalog,'native_and_forwarded_restores':True,'media_bytes_filenames_gallery_JSON_unchanged':True,'expected_logs':52,'accounting':'Two diagnostic runs26successfulPOST each; v2 has13native branding and13forwarded footer including restores. TestDB transactions separate.'})
for n in ['qa_settings.py','runtime.py','qa_urls.py','seed.py','proxy.py','playwright.json','test_site19_candidate.py']:(O/n).write_bytes((Q/n).read_bytes())
(O/'prepare_destination_v2.py').write_bytes((R/'.tmp/prepare_site22_destination_v2.py').read_bytes());(O/'preserve_red_v1.py').write_bytes((R/'.tmp/preserve_site22_red_v1.py').read_bytes())
png={}
for p in sorted((O/'png').glob('*.png')):
 b=p.read_bytes();assert b[:8]==b'\x89PNG\r\n\x1a\n';w,h=struct.unpack('>II',b[16:24]);png[p.relative_to(O).as_posix()]={'sha256':sha(p),'width':w,'height':h}
assert len(png)==72;write('png-manifest.json',png);assert read(O/'visual-review.json')['inspection_completed']
with (O/'matrix.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['suite','id','lang','width','length','check','pass'])
 for n,d in [('prototype-v1',v1),('prototype-v2',v2)]:
  for r in d['rows']:
   for k,v in r['checks'].items():w.writerow([n,r['id'],r.get('lang'),r.get('width'),r.get('length'),k,v])
write('graph-evidence.json',{'project':'C-kidsmap','generation':'2026-10-16T18:56:53Z','nodes':51523,'edges':280457,'status':'ready but stale','coverage':'site.py/models/site.py/hub template/hub CSS metadata_changed, coverage_unavailable; new tests not_tracked','trace':'INHERITS inbound six consumers, untruncated; verified against source and runtime actual admin registry','source_fallback':True,'index_cache_mutations':False})
result={'utc':datetime.now(timezone.utc).isoformat(),'status':'SITE22/P3 OPEN; exact3file PLAN READY; APPROVAL PENDING','application_changes':0,'source_count_unchanged':1033,'candidate_diff_sha256':candidate['diff_sha256'],'candidate_files':candidate['files'],'backend_RED':{'methods':9,'failed_methods':3,'passed_methods':6,'failure_observations':20,'errors':0,'seconds':5.836,'exit':1},'native_previous_evidence':{'package':F.name,'same_source1033_hashes_verified':True,'unmodified_native_SITE22_chains':72,'fresh_native_candidate_GREEN':'NOT RUN'},'destination_prototype':{'explicit_transport_and_temporary_CSS_simulation':True,'v1':counts['prototype-v1'],'v2':counts['prototype-v2'],'long_mobile_document':{r['lang']:[r['baseline']['document'],r['prototype']['document'],r['rollback']['document']] for r in long_mobile},'candidate_applied':False,'pageerrors':0,'unexpected_local_HTTP_errors':0,'nonloopback_resources':'blocked; externalfontERR_FAILED diagnosed; no console-clean claim','PNG':72},'preservation':{'source1033':True,'prior_packages':36,'prior_files':7436,'sharedMO_cbmignore':True,'refs_index_bytes_empty_staging':True,'active_run_NONE':True,'foreign_runtime_identities_states':len(old),'own_fixtures_restored':True,'normal_fixture_expected_logs':52},'git':entry['git'],'execution':'/root inline canonical django-reviewer + frontend-admin scope; no independent-agent claim','module10':'14OPEN (9P2/5P3); full acceptance pending','retained_LOCAL_closures':['SITE01','SITE15','SITE06','SITE19','SITE21','SITE08','module09 composite'],'NOT_RUN':['candidate actual-source backend GREEN','candidate native redirect GREEN','unmodified full acceptance of new destination','full module10/global/module11/production/cross-browser/a11y'],'production':'UNKNOWN; not contacted'}
write('verification.json',result);write('source-final.json',{'sources':entry['sources'],'application_changes':0,'git':entry['git']})
report='''# SITE-QA-22 — выход из разделов настроек, PLAN 2026-10-18

**SITE22/P3 подтверждён OPEN; конкретный three-file PLAN готов, application changes0.** [План](IMPLEMENTATION_PLAN.md), [exact diff](proposed.diff), [SHA](candidate-manifest.json), [verification](verification.json). После обычного Save предлагается возвращаться в существующий settings hub; continue/errors/stale409/ACL сохраняются. Module10 остаётся14OPEN(9P2/5P3), full acceptance pending. Production UNKNOWN/не контактировали.

Execution /root inline в canonical django-reviewer/frontend-admin scope, без независимого специалиста. User «давльше» продолжает модуль10 после закрытия SITE08; предыдущая авторизация ограничена его CSS. Новый scope требует решения по concrete PLAN согласно AGENTS.md. Все1033source SHA/HEAD852938d96764ae315b92859e3651e5ea62054a36/branch codex/module09-transfer-2026-10-16-r1 совпадают с завершённым предыдущим пакетом.

## Причина и границы

Actual src/catalog/domain_admin/site.py:178 `changelist_view` шести subsection admins направляет на singleton editor. Installed Django6.0.2 `response_change` normal-save ветка вызывает `response_post_save_change` →default subsection changelist→same editor. Полный installed contract/sourceSHA сохранён; не догадка по документации. Graph stale/coverage_unavailable, graph6INHERITS edges подтверждены actualsource иruntime registry: branding/about/contacts/footer/empty/visibility. Analytics наследует другой mixin, catalogue/gallery отдельные ModelAdmin.

Изменение1: только base hook `response_post_save_change` возвращает existing `admin:catalog_sitesettings_changelist`. Оно действует после сохранения/LogEntry/message, не переписывает response_change и не обходит форму/409/права. Изменение2: новый постоянный regression test из exact candidate. Изменение3: hub-only alert wrapping в kidsmap_site_settings.css. На новом destination отсутствует settings-form stylesheet; long brand в сообщении даёт мобильный document AZ1039/RU1020/EN1028px. Labelled preview+temporary scopedCSS возвращает360; снятиеCSS точно возвращает1039/1020/1028. Поэтому дополнительный CSS входит в тот же исправляемый поток. Без template/JS/PO/моделей/схемы/общего shell/новых зависимостей.

## Проверки

Fresh own DJANGO_TESTING=1/current3root locales, normal/testDB/cache/media/email отдельно, envclear/integrationsdisabled/ROrepo. [Backend RED](evidence/red-backend.json):9методов/5.836s/exit1,3failed/6PASS,20expectedfailure observations/0errors.18section×language cases +proxy-only +default no-button Save доказывают неверный exit при correct persistence/1log. Continue/invalid200/stale409/denied403/analytics/catalogue controlsPASS. Test `default_enter` — HTTP POST без кнопки; native клавишаEnter этим не проверяется. Initial v1 имел дополнительный QA failure из-за неверного общего PK для двух разных моделей; original evidence сохранён, исправлен fixtureID, destination assertions не ослаблялись.

72unmodified native `_save` chains POST302→changelist302→same editor200 берутся из предыдущего sealed SITE08 followup на **точно тех же1033source hashes**. Это переиспользованное доказательство, не новый browserGREEN. Новый destination probe сознательно является **transport/CSS simulation**. Первая попытка GET redirect interception не сработала:12`actual_hub_render`FAIL из162controls, исходники/данные/36PNG сохранены. Во v2 clicked footer formPOST форвардится route.fetch(maxRedirects0), меняется только Location ответа на realhub.13rewrites включая footer_restore, branding native;12destination cells AZ/RU/EN×360/1440×short/long дают162/162controlsPASS с exactCSS rollback и unchanged fixture во время стиля. Данные и1log каждой операции проверялись. **Ни hook, ни CSS не применены; это не actual-source/native candidateGREEN.** Дополнительная ошибка ожидания12rewrites вместо13и audit baseline whitespace объяснены в сохранённых qualification/checks; продуктовые assertions не удалялись.

Candidate AST parse +gitapply--check PASS; no whitespace в добавленных строках, existing CRLF/старые whitespace сохранены. Installed runtime6consumer checkPASS.72PNG/матрица/визуальная проверка сохранены. Pageerrors/неожиданныхlocalHTTPнет; nonloopbackfontsblocked/ERR_FAILED, не console-clean. Prototype initial/final52expected synthetic logs, original brand/email восстановлены; JSON/gallery/media names+bytes unchanged. Unmodified native newdestination redirect и backendGREEN **NOT RUN**. Previous105backend/33.566sOK — исторический baseline; после применения план требует свежие114methods и native responsive round trips.

## Сохранность и решение

Сохранены36prior packages/7436files/sharedMO/.cbmignore/refs/index/empty staging/activeNONE/foreign runtime IDs-states. Новый own33600 stand/normal+testDB оставлен со своими synthetic fixtures; чужие стенды не перезапускались. Guide/MASTER append-only. SITE01/15/06/19/21/08 иmodule09 LOCAL closures retained; SITE20/SITE11/остальные findings OPEN. Полный модуль10 не принят. Без commit/push/deploy/production/module11.

Требуется одобрить **только exact3file proposed.diff SHAe60661fd4053bc76c501282f788a72351c8ea0d9f1f54ee7439343c260143e97**. Затем новый fresh own RED→exactapply→backend/nativeGREEN по плану. До этого статус SITE22 остаётсяOPEN; внедрения не было.
'''
(O/'REPORT.md').write_text(report)
note='''\n\n## SITE-QA-22 PLAN READY / APPROVAL PENDING — 2026-10-18 pc-r1

**SITE22/P3 CONFIRMED OPEN; exact3file PLAN READY, NOTAPPLIED.** [REPORT]({prefix}{name}/REPORT.md), [PLAN]({prefix}{name}/IMPLEMENTATION_PLAN.md), [diff]({prefix}{name}/proposed.diff), [verification]({prefix}{name}/verification.json). Proposed base.response_post_save_change→existinghub for6subsections +hub-onlyalertCSS +newbehaviorregressiontest. Actual Django6.0.2source/6runtime consumers verified; analytics/catalogue/gallery remain separate. FreshRED9methods3failed/6PASS/20observations/0errors/5.836s; initialwrongfixturePK controlFAIL retained/corrected without destination assertion changes. Prior72nativechains reused on same1033source hashes, notfreshGREEN. New destination transport/CSS simulation12cells162controlsPASS, longmobileAZ1039/RU1020/EN1028→360→exactrollback. v1GETintercept12FAIL retained;v2route.fetch Locationrewrite13includingrestore explicitlylabelled, no native/applied-sourceGREEN claim.72PNG; normalfixture52expectedlogs,scalarsrestored/JSON-media-gallery unchanged. App0changes/source1033unchanged, candidate3files/applycheckASTPASS; existingCRLF/whitespace preserved.36priorpackages/7436files/MO/.cbmignore/refs-index/activeNONE/foreignruntimes preserved;docsappendonly. **Module10 remains14OPEN(9P2/5P3), fullacceptancepending**; SITE01/15/06/19/21/08/module09 closures retained. SITE20/SITE11 othersOPEN. Next exactscope decision then freshown RED→apply→114backend/nativeGREEN; no commit/push/deploy/production/global/module11, inline/no independent-agent claim.
'''
docs={}
for rel,h in entry['documents'].items():
 p=R/rel;before=p.read_bytes();assert sha(p)==h and before==(Q/'documents'/rel).read_bytes();p.write_bytes(before+note.format(prefix='../qa/' if rel.endswith('MASTER_AUDIT.md') else '',name=O.name).encode());assert p.read_bytes().startswith(before);docs[rel]={'original_bytes':len(before),'original_sha256':h,'append_only':True,'final_sha256':sha(p)}
write('document-preservation.json',docs)
post=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True);assert post.returncode==0 and sha(R/'.git/index')==entry['git']['index_sha256'] and all(sha(R/p)==h for p,h in entry['sources'].items())
write('evidence/final-checks.json',{'native_git_diff_check_exit':0,'post_append_diff_check_exit':0,'candidate_apply_check_exit':0,'source1033unchanged':True,'candidate_not_applied':True,'approval_pending':True})
manifest={p.relative_to(O).as_posix():sha(p) for p in O.rglob('*') if p.is_file() and p.name!='artifact-manifest.json'};write('artifact-manifest.json',manifest);assert all(sha(O/p)==h for p,h in manifest.items());print(json.dumps({'status':result['status'],'source1033unchanged':True,'candidate_files':3,'prior_packages':36,'prior_files':7436,'PNG':72,'sealed_entries':len(manifest),'module10':result['module10']},indent=2))
