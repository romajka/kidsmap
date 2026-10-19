import json,hashlib,shutil,re,urllib.request
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module13-repair-2026-10-19-pc-r1';Q=R/'.tmp/m13-full-r1';read=lambda p:json.loads(p.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
backend=read(O/'evidence/qa04-r5-backend.json');discovery=read(O/'evidence/discovery-current.json');assert backend['exit']==0 and not backend['failures'] and not backend['errors'] and backend['unique_methods']==2626 and set(backend['ids'])==set(discovery['exhaustive']['ids'])
current=read(O/'source-current.json')['sources'];assert current==read(R/'.tmp/m13-qa04-r5/profile/source-entry.json')['sources'] and all(sha(R/p)==h for p,h in current.items())
assert read(O/'evidence/node-final.json')['exit']==0 and read(O/'evidence/node-final.json')['TAP_counts']['pass']=='129';assert read(O/'evidence/python-final.json')['exit']==0 and read(O/'evidence/python-windows-locales-final.json')['exit']==0
assert read(O/'evidence/preservation.json')['original_assertion_count']==225 and read(O/'evidence/ci-structure.json')['deploy_job_byte_identical']
names=['browser-event-green-r2','browser-online-event-r3','browser-organization-flow-r3','browser-program-publish','browser-linked-offering','browser-event-lifecycle-r2','browser-cooperation','browser-employee-revoke-r2','browser-specialist-proposal-r2','browser-private-documents-r2','browser-final-public','browser-district-recheck','browser-partial-batch','browser-feature-toggles-r2','browser-native-claim-r3','browser-invitation-recovery','browser-favorite-head','browser-detach-freeze','browser-final-captures'];native=[]
for name in names:
 d=read(O/'evidence'/(name+'.json'));assert not any(d.get(k) for k in ['error','errors','pageerrors','consoleRows']),name
 checks=[v for row in d['rows'] for v in row.get('checks',{}).values()];assert checks and all(v is True for v in checks),name;native.append({'artifact':'evidence/'+name+'.json','rows':len(d['rows']),'checks':len(checks),'PASS':len(checks),'FAIL':0})
