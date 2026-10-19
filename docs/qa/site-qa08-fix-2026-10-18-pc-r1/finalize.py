import csv,hashlib,json,re,struct,subprocess,urllib.request
from datetime import datetime,timezone
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site08-pc-fix-r1';P=O.parent/'site-qa08-recheck-2026-10-18-pc-r1'
read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();write=lambda n,d:(O/n).write_text(json.dumps(d,ensure_ascii=False,indent=2))
assert not (O/'artifact-manifest.json').exists()
entry=read(O/'source-entry.json');applied=read(O/'applied.json');sources=read(O/'source-applied.json')['sources'];cand=read(P/'candidate-manifest.json')
assert len(entry['sources'])==1032 and len(sources)==1033 and applied['application_refinements']==0 and applied['other_existing_sources_unchanged']==1031
assert all(sha(R/p)==h for p,h in sources.items());assert [p for p,h in entry['sources'].items() if sha(R/p)!=h]==['src/catalog/templates/admin/catalog/shared_settings_change_form.html']
assert set(sources)-set(entry['sources'])=={'static/admin/css/pages/kidsmap_settings_forms.css'}
for p,d in cand['files'].items():assert sha(R/p)==d['candidate_sha256']
assert sha(O/'implemented.diff')==sha(P/'proposed.diff')==cand['diff_sha256']
css=(R/'static/admin/css/pages/kidsmap_settings_forms.css').read_bytes();assert all(not line.endswith((b' ',b'\t')) for line in css.splitlines()) and all(line.endswith(b'\r\n') for line in css.splitlines(keepends=True))
priorfiles=0
for pkg,files in entry['prior_packages'].items():
 for p,h in files.items():assert sha(R/'docs/qa'/pkg/p)==h,(pkg,p);priorfiles+=1
assert len(entry['prior_packages'])==34 and priorfiles==6763
assert all(sha(R/p)==h for p,h in entry['shared_mo'].items()) and sha(R/'.cbmignore')==entry['cbmignore']
git=lambda *a:subprocess.check_output(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap',*a],text=True).strip()
assert git('rev-parse','HEAD')==entry['git']['head'] and git('branch','--show-current')==entry['git']['branch'] and git('rev-parse','task33-progress')==entry['git']['task33_ref'] and not git('diff','--cached','--name-only') and sha(R/'.git/index')==entry['git']['index_sha256']
assert re.search(r'^active_run: NONE$',(R/'docs/task33/implementation-status.md').read_text(),re.M)
old={x.split()[1]:(x.split()[0],x.split()[2]) for x in entry['containers']};now={x.split()[1]:(x.split()[0],x.split()[2]) for x in subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines()};assert all(now.get(k)==v for k,v in old.items())
setup=read(O/'evidence/setup.json');assert subprocess.check_output(['docker','inspect','--format','{{.Id}}',setup['app']],text=True).strip()==setup['container_id']
reverse=subprocess.run(['git','-C',str(R),'apply','--reverse','--check',str(O/'implemented.diff')],capture_output=True,text=True);assert reverse.returncode==0,reverse.stderr
follow=read(O/'followup/candidate-manifest.json');assert follow['not_applied'] and len(follow['files'])==1
for p,d in follow['files'].items():assert sha(R/p)==d['before_sha256'] and sha(O/'followup/candidate'/p)==d['candidate_sha256']
assert sha(O/'followup/proposed.diff')==follow['diff_sha256'];fcheck=subprocess.run(['git','-C',str(R),'apply','--check',str(O/'followup/proposed.diff')],capture_output=True,text=True);assert fcheck.returncode==0,fcheck.stderr
diff=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True);assert diff.returncode==0,diff.stderr
names=['browser-acceptance-red','browser-readonly-red','browser-sentinels-red','browser-acceptance-green','browser-readonly-green','browser-sentinels-green','browser-json-mobile','browser-media-footer','browser-public-json','browser-long-json','browser-permissions','browser-json-error-snapshots','browser-file-error-snapshots','browser-file-error-central','browser-followup-prototype'];datasets={n:read(O/'evidence'/(n+'.json')) for n in names};counts={}
for n,d in datasets.items():
 assert not d.get('error') and not d.get('pageerrors') and not d.get('local_errors')
 values=[v for r in d['rows'] for v in r['checks'].values()];assert all(type(v) is bool for v in values);counts[n]={'rows':len(d['rows']),'pass':values.count(True),'fail':values.count(False)}
