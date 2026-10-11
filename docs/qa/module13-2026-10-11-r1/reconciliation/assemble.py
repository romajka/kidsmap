import ast, csv, hashlib, json, re, subprocess
from collections import Counter, defaultdict
from pathlib import Path

ROOT=Path('C:/kidsmap');OUT=Path(__file__).resolve().parent;QA=ROOT/'docs/qa'
D=json.loads((OUT/'historical-findings.json').read_text(encoding='utf-8'))
HEAD=D['head'];F=D['findings']
MODULE_NAMES={'01':'Постоянные места','02':'Организации/подключения/сотрудники','03':'Специалисты/сотрудничество','04':'Мероприятия','05':'Программы/занятия/группы/цены','06':'Публичный каталог/карта','07':'Аккаунт/права/приглашения','08':'Модерация','09':'Отзывы/избранное/уведомления','10':'Настройки/разделы/общие страницы','11':'SEO/URL','12':'Аналитика'}
LATEST={}
for r in D['reports']:LATEST[r['module']]=r
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rel(p):return str(p.relative_to(ROOT)).replace('\\','/')
def mdpath(p):return '../../'+str(p).removeprefix('docs/qa/')
def source_link(p,line=1):return '../../../../'+p+':'+str(line)
def load_rows(folder):
    p=folder/'matrix.json'
    if p.exists():
        x=json.loads(p.read_text(encoding='utf-8'))
        if isinstance(x,dict):return list(x.get('observations',x.get('rows',x.get('matrix',[]))))+list(x.get('not_run',[]))
        return x
    with (folder/'matrix.csv').open(encoding='utf-8-sig',newline='') as f:return list(csv.DictReader(f))

coverage=[]
for m,r in LATEST.items():
    folder=ROOT/Path(r['report']).parent
    rows=load_rows(folder)
    snapshots={'snapshot.json':folder/'snapshot.json'}
    if (folder/'current-snapshot.json').exists():snapshots['current-snapshot.json']=folder/'current-snapshot.json'
    snapshotdata={k:json.loads(p.read_text(encoding='utf-8')) for k,p in snapshots.items()}
    for index,row in enumerate(rows,1):
        status_fields=['status'] if 'status' in row else [k for k in row if k.endswith('_status')]
        if not status_fields:status_fields=['status']
        for field in status_fields:
            historical=row.get(field,'UNRECORDED')
            named_snapshot=row.get('snapshot','snapshot.json')
            snap=snapshotdata.get(named_snapshot,{})
            snapshotfile=folder/named_snapshot
            if not snapshotfile.exists():snapshotfile=folder/'snapshot.json'
            evidence=row.get('evidence',row.get('screenshot',row.get('shot')))
            if evidence and isinstance(evidence,str):evidence=rel(folder/evidence) if not evidence.startswith('docs/') else evidence
            else:evidence=r['matrix_file']
            coverage.append({'record_kind':'HISTORICAL_OBSERVATION','module':m,'scenario':str(row.get('scenario',row.get('id',row.get('state','UNRECORDED'))))+' / '+field,
                'role':row.get('role','UNRECORDED'),'language':row.get('lang',row.get('language','UNRECORDED')),'width':row.get('width','UNRECORDED'),
                'snapshot':rel(snapshotfile),'snapshot_head':snap.get('head',r['head']),'snapshot_digest':snap.get('source_digest','UNRECORDED'),
                'historical_status':historical,'fresh_module13_status':'NOT RUN','evidence':evidence,'evidence_row':row.get('evidence_row',index),
                'url':row.get('url','UNRECORDED'),'note':'Historical observation preserved. Root module13 evidence must supply any fresh result.'})
    for name in ['coverage-gaps.json']:
        gapfile=folder/name
        if not gapfile.exists():continue
        gaps=json.loads(gapfile.read_text(encoding='utf-8'))
        if isinstance(gaps,dict):gaps=gaps.get('gaps',gaps.get('not_run',gaps.get('limits',[])))
        if not isinstance(gaps,list):continue
        for index,g in enumerate(gaps,1):
            if isinstance(g,str):g={'id':g,'reason':g}
            if not isinstance(g,dict):g={'id':'structured-gap-'+str(index),'reason':json.dumps(g,ensure_ascii=False)}
            coverage.append({'record_kind':'HISTORICAL_EXPLICIT_GAP','module':m,'scenario':g.get('id',g.get('scenario','UNRECORDED')),
                'role':g.get('role','UNRECORDED'),'language':g.get('lang','UNRECORDED'),'width':g.get('width','UNRECORDED'),
                'snapshot':r['snapshot'],'snapshot_head':r['head'],'snapshot_digest':r['source_digest'],
                'historical_status':'NOT RUN','fresh_module13_status':'NOT RUN','evidence':rel(gapfile),'evidence_row':index,'url':'UNRECORDED',
                'note':g.get('reason',g.get('note','Explicit historical gap; see source JSON'))})