stock=read(O/'evidence/stock-browser-scripts.json');assert stock[2]['exit']==0 and read(O/'evidence/stock-review-submission-r2.json')['exit']==0 and read(O/'evidence/stock-urls-r2.json')['exit']==0
for file in (Q/'stock-screenshots').glob('*.png'):shutil.copyfile(file,O/'png'/('stock-'+file.name))
shutil.copyfile(R/'.tmp/m13-qa04-r5/profile/attestation.json',O/'evidence/final-quality-attestation.json');shutil.copyfile(R/'.tmp/m13-qa04-r5/locales/manifest.json',O/'evidence/final-quality-locale-manifest.json');shutil.copyfile(Q/'locales-current/manifest.json',O/'evidence/final-native-locale-manifest.json')
with urllib.request.urlopen('http://127.0.0.1:33810/qa/m13/state/',timeout=10) as response:state=json.loads(response.read())
with urllib.request.urlopen('http://127.0.0.1:33810/qa/m13/cross/',timeout=10) as response:cross=json.loads(response.read())
assert all(state['flags'].values()) and cross['place']['organization_id'] is None and cross['program']['activities']==0 and cross['organization']['branches']==1 and read(Q/'simulation.json')=={'report':'disabled','storage':'healthy'}
(O/'evidence/fixture-final-summary.json').write_text(json.dumps({'synthetic_only':True,'all_original_flags_ON':True,'selected_branch_detached':True,'other_branch_remains_connected':True,'shared_program_no_longer_drives_frozen_activity':True,'private_documents_actual_native_ACL':'33checksPASS','own_media_files':len(state['media']),'analytics_event_count':state['events_total'],'no_history_reset':True,'initial_four_historical_analytics_rows':'Explicit synthetic setup inherited fixture design; not production history','simulation':read(Q/'simulation.json'),'source':'Own loopback read-only aggregate helpers, no user rows or identity hashes exported'},indent=2))
v={'status':'PASS LOCAL Module13 within documented scope','primary_historical_findings':{'CROSS-QA-01':'CLOSED LOCAL','CROSS-QA-02':'CLOSED LOCAL','CROSS-QA-03':'ALREADY CLOSED PLACE-QA-08; fresh54checksPASS'},'related_quality_findings':{'CROSS-QA-04':'CLOSED LOCAL supported actual QA04 resources, no guard weakening','CROSS-QA-05':'CLOSED LOCAL fixture maintenance;225 existing assertions identical','CROSS-QA-06':'CLOSED LOCAL LF portability'},'confirmed_OPEN':0,'backend_unique_methods':2626,'backend_exit':0,'backend_failures':0,'backend_errors':0,'backend_full_source_files':len(current),'js_TAP_pass':129,'js_TAP_fail':0,'python_linux':{'run':21,'pass':20,'skip':1},'python_windows_locales':{'run':9,'pass':9},'python_unique_methods_covered_across_platforms':21,'native':native,'native_rows':sum(x['rows'] for x in native),'native_checks':sum(x['checks'] for x in native),'stock_native_scripts':3,'source_files':len(current),'changed_or_added_source_files':14,'new_source_files':5,'prior_packages':44,'prior_files':9905,'original_assertions_preserved':225,'production_GitHub_external_integrations':'NOT RUN','commits_push_deploy':'NOT RUN','independent_specialists':'Not claimed; root sequential execution'}
(O/'verification.json').write_text(json.dumps(v,ensure_ascii=False,indent=2))
rows=[('CROSS-QA-01','P2','CLOSED LOCAL','Future rescheduled published events remain in organization; private/cancelled/past exclusions preserved.'),('CROSS-QA-02','P2','CLOSED LOCAL','Canonical complete discovery: no-label/manage.main/full wrapper/exhaustive IDs agree; CI full supported profile.'),('CROSS-QA-03','P3','ALREADY CLOSED LOCAL','Existing PLACE-QA-08 active RU translation verified fresh; no duplicate PO edit.'),('CROSS-QA-04','P2','CLOSED LOCAL','Actual dedicated QA04 role/database/socket/current locales; all42 formerly unavailable guard/helper bodies ran.'),('CROSS-QA-05','P2','CLOSED LOCAL','Three stale Django fixtures and platform-specific compiler fixture corrected with225 unchanged assertions.'),('CROSS-QA-06','P3','CLOSED LOCAL','Bash LF attributes + two actual entrypoints normalized; original synthetic backup assertions pass.')]
(O/'FINDINGS.md').write_text('# Module13 finding ledger\n\n| ID | Priority | Final local state | Evidence/result |\n|---|---|---|---|\n'+''.join('| '+' | '.join(row)+' |\n' for row in rows)+'\nCROSS04–06 are related quality-gate causes under CROSS02, not three new business modules. Historical raw45 failures/errors remain in full-backend-r1.json; final full r5 runs every method successfully. No source/model/schema deletion.\n')
modules=read(O/'evidence/module01-12-report-index.json');assert all(x['exists'] for x in modules)
table='| Модуль | Последнее локальное решение |\n|---|---|\n'+''.join('| '+str(x['module'])+' | [REPORT](../'+Path(x['report']).parent.name+'/REPORT.md), LOCAL в описанных границах |\n' for x in modules)
report=f'''# Модуль13 — финальная межмодульная проверка

2026-10-19, C:\\kidsmap. Root, последовательная проверка исходников, backend, CI и native Chromium; независимые специалисты не запускались. Пользователь разрешил следующий модуль целиком с исправлением подтверждённых связанных проблем. **Модуль13 завершён LOCAL в проверенном контуре. Подтверждённых OPEN:0. Production и глобальный release PASS не объявляются.**

## 1. Состояние области
HEAD852938d96764ae315b92859e3651e5ea62054a36, branch codex/module09-transfer-2026-10-16-r1 +dirty WORKTREE; active_run NONE. HEAD, refs, index и пустой staging сохранены. [Исходный срез](source-entry.json), [дополнение3 ранее не включённых CI/shell файлов до первого изменения](source-supplemental-entry.json), [итог1074источника/14изменённых или добавленных](source-current.json), [полный diff](application.diff).

Сверены последние модульные решения01–12, включая финальный SOCIAL12 вместо раннего OPEN09. Их исторические counts не суммируются и не выдаются за новые. Изменённые пересечения проверены заново; итоговый полный backend выполняет текущие бизнес-тесты всех модулей.

{table}

## 2. Что работает
Полный свежий PostgreSQL прогон: **2626 уникальных методов,0FAIL/0ERROR**,1359.753s, exit0. Django check и migration drift PASS. [Точная команда и IDs](evidence/qa04-r5-backend.json), [реальные изолированные ресурсы](evidence/qa04-r5-setup.json), [проверка фактического Unix-сокета/роли/БД](evidence/final-quality-attestation.json). App и PostgreSQL не имеют внешней сети. Новые реальные QA04 ресурсы удовлетворяют исходным guard-контрактам; существующие guards не изменялись и исторический стенд не подменялся.

Node24/jsdom29.1.1: **129TAP PASS/0FAIL**. Linux Python:20PASS/1Windows-onlySKIP из21; текущая Windows-ветка locale suite:9PASS, включая пропущенную на Linux junction-проверку. Вместе покрыт21 уникальный Python-метод. Все3 аутентифицированных stock browser scripts также прошли отдельно: URL preview, review submission и3-second cooldown. [Node](evidence/node-final.json), [Python](evidence/python-final.json), [Windows](evidence/python-windows-locales-final.json), [stock](evidence/stock-browser-scripts.json), [review final](evidence/stock-review-submission-r2.json), [URLs final](evidence/stock-urls-r2.json).

Принятые новые native suites: **{v['native_rows']}строк/{v['native_checks']}проверок**, всеPASS; это наблюдения, не число уникальных пользовательских сценариев. RU/AZ/EN, responsive Chromium360/390/768/1024/1280/1440. Публичная матрица108строк/756проверок; OFF/ON74строки/313проверок; остальные артефакты и точные counts — [verification.json](verification.json). Фиктивный role-login обозначен как QA helper; изменения моделей выполнялись настоящими формами, подтверждениями и модерацией.

## 3. Подтверждённые причины и исправления
Перенесённое будущее опубликованное событие выпадало из организации из-за scheduled-only фильтра. Теперь допустимы scheduled/rescheduled при прежних publication/deleted/date ограничениях. PostgreSQL и native UI подтверждают очное и онлайн событие, повторный перенос, stale cancel, отмену, прежний URL и честное состояние.

No-label CI раньше видел618 из2619 методов входного WORKTREE. Теперь real manage.main, wrapper full и полный inventory согласованы на2626; различий и дубликатов нет. Чистый HEAD-source donor:618/2207/2347 для no-label/catalog/full. Текущий tracked корпус2347, ещё279методов находятся в локальных untracked файлах. Они появятся в удалённом корпусе только после отдельной Git-публикации; actual GitHub NOT RUN. [Сверка](evidence/discovery-reconciliation.json).

Полное обнаружение выявило45 старых отказов:17schema guards,15conversion guards,10отсутствующих внешних helper-зависимостей и3несовместимые Django fixture assumptions. Подготовлен безопасный Linux quality entrypoint и CI-профиль с настоящим PostgreSQL/socket, текущими изолированными MO и очищенным окружением. Три Django-фикстуры получили объявленные виртуальные hosts, корректного кандидата/версию отзыва и Category после transaction flush; compiler fixture выбирает WSL на Windows и native GNU на POSIX. **225 существующих assertions сохранены AST-эквивалентно**, остальные прежние test bytes неизменны. [Планы](QUALITY_PROFILE_PLAN.md), [доказательство](evidence/all-existing-assertions-preserved.json).

Два Bash entrypoint имели CRLF; это ломало wrapper и давало ложные отрицательные backup controls. Теперь LF и .gitattributes; реальные backups не запускались — только исходные тесты с synthetic mock transport. Deploy-job byte-identical, quality dependency сохранена, continue-on-error отсутствует. [CI structure](evidence/ci-structure.json), [ledger](FINDINGS.md).

## 4. Межмодульные контракты
Native пройден путь: организация без филиалов → публикация места → canonical preview/consent/confirm → общая программа → занятие/группа/цена/расписание → раздельная модерация. Проверены mixed batch с other-network conflict/no-op/новым запросом и отдельное согласие второго владельца; stale two-tab ввод сохраняется. Специалист предложен, claim отклонён/повторён/подтверждён staff, профиль исправлен после отказа и опубликован с двумя местами приёма. Сотрудничество с сетью требует двух согласий и отзывается независимо от person rights; private documents прошли33 ACL/file/consent проверки.

Роль/доступ сотрудника изменены и отозваны через UI, отдельный Place-grant сохранился. Отвязка выбранного филиала оставляет другие связи; общая программа замораживается в занятии. После последующего одобрения нового общего текста старое занятие сохраняет прежний текст,20AZN и16:00; явный организатор события и избранное остаются. OFF/ON не меняет данные/медиа. HEAD не добавляет analytics. Phone/privacy/SEO/permissions/backend regression входят в полный2626 corpus; реальные GA/OAuth/Maps/SMTP не вызывались.

## 5. Риски и сохранность
Сохранены44предыдущих пакета/9905файлов, shared MO, .cbmignore, Git refs/index и active_run. Неожиданных source changes нет; добавлено5файлов, поддержано9существующих. Один чужой standby m10s01-plan-r1-app завершил собственный sleep86400 с exit0/OOMfalse; CID сохранён, задача его не останавливала и не перезапускала. Это документированное естественное истечение, а не утверждение непрерывности всех старых HTTP. [Preservation](evidence/preservation.json), [transition](evidence/foreign-runtime-transitions.json).

## 6. Legacy и технический долг
Ничего не удалено. Совместимый test_catalog bridge и scoped labels сохранены; canonical full принадлежит KidsMapTestRunner. Конвертация остаётся fail-closed и требует реального disposable QA04 профиля. Codebase Memory использован первым; индекс2026-10-16ready, coverage_unavailable/metadata_changed на18релевантных путях. Graph — подсказки; выводы проверены по source/routes/ORM. [Coverage](evidence/graph-coverage.json). Негативный graph result не использован для удаления или изменения схемы.

## 7. Границы проверки
Это локальная межмодульная приёмка на вымышленных данных с изолированными DB/cache/media/private/email. Native проверки используют Chromium responsive viewports; настоящие телефоны/планшеты, Safari/Firefox и полный screen-reader audit NOT RUN. Проверен sample keyboard/focus и stock review keyboard, не каждый контроль во всех комбинациях. Сохранены предыдущие полные модульные acceptance boundaries; не заявляется новый полный визуальный аудит каждого неизменившегося поля01–12.

Actual GitHub execution, commit/push/deploy, production, реальные Google OAuth/GA/Maps/SMTP/IndexNow и внешняя индексация NOT RUN. Simulated503/500/network/malformed/expiry случаи обозначены в соответствующих сценариях. Первые observer/fixture/profile failures сохранены; они не входят в принятые native counts. Изображения фиктивные; manual visual review выборочный, стабильные финальные captures имеют prefix final-capture-.

## 8. Рекомендации и воспроизводимость
Для нового Linux quality run использовать scripts/run_isolated_quality.py с новым настоящим QA04 PostgreSQL/socket; готовая provision последовательность находится в quality-job workflow. Команда не читает credentials и не создаёт/останавливает контейнеры. [Запуск и ограничения](TESTING.md). Текущий отчёт и manifest проверяются read-only verify_artifacts.py; старые локальные PID/порты/имена — provenance, не параметры нового стенда. Сначала отдельно подготовить Git-пакет всех разрешённых изменений и untracked тестов; публикация и release потребуют отдельной задачи.

## 9. P0/P1/P2/P3
В проверенном локальном scope подтверждённых открытых P0/P1/P2/P3:0. CROSS01/02 и связанные04–06 CLOSED LOCAL. CROSS03 уже исправлен PLACE-QA-08 и перепроверен54native checks. Это не production release approval и не скрытие NOT RUN границ.
'''
(O/'REPORT.md').write_text(report)
(O/'TESTING.md').write_text('''# Module13 quality execution

Canonical complete discovery: KidsMapTestRunner with no labels. Explicit labels/patterns remain scoped. scripts/run_kidsmap_tests.sh full delegates to the same no-label manage.py test; use only with an explicitly isolated testing profile, never credentials from a deployment environment.

Linux CI provisions a fresh qa_stage04 PostgreSQL and real Unix socket, then runs:

    python scripts/run_isolated_quality.py --profile-root "$QUALITY_PROFILE_ROOT" --socket-dir "$QUALITY_SOCKET_DIR"

The root must be a new /tmp/kidsmap-task33-qa04-* directory. Socket directory must actually be checkout .tmp/kidsmap-task33-qa04-socket-*/socket. The official image keeps /var/run/postgresql for its bootstrap and adds the mounted socket; TCP and container network are disabled. The CLI verifies actual socket/server/database/role, clears inherited env, compiles current PO into a fresh checkout .tmp descendant, supplies strict historical guard helper, checks migrations/system and runs all methods sequentially. Existing guards and business assertions are unchanged. A new PostgreSQL instance is required; retained test DBs are evidence, not a reset target.

Local execution used the exact CLI in dedicated network-none app/PG containers with current-source RO mount and separate own socket/data/profile/locale storage. See evidence/qa04-r5-setup.json and qa04-r5-backend.json for actual IDs/args. Do not reuse their historical paths on another computer. Raw logs/private synthetic cookie configs are ignored scratch and are intentionally absent from the artifact package.

CI additionally runs original standalone Python and Node unit/DOM checks. The3 fixture-authenticated browser scripts have separate explicit native configurations; they are excluded by name from unit-only invocation and were executed successfully in this local acceptance. YAML/Bash syntax and deploy preservation were verified locally; actual GitHub execution remains NOT RUN.
''')
for p in [O/'IMPLEMENTATION_PLAN.md',O/'QUALITY_PROFILE_PLAN.md']:p.write_text(p.read_text().replace('- [ ]','- [x]'))
(O/'PROGRESS.md').write_text('Module13 CLOSED LOCAL. Backend2626/0F0E, JS129/0F, Python21unique across Linux/Windows, native'+str(v['native_checks'])+'checksPASS. Reports/ledger complete; source/previous packages preserved; seal/verify is final read-only step.\n')
# Guarded append to canonical decision documents, preserving every original byte.
append_records={};documents=read(O/'document-current.json')
for relative,heading in [('docs/qa/continuation-and-repair-prompts-2026-10-11.md','## Module13 repaired and accepted LOCAL — 2026-10-19 pc-r1'),('docs/agent-audits/MASTER_AUDIT.md','## Module13 final cross-module acceptance LOCAL — 2026-10-19 pc-r1')]:
 p=R/relative;before=p.read_bytes();assert hashlib.sha256(before).hexdigest()==documents[relative] and heading.encode() not in before
 text='\n\n'+heading+'\n\nМодуль13 завершён LOCAL в проверенном scope: CROSS01/02 и связанные quality04–06 закрыты; CROSS03 уже PLACE-QA-08, свежие54nativePASS. Полный текущий PostgreSQL корпус2626уникальных методов/0FAIL/0ERROR; Node129PASS, Python21unique across Linux/Windows;225existing assertions preserved. Native'+str(v['native_rows'])+'rows/'+str(v['native_checks'])+'checksPASS плюс3stock scripts. Discovery no-label/manage/full/exhaustive IDs согласованы; tracked2347 +localuntracked279. Production/GitHub/commit/push/deploy NOT RUN. [REPORT](../qa/module13-repair-2026-10-19-pc-r1/REPORT.md), [verification](../qa/module13-repair-2026-10-19-pc-r1/verification.json). Предыдущие44пакета/9905файлов сохранены; один standby86400s истёк естественно, CID сохранён.\n'
 if relative.startswith('docs/qa/'):text=text.replace('../qa/module13-repair','module13-repair')
 with p.open('ab') as f:f.write(text.encode())
 assert p.read_bytes()[:len(before)]==before
 append_records[relative]={'original_prefix_length':len(before),'original_prefix_sha256':hashlib.sha256(before).hexdigest(),'final_sha256':sha(p)};documents[relative]=sha(p)
(O/'document-current.json').write_text(json.dumps(documents,indent=2));(O/'evidence/document-appends.json').write_text(json.dumps(append_records,indent=2))
for p in sorted((R/'.tmp').glob('m13-*.py')):shutil.copyfile(p,O/'execution-scripts'/p.name)
for name in ['runtime.py','qa_settings.py','qa_urls.py','qa_simulation.py','stage_apply.py','apply-native.ps1','proxy.py','playwright.json','seed.py','seed-extra.py']:
 shutil.copyfile(Q/name,O/'execution-scripts'/name)
print(json.dumps({'status':v['status'],'backend':2626,'native_rows':v['native_rows'],'native_checks':v['native_checks'],'confirmed_OPEN':0,'source_files':len(current)},indent=2))