expected={'browser-acceptance-red':(162,820,314),'browser-readonly-red':(18,126,0),'browser-sentinels-red':(12,48,0),'browser-acceptance-green':(162,1134,0),'browser-readonly-green':(18,126,0),'browser-sentinels-green':(12,60,0),'browser-json-mobile':(48,354,0),'browser-media-footer':(62,355,25),'browser-public-json':(3,15,3),'browser-long-json':(20,186,0),'browser-permissions':(2,7,0),'browser-json-error-snapshots':(18,126,0),'browser-file-error-snapshots':(12,60,12),'browser-file-error-central':(12,72,0),'browser-followup-prototype':(5,14,0)}
for n,(rows,pas,fail) in expected.items():assert counts[n]=={'rows':rows,'pass':pas,'fail':fail},(n,counts[n])
for n in ['browser-acceptance','browser-readonly']:assert (O/(n+'-red.js')).read_bytes().replace(('red-'+('acceptance' if n=='browser-acceptance' else 'readonly')+'-').encode(),('green-'+('acceptance' if n=='browser-acceptance' else 'readonly')+'-').encode())==(O/(n+'-green.js')).read_bytes()
for n in ['browser-acceptance-red','browser-readonly-red','browser-sentinels-red','browser-acceptance-green','browser-readonly-green','browser-sentinels-green']:assert datasets[n]['no_fixture_write']
media=datasets['browser-media-footer'];mediafails=[(r['id'],k) for r in media['rows'] for k,v in r['checks'].items() if not v];assert sum(k=='error_visible' for _,k in mediafails)==12 and sum(k=='exited' for _,k in mediafails)==12 and sum(k=='no_overflow' for _,k in mediafails)==1
assert all(k=='visible_inline_error' for r in datasets['browser-file-error-snapshots']['rows'] for k,v in r['checks'].items() if not v)
assert all(k=='public_filter_value' for r in datasets['browser-public-json']['rows'] for k,v in r['checks'].items() if not v)
actual=[n for n in names if not n.endswith('-red') and n!='browser-followup-prototype'];rawtotal=sum(counts[n]['pass']+counts[n]['fail'] for n in actual);rawpass=sum(counts[n]['pass'] for n in actual);rawfail=sum(counts[n]['fail'] for n in actual);assert (rawtotal,rawpass,rawfail)==(2535,2495,40)
for n in actual:
 text=(O/(n+'.js')).read_text();assert 'addStyleTag' not in text and 'classList.add' not in text
proto=datasets['browser-followup-prototype']['rows'][2];assert proto['baseline']['document']==366 and proto['prototype']['document']==360 and proto['rollback']==proto['baseline']
backend=read(O/'evidence/green-backend.json');assert backend['exit']==0 and 'Ran 105 tests in 33.566s' in backend['summary'] and 'OK' in backend['summary'] and not backend['failures'] and not backend['errors']
ids=re.findall(r'^test_\S+ \(([^)]+)\)',(Q/'green-tests.log').read_text(),re.M);assert len(ids)==len(set(ids))==105;write('evidence/backend-test-ids.json',ids)
isolation=read(Q/'test-isolation.json');assert isolation['testing'] and isolation['own_separate_test_cache'] and isolation['normal_fixture_storage_not_used'] and isolation['test_DB']=='test_m10s08_fix_r1';write('evidence/test-isolation.json',isolation)
static=read(O/'evidence/static-runtime.json');assert static['source_count']==1033 and len(static['branches'])==18 and static['actual_template_compiled'] and static['CSS_HTTP_status']==200 and static['CSS_HTTP_sha256']==sha(R/'static/admin/css/pages/kidsmap_settings_forms.css') and static['integrations_disabled'] and static['current3root_locales_verified']
with urllib.request.urlopen('http://127.0.0.1:33580/qa/site08/state/',timeout=10) as response:catalog=json.load(response)
with urllib.request.urlopen('http://127.0.0.1:33580/qa/site08/form-state/',timeout=10) as response:fixture=json.load(response)
initial=read(O/'fixture-entry.json');assert all(catalog[k]==initial[k] for k in ['districts_json','metro_stations_json','seo_pages_json']) and catalog['admin_log_count']==fixture['admin_log_count']==84
orig=media['initial'];assert fixture['brand_name']==orig['brand_name'] and fixture['footer_email']==orig['footer_email'] and fixture['logo_size']==orig['logo_size'] and fixture['gallery']==orig['gallery'];write('fixture-final.json',{'catalog':catalog,'site':fixture,'restoration':'Original JSON/name/email/image dimensions and pre-existing own gallery rows restored natively; image filename/bytes can differ under normal upload normalization;84expected synthetic LogEntries retained; one public Place fixture retained.'})
png={}
for p in sorted((O/'png').glob('*.png')):
 b=p.read_bytes();assert b[:8]==b'\x89PNG\r\n\x1a\n';w,h=struct.unpack('>II',b[16:24]);png[p.relative_to(O).as_posix()]={'sha256':sha(p),'width':w,'height':h}