parent_file=OUT/'fresh-root-evidence.json'
parent_proof=json.loads(parent_file.read_text(encoding='utf-8')) if parent_file.exists() else {'rows':[]}
for r in parent_proof['rows']:
    ids=r['historical_ids']+r['new_ids'];module=','.join(sorted({fid['module'] for fid in F if fid['id'] in ids})) or '13'
    coverage.append({'record_kind':'FRESH_PARENT_HANDOFF','module':module,'scenario':r['scenario'],
        'role':r['role'],'language':r['lang'],'width':r['width'],'snapshot':r['snapshot'],'snapshot_head':r['snapshot_head'],
        'snapshot_digest':r['snapshot_digest'],'historical_status':'NOT APPLICABLE','fresh_module13_status':r['status'],
        'evidence':r['evidence'],'evidence_row':r['evidence_row'],'url':r['url'],'note':r['execution_attribution']+' IDs: '+','.join(ids)})
with (OUT/'coverage.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(coverage[0]));writer.writeheader();writer.writerows(coverage)

groups=[{'key':'NETWORK-GRANT-UI','ids':['ORG-QA-02','ACCESS-QA-03'],'root_cause':'One missing management surface for network grants and invitations; same organization_workspace.html markup and invitation-only JS.',
         'source_verified':['src/catalog/templates/pages/organization_workspace.html:462','static/js/organization_workspace.js:255'],'severity':'P2','dependency':'Canonical business_team action/CAS and recipient inbox; retain separate recipient-decline ACCESS-QA-02.'},
        {'key':'COMPILED-LOCALE-FRESHNESS','ids':['PLACE-QA-06','EVENT-QA-01','PUBLIC-QA-03','SITE-QA-07'],'root_cause':'Existing ignored compiled catalogs differ from tracked PO; failure applies to runtime locale profile. PLACE-QA-06 has later isolated-builder repair claim.',
         'source_verified':['scripts/build_isolated_locales.py'],'severity':'P2','dependency':'Verify effective LOCALE_PATHS, frozen PO hashes and manifest before startup; rebuilding does not repair missing/fuzzy/wrong source translations.'}]
groupid={fid:g['key'] for g in groups for fid in g['ids']}
repair_claim=ROOT/'docs/qa/place-qa01-07-fix-2026-10-10/REPORT.md'
repair_ids={f'PLACE-QA-{n:02d}' for n in range(1,8)}
for f in F:
    f['root_cause_group']=groupid.get(f['id'],f['id'])
    f['later_repair_claim']=rel(repair_claim) if f['id'] in repair_ids else None
    if f['id'] in repair_ids:f['historical_status']='REPAIRED CLAIM IN LATER WORKTREE REPORT; module13 recheck NOT RUN by this role'
    p=ROOT/f['finding']
    txt=p.read_text(encoding='utf-8-sig')
    direct=None
    if f['module'] in ['06','07']:
        q=p.parent/(('repair-'+f['id']+'.txt') if f['module']=='07' else '')
        if f['module']=='07' and q.exists():direct=rel(q)
    else:
        q=p.with_name(f['id']+'-repair.txt')
        if q.exists():direct=rel(q)
    f['repair_prompt']=direct or f['finding']
    f['repair_prompt_location']='standalone text file' if direct else 'embedded original finding fenced text'
    fresh=[r for r in parent_proof['rows'] if f['id'] in r['historical_ids']]
    if fresh:
        f['fresh_module13_status']='FAIL' if any(r['status']=='FAIL' for r in fresh) else 'NOT RUN'
        f['fresh_module13_evidence']=fresh
        f['fresh_execution_attribution']='Parent /root native module13; support read artifact only.'
D.update({'root_cause_groups':groups,'historical_root_cause_bucket_count':len(set(f['root_cause_group'] for f in F)),
    'later_repair_claim_ids':sorted(repair_ids),'historical_unresolved_ids_count':len([f for f in F if f['id'] not in repair_ids]),
    'historical_unresolved_bucket_count':len({f['root_cause_group'] for f in F if f['id'] not in repair_ids}),
    'fresh_current_open_count':'Partial parent handoff only; 4 historical IDs/3 root-cause buckets FAIL, plus parent new CROSS-QA-01 P2. Full current count belongs to root final report.',
    'fresh_parent_handoff':parent_proof,
    'coverage_rows':len(coverage), 'coverage_kinds':dict(Counter(r['record_kind'] for r in coverage))})

# Source AST declarations, not runtime app registry. Graph-first discovery preceded this read.
def modules_for_entity(name,filename):
    explicit={'Organization':'02','OrganizationPlaceRequest':'02','OrganizationConnectionOperation':'02','OrganizationConnectionItem':'02',
        'OrganizationOwnershipRequest':'02','OrganizationGrant':'02,07','OrganizationTeamInvitation':'02,07','Program':'05','Activity':'05',
        'OfferingGroup':'05','Location':'06','PlaceVenueRequest':'06','Event':'04','EventPhoto':'04','EventOccurrenceChange':'04',
        'PlaceLike':'09','PlaceReviewsByClub':'09','SiteVisit':'12','FunnelEvent':'12','SiteAnalytics':'12','CatalogContentSettings':'11',
        'SpecialistReview':'09','WorkflowNotification':'09','EmailOutbox':'09','StaffRoleAudit':'07','SuperadminPromotionRequest':'07',
        'PlaceLocationOverride':'01','PlaceChangeAudit':'08','ServerDraft':'01,02,03,04,05'}
    if name in explicit:return explicit[name]
    if filename in ['analytics.py']:return '12'
    if filename in ['conversion.py']:return 'UNMAPPED'
    if filename in ['pricing_plan.py']:return '01,05'
    if filename in ['rating_ranking.py','review.py','review_versions.py']:return '09'
    if filename=='seo.py':return '11'
    if filename=='volunteer.py':return '08'
    if filename=='site.py':return '10'
    if filename in ['user.py','owner.py','staff_role.py']:return '07'
    if filename.startswith('specialist'):return '03'
    if filename=='catalog_structure.py':return '02,05,06'
    return '01'

source_inventory=[]
for folder,kind in [(ROOT/'src/catalog/models','MODEL_DECLARATION'),(ROOT/'src/catalog/domain_admin','ADMIN_DECLARATION')]:
    for p in sorted(folder.glob('*.py')):
        tree=ast.parse(p.read_text(encoding='utf-8-sig'),filename=str(p))
        for node in tree.body:
            if not isinstance(node,ast.ClassDef):continue
            bases=[ast.unparse(x) for x in node.bases]
            registered=[]
            for d in node.decorator_list:
                if isinstance(d,ast.Call) and ast.unparse(d.func).endswith('.register'):registered.extend(ast.unparse(x) for x in d.args)
            if kind=='MODEL_DECLARATION' and any(x.endswith(('.TextChoices','.QuerySet','.Manager')) for x in bases):continue
            if kind=='ADMIN_DECLARATION' and not registered:continue
            modules=modules_for_entity(node.name,p.name) if kind=='MODEL_DECLARATION' else ','.join(sorted({m for entity in registered for m in modules_for_entity(entity,p.name).split(',')}))
            source_inventory.append({'kind':kind,'source':rel(p),'line':node.lineno,'name':node.name,'route':'','callback':'',
                'models':','.join(registered),'bases':','.join(bases),'module_scope_hint':modules,'historical_module_report':';'.join(LATEST[m]['report'] for m in modules.split(',') if m in LATEST),
                'fresh_module13_status':'NOT RUN','evidence_basis':'Fresh AST/source declaration only; runtime registration/entity lifecycle not executed by this role.'})
for p in [ROOT/'src/catalog/urls.py',ROOT/'src/config/urls.py']:
    tree=ast.parse(p.read_text(encoding='utf-8-sig'))
    for node in ast.walk(tree):
        if not isinstance(node,ast.Call) or ast.unparse(node.func) not in ['path','re_path']:continue
        if not node.args or not isinstance(node.args[0],ast.Constant) or not isinstance(node.args[0].value,str):continue
        route=node.args[0].value;callback=ast.unparse(node.args[1]) if len(node.args)>1 else '';name=next((k.value.value for k in node.keywords if k.arg=='name' and isinstance(k.value,ast.Constant)),None)
        lower=(route+' '+callback+' '+str(name)).lower()
        if 'api/drafts/' in lower:mods='01,02,03,04,05'
        elif 'api/location/' in lower:mods='01,03,06'
        elif route.startswith('account/owner/') or 'legacy_owner_section' in lower:mods='07'
        elif name in ['account_dashboard','account_profile','account_settings']:mods='07'
        elif route in ['favicon.ico','i18n/']:mods='10'
        elif name=='indexnow_key_file':mods='11'
        elif 'events/track' in lower:mods='12'
        elif 'google' in lower:mods='07';
        elif 'sitemap' in lower or 'robots' in lower:mods='11'
        elif 'notifications' in lower or 'review' in lower or 'favorite' in lower or 'like' in lower:mods='09'
        elif 'business/team' in lower or 'team' in lower or 'auth' in lower or 'deletion' in lower:mods='07'
        elif 'specialist' in lower:mods='03'
        elif 'program' in lower or 'offering' in lower or 'activity' in lower or 'pricing' in lower:mods='05'
        elif 'organization' in lower:mods='02'
        elif 'event' in lower:mods='04'
        elif 'photo' in lower or 'place' in lower and 'account/' in route:mods='01'
        elif 'map' in lower or 'catalog' in lower or 'place' in lower:mods='06'
        elif 'admin' in lower:mods='08'
        elif not route or any(s in lower for s in ['home','about','faq','contact','privacy','terms','rule','business']):mods='10'
        else:mods='UNMAPPED'
        source_inventory.append({'kind':'ROUTE_DECLARATION','source':rel(p),'line':node.lineno,'name':name or 'UNNAMED','route':route,'callback':callback,'models':'','bases':'',
            'module_scope_hint':mods,'historical_module_report':';'.join(LATEST[m]['report'] for m in mods.split(',') if m in LATEST),
            'fresh_module13_status':'NOT RUN','evidence_basis':'Fresh static route declaration only; module_scope_hint is navigation mapping, not proof endpoint was audited.'})
with (OUT/'source-coverage.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.DictWriter(f,fieldnames=list(source_inventory[0]));writer.writeheader();writer.writerows(source_inventory)
D['source_inventory_counts']=dict(Counter(r['kind'] for r in source_inventory));D['unmapped_source_declarations']=[r for r in source_inventory if r['module_scope_hint']=='UNMAPPED']
for r in D['reports']:
    folder=ROOT/Path(r['report']).parent
    p=folder/'current-snapshot.json'
    if p.exists():
        snap=json.loads(p.read_text(encoding='utf-8'));same=0;changed=[];missing=[]
        for path,expected in snap.get('source_files',{}).items():
            q=ROOT/path
            if not q.exists():missing.append(path)
            elif sha(q)==expected:same+=1
            else:changed.append(path)
        r['final_runtime_snapshot_comparison']={'snapshot':rel(p),'digest':snap.get('source_digest'),'recorded_files':len(snap.get('source_files',{})),'same':same,'changed':changed,'missing':missing}
(OUT/'historical-findings.json').write_text(json.dumps(D,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

queue_order={}
for i,ids in enumerate([
    ['SITE-QA-01','ANALYTICS-QA-01'],
    sorted(repair_ids),
    ['ORG-QA-02','ACCESS-QA-03','ACCESS-QA-02','ORG-QA-01','OFFER-QA-07'],
    ['OFFER-QA-01','OFFER-QA-02','OFFER-QA-08','PLACE-QA-03'],
    ['SPEC-QA-01','SITE-QA-06','EVENT-QA-02','MOD-QA-02','SPEC-QA-02'],
    ['SITE-QA-09','SITE-QA-10','SOCIAL-QA-09','SEO-QA-05','SEO-QA-06','SEO-QA-04'],
    ['ANALYTICS-QA-02','ANALYTICS-QA-03','ANALYTICS-QA-07','ANALYTICS-QA-04','ANALYTICS-QA-05'],
    ['PLACE-QA-06','PUBLIC-QA-03','EVENT-QA-01','SITE-QA-07','EVENT-QA-03','OFFER-QA-06','ACCESS-QA-05','ANALYTICS-QA-08','ANALYTICS-QA-06'],
    ['SOCIAL-QA-02','SOCIAL-QA-03','SOCIAL-QA-08','MOD-QA-07','SITE-QA-14','SITE-QA-15'],
]):
    for fid in ids:queue_order.setdefault(fid,i)
ordered=sorted(F,key=lambda f:(queue_order.get(f['id'],10),f['severity'],f['module'],f['id']))
queue=['# Историческая очередь repair scopes','',
       '81 исходный ID сохранён. Это очередь повторной проверки и возможных согласованных исправлений, а не 81 подтверждённый свежий OPEN. Семь PLACE ID имеют более поздний repair claim. Root module13 должен добавить свежий статус; пользователь выбирает конкретный scope до реализации. Общие причины объединены без потери исходных доказательств.','',
       '| Порядок | ID / bucket | Историческая P | Состояние | Исходный finding / готовый промпт |', '|---|---|---|---|---|']
for i,f in enumerate(ordered,1):
    status='Fresh13 FAIL: parent native proof' if f['fresh_module13_status']=='FAIL' else ('Перепроверить уже записанный repair' if f['later_repair_claim'] else 'Сначала fresh recheck, затем scoped repair')
    queue.append(f"| {i} | {f['id']} / {f['root_cause_group']} | {f['severity']} | {status} | [finding]({mdpath(f['finding'])}), [prompt]({mdpath(f['repair_prompt'])}) |")
queue+=['','Зависимости и acceptance: сначала model permissions/CSRF для глобальных записей и чтения агрегатов; затем свежая проверка repaired Place candidate/live/CAS; далее network grant/inbox controls и stale draft recovery, группы/recurring, файлы/модерация, OFF/ON и URL policy, analytics transport/failure handling, отдельный locale build и source translations, затем layout/focus/copy. Готовые prompts сохранены в исходных finding-файлах/standalone TXT; новая реализация не разрешена этим списком.','',
        'NETWORK-GRANT-UI: ORG-QA-02 + ACCESS-QA-03 один scope. COMPILED-LOCALE-FRESHNESS: PLACE-QA-06 + EVENT-QA-01 + PUBLIC-QA-03 + SITE-QA-07 один фактор сборки, но эффективный runtime профиль проверяется отдельно. EVENT-QA-03/OFFER-QA-06/ACCESS-QA-05/ANALYTICS-QA-08 — дополнительные source translation causes, не закрывать одной компиляцией.','']
(OUT/'repair-queue.md').write_text('\n'.join(queue),encoding='utf-8')

gaps=[
('13-01','02','Создать организацию без филиалов; draft/reload/submit/reject/approve','organization owner/admin','organization_workspace.py / Organization','ORG-QA-01 stale server draft; module02 historical lifecycle is not this new end-to-end path.'),
('13-02','01,02','Создать/опубликовать Place; подключить request/confirm','place owner/network owner/admin','Place / OrganizationPlaceRequest / OrganizationConnectionOperation','PLACE-QA-01…07 later repaired claim; source16 changes since modules01–09. Fresh mixed pricing+identity candidate/live and CAS mandatory.'),
('13-03','05','Программа/занятие/группы/тарифы/расписания','network/place owner/admin','Program / Activity / OfferingGroup / PricingPlan','OFFER-QA-01 absent group not archived; OFFER-QA-02 recurring controls missing; OFFER-QA-07 stale server restore.'),
('13-04','03','Предложить/подтвердить специалиста; сеть; несколько мест','person/proposer/network owner/moderator','SpecialistClaim / SpecialistEmployment / SpecialistPracticeLocation','Initial rejected-proposal correction, persisted online→both→offline toggles and max practice rows were historical NOT RUN.'),
('13-05','04','Очное Event в филиале и online Event доступного организатора','organization/person owner/admin','Event / EventOccurrenceChange','Venue rights changes previously fixture SIMULATED; fresh native revoke/affiliation relations must be established.'),
('13-06','01,02,03,04,05,08','Draft/reload/submit/reject/correct/approve/public','owner/moderator/public','VolunteerPlaceRevision vs model-specific workflows','Do not infer Event or Specialist candidate/live revision from Place workflow; rejection reasons missing in several independent templates.'),
('13-07','01,02,05,08','Опубликованный edit; две вкладки; live preservation','owner/admin/reviewer','publication.propose / ServerDraft / CAS','Published Place rebase changed. Organization autosave and stale offerings restore separate causes; distinguish genuine CAS from stale harness state.'),
('13-08','02,03,04,05,07','Detach/revoke/cooperation change/reschedule/cancel','network owner/person/employee/event owner/public','organization_detach_preview / business_team / event occurrence','Native employee revoke and invitation cancel absent (ORG-QA-02/ACCESS-QA-03); HTTP contract check is independent, not replacement UI PASS.'),
('13-09','06,10','Разделы OFF/ON: menu/direct/search/map/data','admin/public/owner','SiteVisibilitySettings / features / content_quality','SITE-QA-09 legacy temporary Place direct URL remains accessible despite events OFF; SITE-QA-10 empty410. Shared/multiworker cache NOT RUN.'),
('13-10','01,03,04,08,09,11,12','Фото/галерея/private docs/reviews/favorites/redirect/view counts','owner/reviewer/public/staff/outsider','photo/views/documents/typed_reviews/public_urls/analytics','Photo delete EVENT-QA-02; corrupt docs/images SPEC-QA-01/SITE-QA-06; dynamic favorite lifecycle and typed review redirects coverage gaps; legitimate port Origin ANALYTICS-QA-03.'),
('13-BE','all','Полная применимая backend suite','integration-reviewer','src/catalog/testcases + isolated launcher','Earlier modules targeted subsets only; several Linux donor/tmp/socket guard bodies NOT RUN on Windows; must record current full command/methods/exits.'),
('13-JS','all','Полные применимые JS suites','integration-reviewer','scripts/test_*.cjs / actual manifests','No old green result is fresh. Actual script inventory and dependencies required; keep assertions unchanged.'),
('13-UI','all','RU/AZ/EN ×360/390/768/1024/1280/1440; applicable states/keyboard/console/network','browser-qa','Native Chromium new13 stand','Historic render matrices are not current evidence; per-control exhaustive keyboard/device/browser scope remained limited.'),
('13-EXT','all','Real SDK/GA/OAuth/email/devices/Safari/Firefox/production','release/security/browser/integration','external integrations','Forbidden/disabled external credentials and production; honest NOT RUN. Local adapters/fault injection SIMULATED only.'),
('UNMAPPED-01','UNMAPPED','ConversionRun/ConversionMapping full operational lifecycle','database/integration','models/conversion.py','Historical acceptance modules do not prove conversion/recovery commands safe or tested. No cleanup or conversion write authorized.'),
('UNMAPPED-02','11','SEOAuditRun/SEOIssue/SEOChange operational audit/fix subsystem','seo/release','models/seo.py','Read/display metadata tests do not prove state-writing audit/fix commands, production indexing or rollback.'),
('UNMAPPED-03','09','Rating calibration/EmailOutbox workers and maintenance','analytics/integration','rating_ranking.py / workflow_notification.py','Ordinary social UI observations do not prove calibration admin mutations, real email worker delivery/retention.'),
('UNMAPPED-04','01,07','Location overrides/staff promotions diagnostic admin mutations','database/security/frontend-admin','location_override.py / staff_role.py','Place map/account permission tests are narrower than full override/promotion admin maintenance lifecycle.'),
]
with (OUT/'mandatory-gaps.csv').open('w',encoding='utf-8-sig',newline='') as f:
    writer=csv.writer(f);writer.writerow(['scenario','module','required_path','role','source','fresh_module13_status','reason'])
    for gid,m,path,role,source,reason in gaps:writer.writerow([gid,m,path,role,source,'NOT RUN',reason])

summary=['# Module13 — историческая сверка и coverage handoff','',
    'Роль kidsmap-orchestrator; execution identity `/root/cross_reconcile`; definition `.agents/agents/kidsmap-orchestrator/agent.md`. Дата2026-10-11. AUDIT ONLY, ownership только `reconciliation/`. Root владеет свежим стендом/браузером/итоговым решением. Приложение, rules, migrations, assertions, journal и чужие stands здесь не изменялись.','',
    '## 1. Состояние области','',
    f'Checkout `C:/kidsmap`, branch `{D["branch"]}`, HEAD `{HEAD}`; dirty WORKTREE, parent active_run `NONE`. Прочитаны13 исторических REPORT файлов (01r1/r2 +02–12), исходные finding-файлы и canonical module13 prompt. Исторические наблюдения не fresh evidence. Production UNKNOWN/NOT RUN; runtime подключений этим исполнителем не было. Явный [свежий handoff root](fresh-root-evidence.json) импортирует только три перепроверенные причины и новый root finding; native browser лично выполнял /root. [Полный inventory](historical-findings.json), [scenario/role/snapshot coverage](coverage.csv), [source route/model/admin declarations](source-coverage.csv).','',
    'Один HEAD скрывает изменение WORKTREE: у recorded manifests модулей01–10 сейчас16 изменённых файлов; у01–04 также более узкий manifest2776 без root templates, у05–10 manifest2784. Модуль10 после drift имеет отдельный final current-snapshot2788 и fresh-repeat claims в своём историческом отчёте; entry результаты не приравниваются к current. Модули11/12 recorded2788 hashes совпадают с диском, но старые фикстуры/результаты всё равно не свежая приёмка13. Подробные drift arrays сохранены в JSON.','',
    '| Модуль | Исторические IDs/P | Recorded manifest→disk | Исторический отчёт |', '|---|---|---|---|']
for m,r in LATEST.items():
    c=r['source_comparison_current'];sev=D['module_severity'].get(m,{})
    drift=f"{c['historical_files']} recorded, {len(c['changed'])} changed, {len(c['missing'])} missing"
    if r.get('final_runtime_snapshot_comparison'):drift+=f"; final {r['final_runtime_snapshot_comparison']['recorded_files']} recorded/{len(r['final_runtime_snapshot_comparison']['changed'])} changed"
    summary.append(f"| {m} {MODULE_NAMES[m]} | {sum(sev.values())}: {sev} | {drift} | [REPORT]({mdpath(r['report'])}) |")
summary+=['','## 2. Сильные стороны','',
    'Все12 областей имеют собственные dated reports, snapshot/evidence и отрицательные сценарии. Исходные IDs и repair prompts сохранены. Повторный01-r2 сохраняет пять исходных ID и добавляет два, без создания дублей. Module09 отдельно повторял MOD-QA-03 без нового SOCIAL ID. Source guard и явные NOT RUN/SIMULATED границы доступны в reports; это структура доказательств, а не текущий product PASS.','',
    '## 3. Реальные проблемы','',
    'Исторический inventory:86 finding occurrences →81 unique IDs, P0=0/P1=2/P2=67/P3=12. После объединения только проверенных одинаковых причин —77 исторических buckets. Семь PLACE-QA-01…07 имеют последующий repair claim; они не объявляются автоматически свежими OPEN или PASS. Остальные74 ID (71 buckets) исторически не имеют такого repair claim. Из явного parent handoff свежо FAIL только SITE-QA-01 P1, ANALYTICS-QA-01 P2 и общий ORG-QA-02/ACCESS-QA-03 P2; для остальных fresh status NOT RUN в этом inventory. Full current OPEN count принадлежит root итоговому отчёту.','',
    '| Проверенный общий root cause | Сохранённые IDs | Что объединяется / граница |', '|---|---|---|']
for g in groups:summary.append(f"| {g['key']} | {', '.join(g['ids'])} | {g['root_cause']} {g['dependency']} |")
summary+=['',
    'ORG-QA-02/ACCESS-QA-03 source проверен: grants/invitations строки без action controls в organization_workspace.html:462–496; JS с255 обслуживает приглашения. ACCESS-QA-02 recipient decline отдельно: другая поверхность/переход. SITE-QA-01 media write и ANALYTICS-QA-01 statistics read имеют похожий missing-model-permission pattern, но разные custom admin handlers, scopes и acceptance; их IDs не объединены.','',
    'Compiled freshness объединяет environment фактор, не все переводы. EVENT-QA-03/OFFER-QA-06/ACCESS-QA-05/ANALYTICS-QA-08 дополнительно содержат source missing/fuzzy/wrong meanings. PLACE-QA-06 later repair — isolated build helper, не массовая замена shared ignored MO. Effective locale profile нужен в каждом свежем результате. Дополнительно выполнен [свежий direct asset readback](current-shared-locale-readback.json): shared ignored MO сверены с PO через GNUTranslations без Django.setup/DB/locale writes. Это asset/source evidence, не rendered browser или attestation effective root LOCALE_PATHS.','',
    'Все81 finding и исходные links/prompts: [repair queue](repair-queue.md), JSON включает evidence_links/source/dependencies/severity и SHA исторических файлов. Новые CROSS-QA IDs этим исполнителем не назначаются. Parent передал новый CROSS-QA-01 P2: после native будущего переноса Event остаётся на своей карточке/в общей афише, но исчезает из feed организатора; root оформляет отдельный finding/prompt.','',
    '| Fresh parent scenario | Роль/язык/ширина | Результат/доказательство |', '|---|---|---|']
for r in parent_proof['rows']:
    shot=f", [PNG]({mdpath(r['screenshot'])})" if r.get('screenshot') else ''
    summary.append(f"| {r['scenario']} | {r['role']}/{r['lang']}/{r['width']} | {r['status']}: [row{r['evidence_row']}]({mdpath(r['evidence'])}){shot} |")
summary+=['',
    '## 4. Tech debt','',
    'Исторические matrix schemas отличаются: module04 разделяет geometry/document-language и copy_status вместо одного status; module07 хранит observations/not_run; module10 строки с entry/current snapshot. Coverage CSV сохраняет исходный status в отдельной колонке, fresh_module13_status всегда NOT RUN в этом support scope. Counts не суммируются в количество уникальных transactions/tests.','',
    'Source map охватывает static declarations моделей (включая abstract/proxy candidates), явные admin.register decorators и path/re_path calls. Это navigation mapping, не runtime app registry/доказательство coverage каждого endpoint. Dynamic ORM, proxy replacement registration и settings gates требуют root native/source подтверждения.','',
    '## 5. Risks','',
    'Исторический SITE-QA-01 P1 global logo upload/delete без model permission важнее layout polish. PLACE-QA-03 P1 имеет более позднее исправление в грязном WORKTREE: publication.propose:355–369 содержит scalar projection rebase; root обязан воспроизвести mixed price+identity→submit→approve, CAS и live preservation на новом стенде. Само наличие patch не PASS.','',
    'Граф C-kidsmap callable/ready, но cited paths coverage_unavailable/partial и metadata_changed, recorded metadata truncated. Бounded source fallback использован. ajax_upload inbound trace дал0callers, однако site.py:get_urls явным образом подключает handler через admin_view; нулевой graph trace не доказательство dead code. [Компактные graph bounds](graph-summary.json). Реальные SDK/GA/SMTP/OAuth и production не использованы.','',
    '## 6. Dead/legacy candidates','',
    'STATUS UNKNOWN/ACTIVE; удаление не предлагается. Legacy scalar pricing, temporary Place, readonly diagnostic admins, conversion/SEO metadata models и compatibility facades не объявлены dead. Coverage gaps в conversion/SEO audit writes не являются дефектом или основанием удалить model/table. DB/data/deletion audit NOT RUN.','',
    '## 7. Tests gaps','',
    f"В этом support scope выполнены document inventory, SHA drift comparison, AST declarations, direct assets readback и bounded source review. Собственных backend/JS/browser lifecycle tests нет: NOT RUN;7 явно импортированных parent native rows имеют6FAIL/1NOTRUN, атрибуция сохранена. Coverage CSV имеет{len(coverage)} записей: {dict(Counter(r['record_kind'] for r in coverage))}; исторические строки fresh_module13_status NOT RUN. [18 обязательных сценариев/внешних/операционных gaps](mandatory-gaps.csv) остаются checklist, их полный результат root ведёт отдельно.",'',
    'Команды: `.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/reconciliation/inventory.py`; `.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/reconciliation/asset_readback.py`; `.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/reconciliation/assemble.py`; source reads `rg`/PowerShell Get-Content и Codebase Memory list_projects/index_status/get_architecture/search_graph/trace_path/check_index_coverage. Native script exits/artifact validation отдельно в [command-results.json](command-results.json) после проверки. Ранний ad-hoc metadata-print attempt имел собственный IndexError при поиске отсутствующего module04 matrix.json (там CSV), assemble first attempt — QA parser list/dict mismatch ([attempt](assemble.attempt1.json)); они не считаются app/test failures и не поддерживают findings.','',
    'Исторические обязательные ограничения: full suites ранее не запускались; Windows donor/socket/tmp preflight bodies зачастую NOT RUN; native employee revoke/role/cancel и recipient decline отсутствуют; полный Specialist author rejected proposal correction/все practice permutations не установлены; exact recurring group positive blocked; real device/engine/screenreader/multiworker cache/real integrations не проверены. Root должен продолжить независимые проверки, а blocked переходы оставить NOT RUN с доказанной причиной.','',
    '## 8. Recommendations','',
    'Порядок: (1) fresh SITE-QA-01 permission boundary + отдельный ANALYTICS-QA-01; (2) fresh repaired PLACE01–07 в фактическом locale profile, особенно pricing candidate/CAS; (3) canonical network request/confirm, employee controls/recipient decline, organization autosave и stale offerings restore; (4) group removal/recurring/moderation; (5) files/private docs/primary delete/photo moderation; (6) OFF/ON/direct legacy URL, review pagination, slug aliases/sitemap/SEO editor; (7) analytics origin/failure handling; (8) build freshness и отдельно source translations; (9) geometry/focus/copy. Исходные самостоятельные prompts linked в repair queue. Перед любым исправлением нужен конкретный user-approved scope.','',
    'Named handoff: `/root` kidsmap-orchestrator — соединить inventory с собственными fresh module13 rows без автоматического наследования PASS/OPEN; django-reviewer — disputed workflow/permission rules; integration-reviewer — full isolated suites/Windows guards; browser-qa lead — ten-step native pipeline и18 cells. Acceptance: каждый fresh статус имеет новый snapshot/result/PNG или честный NOT RUN; оригинальные IDs не потеряны.','',
    '## 9. P0/P1/P2/P3','',
    'Исторические unique IDs: P0=0, P1=2, P2=67, P3=12; repaired claim7 (1P1/5P2/1P3), remaining historical unresolved claims74 (1P1/62P2/11P3). Это не новый current defect count. Ограниченный свежий parent handoff:1P1/2P2 historical root causes (4IDs), плюс новый parent CROSS-QA-01 P2. Остальные не повышены до OPEN/PASS по истории. Общий project PASS и production readiness не заявляются.','']
(OUT/'REPORT.md').write_text('\n'.join(summary),encoding='utf-8')
print(json.dumps({'coverage_rows':len(coverage),'coverage_kinds':D['coverage_kinds'],'source_inventory':D['source_inventory_counts'],'unmapped_source':len(D['unmapped_source_declarations']),'unique_historical_ids':len(F),'root_cause_buckets':D['historical_root_cause_bucket_count'],'later_repair_claims':7,'historical_unresolved_ids':D['historical_unresolved_ids_count'],'historical_unresolved_buckets':D['historical_unresolved_bucket_count']},ensure_ascii=False))