assert len(png)==239;write('png-manifest.json',png);visual=read(O/'visual-review.json');assert visual['inspection_completed'] and all((O/'png'/p).exists() for p in visual['inspected'])
with (O/'matrix.csv').open('w',newline='') as f:
 w=csv.writer(f);w.writerow(['suite','id','model','role','lang','width','phase','check','pass'])
 for n,d in datasets.items():
  for r in d['rows']:
   for phase in ['source','baseline','prototype','rollback']:
    checks=r['checks'] if phase=='source' else r.get(phase,{}).get('checks',{})
    for k,v in checks.items():w.writerow([n,r['id'],r.get('model'),r.get('role'),r.get('lang'),r.get('width'),phase,k,v])
write('failure-classification.json',{'raw_actual_source_checks':2535,'raw_pass':2495,'raw_fail':40,'real_failures':{'SITE08_remaining_saved_message_document_overflow':1,'SITE22_preexisting_save_exit_navigation':12},'QA_observation_failures_retained':{'hidden_duplicate_errorlist_selected':12,'inline_error_expected_but_only_central_field_linked_error_visible':12,'raw_uppercase_public_label_expected_and_JSON_dependency_not_established':3},'supporting_passes':{'central_field_linked_error_and_native_anchor_focus':72,'mobile_JSON_error_draft_focus_bounds':126},'public_JSON_scope':'Native persistence/reload PASS; published-Place lowercase district presence does not establish districts_json consumer dependency; UNVERIFIED/manual_review, no unsupported finding added.','source_before_after_Python_site_admin_unchanged':True,'no_assertions_rewritten_for_green':True})
write('graph-evidence.json',{'project':'C-kidsmap','generation':'2026-10-16T18:56:53Z','freshness':'stale; template metadata_changed/coverage_unavailable; new CSS missing in index','impact':'Approved sealed PLAN9actual consumers reused; actual source/runtime compile18permission/model branches/CSS_HTTP200/source1033hashes verified','new_discovery':'build_public_place_filter_options exact graph1match has_morefalse, source verified database-derived districts; graph navigation only','cache_reindex_mutations':False})
result={'utc':datetime.now(timezone.utc).isoformat(),'status':'Exact approved2file patch APPLIED; acceptance PARTIAL; SITE-QA-08 REMAINS OPEN','application_files':applied['approved_files'],'application_refinements':0,'source_count':1033,'other_existing_sources_unchanged':1031,'backend':{'tests':105,'failures':0,'errors':0,'seconds':33.566,'exit':0},'native':{'basic_source_GET_readonly_neighbor_checks_pass':1320,'raw_actual_source_checks':2535,'raw_pass':2495,'raw_fail':40,'real_failures':13,'QA_observation_failures':27,'suites':counts,'pageerrors':0,'unexpected_local_HTTP_errors':0,'expected_negative_HTTP':'viewerPOST403/deniedGET403 explicitly tested','PNG':239,'no_positive_API_POST':True},'followup':{'files':1,'applied':False,'temporary_CSS_prototype':'366→360→366','controls_pass':14,'actual_source_followup_GREEN':'NOT RUN'},'preservation':{'prior_packages':34,'prior_files':priorfiles,'shared_MO':True,'cbmignore':True,'refs_index_bytes_empty_staging':True,'active_run_NONE':True,'foreign_container_identities_states':len(old),'fixture_original_JSON_scalar_image_dimensions_gallery_rows_restored':True,'own_native_successful_log_count':84},'git':entry['git'],'module10':'15canonical OPEN (10P2/5P3); SITE08 still OPEN, new SITE22/P3 OPEN; full acceptance pending','closed_local_retained':['SITE01','SITE15','SITE06','SITE19','SITE21','module09 composite'],'separate_open_limits':['SITE20','SITE11','SITE22'],'execution':'inline; no independent-agent claim','NOT_RUN':['applied-source followup GREEN','backend Save-exit repair','controlled native public JSON dependency','full accessibility','production/global/module11']};write('verification.json',result);write('source-final.json',{'sources':sources,'application_files':applied['approved_files'],'application_refinements':0,'other_existing_sources_unchanged':1031,'git':entry['git']})
report='''# SITE-QA-08 — применённый patch и незавершённая приёмка, 2026-10-18

**Exact approved2file patch APPLIED; SITE08 остаётся OPEN.** Основные формы исправлены, но after-save notification на RU360 расширяет документ до366px. Подготовлен [отдельный one-CSS followup](followup/IMPLEMENTATION_PLAN.md) /[точный diff](followup/proposed.diff); он **НЕ ПРИМЕНЁН**. Новая отдельная [SITE22/P3](findings/SITE-QA-22.md): «Сохранить и выйти» возвращается в subsection editor. Module10 теперь **15OPEN (10P2/5P3)**, full acceptance pending. Ложного CLOSED/полного GREEN нет.

Execution /root inline в canonical frontend-admin/orchestrator scope; independent specialist review NOT RUN. User «дальше» непосредственно после вопроса о применении конкретного SITE08 плана — authorization.json. LOCAL HEAD852938d96764ae315b92859e3651e5ea62054a36, branch codex/module09-transfer-2026-10-16-r1; dirty WORKTREE сохранён. Production UNKNOWN/не контактировали.

## Применено

Точно approved implemented.diff (SHA b19111c30e283d2514c81b649e73fd1de8409556de73dc4e132a0bb9f7234c0a): shared_settings_change_form.html root col-12/marker/editable flag +link, новый scoped kidsmap_settings_forms.css. Template e3791aa31eba0d31ecd14ce559cfca8745185b9ba3950dcc4aa92d224e5cbe29; CSS baf70032e5b918a783c136b4fa9449855c6eafb18df13f015a7ff144c7367f83. Source1033:1existing changed/1new/1031others unchanged, application refinements0. Global shell CSS/JS/backend/model/schema/PO/permissions/revision semantics не менялись. Full Git diff с HEAD также содержит прежние dirty edits; наш exact patch считается от fresh entry.

## Проверки и пределы

| Набор | Факт |
| --- | --- |
| Actual-source RED9forms×3langs×6widths | 820PASS314expectedFAIL /1134checks |
| Тот же actual-source GREEN | 1134/1134PASS,162cases |
| Readonly catalogue18cases | 126/126PASS до/после |
| Place/Event12native neighbor cases | 48baselinePASS →60PASS включая exactgeometry parity/no scoped CSS/marker |
| Native mobile JSON /both buttons /all3malformed fields/retries | 354/354PASS,48rows |
| Long1024char/nestedUnicode JSON/editor+readonly/native restore | 186/186PASS,20rows |
| Native mobile JSON errors/focus/bounds unique screenshots | 126/126PASS,18cases |
| Native field-linked central file errors/anchor focus | 72/72PASS,12cases |
| Viewer negativePOST403/deniedGET403/no writes | 7/7PASS |
| Existing backend regression suite | 105tests/33.566s/OK/exit0 |
| Actual source compile/current locale/CSS | 18permission-model roots,9active consumers,1033source hashes, current3root locales, CSSHTTP200/exactSHA |

Native media/footer62rows дали355PASS25FAIL; original assertions/results сохранены. Native image/email/gallery valid save/reload/public SSR values, invalid no-write/retry и actual Select2 longest existing option/open/Escape работают. Из25FAIL:12wrong hidden duplicate `.errorlist` targets,12real Save-exit mismatches SITE22,1real saved-message overflow remainingSITE08. Дополнительная ошибочная inline-error assumption дала12FAIL: actual error text существует в видимом central field-linked summary, inline container содержит только hidden duplicate list. Correct field-linked visibility/native focus затем подтвердились72checks. Эти failed datasets не переписывались/не удалялись.

Public JSON suite15PASS3FAIL: native mobile POST/reload/LogEntry/publicGET200 прошли, uppercase raw district expectation не совпала с lowercase public label. Source public_filter_options.py85–213 строит districts по published Place counts; presence `site08 qa district` не доказывает consumption districts_json. **Controlled native JSON→public dependency UNVERIFIED/manual_review**; ложный новый finding не создан и assertion не заменён ради green. Одна own synthetic published Place создана existing factory только как fixture foundation, не как native publication transition.

Raw actual-source aggregate2535checks: **2495PASS/40FAIL**. Классификация40:13real (remainingSITE08one +SITE22twelve),27incorrect/unsupported QA observations retained. Поэтому aggregate GREEN не заявляется. Details failure-classification.json /verification.json /matrix.csv. Все datasets без pageerrors/неожиданных localHTTPerrors; negative403 ожидаемые; external fonts blocked/ERR_FAILED диагностированы, console-clean не заявляется.

## Остаточный дефект и следующий scope

Native RU360 `_continue`, brand qa_ru_360, footer qa_ru_360_continue@example.invalid: стандартный Jazzmin message состоит из anonymous flex text/link. Baseline document366, временный scoped normal-flow CSS360, rollback366;14controlsPASS и unchanged fixture во время style probe. [PNG до](png/followup-alert-baseline-ru-360.png) /[прототип](png/followup-alert-prototype-ru-360.png). Followup меняет только existing CSS, не template/backend/navigation; candidate074e3405a541bc9c0ce6eaefea013388d48e810d2d9a48eb3a4bb7c940d7474c, diff da5563bc9a2e2d75f6cdf8ffa2b7c1992c440ff2ccbc0d5a2eb8678cd77dde99. DOM prototype не applied-source GREEN. До решения пользователя этот CSS не записан в приложение.

SITE22 native chain302POST→302GET changelist→200GET same editor, data/LogEntry correct; site.py untouched versus entry. Это отдельный pre-existing navigation issue/P3, не CSS regression. Нужен отдельный Django plan, не расширение текущего diff.

## Изоляция и сохранность

Own33580, normal/test separate DB/cache/media/private-media, locmem email; env clear/current source+locale guard до setup, integrations disabled. Test isolation proof/test IDs сохранены. Исходные JSON/scalar fields/image dimensions и прежние own gallery rows восстановлены native saves;84expected synthetic LogEntries, normalized uploaded file paths/bytes и owned media/public Place fixture оставлены на своём стенде. Не утверждается byte-identical restoration image under existing normalization. Ни одного foreign fixture cleanup/restart.

Сохранены34prior sealed packages/6763files, sharedMO/.cbmignore/refs/index/empty staging/activeNONE/foreign container IDs-state. Guide/MASTER append-only. SITE01/15/06/19/21 и module09 composite LOCAL closures retained; SITE20/SITE11 остаются отдельными OPEN.239PNG, named visual-review, commands/exits/manifests сохранены. Первый sentinel-route failure, screenshot9within-run overwrite и оба ошибочных error observers сохранены/объяснены; supplemental18unique JSON states доступны. WSL Git отметил74CRLF lines как trailing whitespace; exact approved bytes preserved/no whitespace bypass, Windows diffcheck0 и отдельный no-spaces-before-CRLF auditPASS. No commit/push/deploy/production/global/module11.

Следующий шаг — одобрить только конкретный one-file followup, затем fresh own native sourceRED→apply→GREEN по его плану. AGENTS.md требует «Future implementation requires a concrete plan and user approval for its scope»; дополнительного alert rule в первоначальном согласованном diff нет.
'''
(O/'REPORT.md').write_text(report)
print('All evidence/preservation assertions passed; status remains PARTIAL OPEN; appending and sealing.',flush=True)
note='''\n\n## SITE-QA-08 APPLIED / ACCEPTANCE PARTIAL; SITE22 OPEN — 2026-10-18 pc-r1

**Approved exact2file SITE08 patch APPLIED; SITE08 REMAINS OPEN.** [REPORT]({prefix}{name}/REPORT.md), [verification]({prefix}{name}/verification.json), [oneCSS followup PLAN]({prefix}{name}/followup/IMPLEMENTATION_PLAN.md), [followup diff]({prefix}{name}/followup/proposed.diff), [newSITE22/P3]({prefix}{name}/findings/SITE-QA-22.md). Template e3791aa/newCSS baf70032; app2files/1033sources/1031others unchanged/refinements0. SourceRED820PASS314FAIL→coreGREEN1134/1134;readonly126/sentinels60PASS,105backend33.566sOK; mobileJSON354/long186/JSONerror126/centralfileerror72/permission7PASS. Raw actual2535checks2495PASS40FAIL retained/classified:13real (remainingSITE08saved-toast366px at360 one;SITE22save-exit12),27QA observer/unsupported public-label assumptions; no blanketGREEN/closure. Native media/public logo/footer/gallery persistence works. Public districts source database-derived; native JSON→public dependencyUNVERIFIED/manual_review. Followup temporary scopedCSS366→360→366/14controlsPASS, candidate074e3405/diffda5563... **NOTAPPLIED**, needs separate exact1file decision. Source site.py unchanged, native Saveexit chain302→302→same200, separateP3/Django plan.239PNG; original wrongselectors/screenshotcollision/sentinelroute evidence retained, no assertion rewrite forgreen. Native original JSON/scalars/image dimensions/gallery rows restored,84synthetic LogEntries/media/own public fixture retained.34priorpackages/6763files/MO/.cbmignore/refs-index/activeNONE/foreign runtimes preserved; docsappendonly. **Module10 now15OPEN (10P2/5P3), full acceptance pending**; SITE01/15/06/19/21 and module09 closures retained. No commit/push/deploy/production/global/module11; inline/no independent-agent claim.
'''
docs={}
for rel,h in entry['documents'].items():
 p=R/rel;before=p.read_bytes();assert sha(p)==h and before==(Q/'documents'/rel).read_bytes();prefix='../qa/' if rel.endswith('MASTER_AUDIT.md') else '';p.write_bytes(before+note.format(prefix=prefix,name=O.name).encode());assert p.read_bytes().startswith(before);docs[rel]={'original_bytes':len(before),'original_sha256':h,'append_only':True,'final_sha256':sha(p)}
write('document-preservation.json',docs)
post=subprocess.run(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','diff','--check'],capture_output=True,text=True);assert post.returncode==0 and sha(R/'.git/index')==entry['git']['index_sha256'] and all(sha(R/p)==h for p,h in sources.items());write('evidence/final-checks.json',{'native_git_diff_check_exit':diff.returncode,'post_append_diff_check_exit':post.returncode,'reverse_initial_patch_check_exit':reverse.returncode,'followup_apply_check_exit':fcheck.returncode,'no_spaces_tabs_before_CRLF_new_CSS':True,'exact_initial_candidate_sha_verified':True,'followup_not_applied':True,'source_hashes_match':1033})
(O/'prepare_entry.py').write_bytes((R/'.tmp/prepare_site08_fix.py').read_bytes())
manifest={p.relative_to(O).as_posix():sha(p) for p in O.rglob('*') if p.is_file() and p.name!='artifact-manifest.json'};write('artifact-manifest.json',manifest);assert all(sha(O/p)==h for p,h in manifest.items());print(json.dumps({'status':result['status'],'backend':result['backend'],'basic_checks_pass':1320,'raw_actual':{'pass':2495,'fail':40,'real_remaining':13,'QA_observations':27},'prior_packages':34,'prior_files':priorfiles,'PNG':239,'sealed_entries':len(manifest),'followup_not_applied':True,'module10':result['module10']},indent=2))
