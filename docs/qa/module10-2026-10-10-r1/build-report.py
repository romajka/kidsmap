"""Aggregate only fresh QA10 evidence, classify harness attempts, write assigned reports."""
from pathlib import Path
import json,collections,csv,hashlib,datetime,sys,re,runpy,struct,urllib.request
sys.stdout.reconfigure(encoding='utf-8');P=Path(__file__).resolve().parent;R=P.parents[2]
F=runpy.run_path(str(P/'finding-data.py'))['FINDINGS']
for f in F:
 current=['current-concurrency.result.txt'] if f['id']=='SITE-QA-15' else ['current-boundary.result.txt'] if f['id'] in ['SITE-QA-01','SITE-QA-06','SITE-QA-09','SITE-QA-10','SITE-QA-12'] else ['current-focus.result.txt'] if f['id'] in ['SITE-QA-11','SITE-QA-13'] else ['current-network.result.txt'] if f['id']=='SITE-QA-14' else ['current-matrix.result.txt','current-settings.result.txt']
 f['evidence']+=current
 f['current_snapshot_note']='Supplemental native process8825/8826 started from current-snapshot.json after recorded foreign source drift. Module10 relevant handlers/templates/MO remain unchanged; own reports preserve entry evidence. SITE-QA-01 current recheck is GET only; upload/delete proof earlier, identical handler hashes, no new security mutation.'
def dump(name,data): (P/name).write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding='utf-8')
datasets={}
for name in ['matrix-empty','settings','matrix-filled','flags','acl','keyboard','media-errors','finish','faq-proof','modal-proof','organization-proof','network-proof','visual-final','focus-proof','current-settings','current-matrix','current-focus','current-boundary','current-pages','current-network','current-console','current-concurrency']:
 datasets[name]=json.loads((P/(name+'.result.txt')).read_text(encoding='utf-8'))
changes=[{'evidence':name+'.result.txt',**x} for name,d in datasets.items() for x in d.get('changes',[])]
dump('settings-changes.json',{'settings_edits':changes,'other_initial_fixtures':['seed.py','extra-fixtures.py (temporary Place6)','lawful-fixtures.py (verified person Spec2/resolved Event2)','owned-organization.py (admin-owned Organization2)'],'non_settings_native_change':'Organization2 name_az saved as draft under OFF; live unchanged; organization-readback.json','security_negative_writes':'acl.js direct negative HTTP upload/delete with CSRF only in own DB; admin native restore','final_state_notes':'Section flags ON, public favorites OFF threshold1, home EN title restored, valid fictional logo restored. Other synthetic text/footer/image settings intentionally remain for review.'})
matrix=[];excluded=[]
for name,d in datasets.items():
 for i,r0 in enumerate(d.get('rows',[])):
  r={'evidence':name+'.result.txt','evidence_row':i+1,'snapshot':'current-snapshot.json' if name.startswith('current-') else 'snapshot.json',**r0};s=r['scenario'];why=None
  if name in ['matrix-filled','focus-proof','network-proof']:why='SUPERSEDED CURRENT WORKTREE: supplemental fresh current runtime repeats this dataset after recorded foreign source drift; entry evidence retained.'
  if name=='settings' and r['status']=='FAIL':why='HARNESS: expectation kept trailing spaces; Django strips CharFields; final trimmed readback passes.'
  if name=='flags' and s=='flag-admin-edit-preserved' and r.get('kind')=='organization':why='HARNESS: tested wrong submit button and administrator without organization.edit business entitlement; final Organization2 UI save/reload passes.'
  if name=='flags' and s in ['flag-owner-specialist','flag-owner-event'] and r['status']=='FAIL':why='HARNESS: legacy unresolved/unverified initial fixtures correctly denied; final lawful verified Spec2/resolved Event2 passes OFF/ON.'
  if name=='keyboard' and s in ['faq-keyboard-enter','faq-keyboard-space']:why='SUPERSEDED: final native FAQ waits for 320/260ms animation; 36/36 fresh checks PASS.'
  if name=='media-errors' and s in ['delete-dialog-keyboard-trap','delete-dialog-escape-preserves-file']:why='SUPERSEDED: final foreground focus/escape proof includes wait1250/450ms; focus FAIL, Escape PASS.'
  if name=='finish' and (s=='organization-custom-editor-available' or s=='aborted-settings-input-recovery'):why='SUPERSEDED: lawful Organization2 native proof and independent network history proof.'
  if name=='modal-proof':why='CORROBORATING: final foreground focus-proof used in acceptance counts; this independent trace retained.'
  if name=='finish' and s=='lawful-owner-flag-event' and r.get('enabled'):
   r.update(status='NOT RUN',raw_status=r0['status'],classification='HTTP200 after expected published Event edit redirect to account/places is not an editable-form proof. Feature guard OFF404 passed; native management form lifecycle NOT RUN.')
  if why:excluded.append({**r,'disposition':why});continue
  if name=='matrix-empty' and r['status']=='FAIL':r.update(status='NOT RUN',raw_status='FAIL',classification='ENVIRONMENT: DEBUG=True diagnostic 404, excluded from application decision; DEBUG=False fresh proof in keyboard.')
  if name=='keyboard' and s=='200-percent-zoom-no-document-overflow':r.update(status='NOT RUN',raw_status=r0['status'],classification='SIMULATED CSS zoom2 diagnostic only; real Chrome 200% zoom NOT RUN.')
  if name=='current-settings' and r['status']=='FAIL':excluded.append({**r,'disposition':'HARNESS: retained trailing-space expectation in copied initial settings script; existing trimmed readback and current matrix fields validate stored strings.'});continue
  if name=='current-pages' and s=='current-shared-page-js-console' and r['status']=='FAIL' and not r.get('errors') and all(x=='Failed to load resource: net::ERR_FAILED' for x in r.get('consoleErrors',[])):
   r.update(status='NOT RUN',raw_status='FAIL',classification='ENVIRONMENT / SIMULATED: own route blocks unpkg Leaflet/MarkerCluster CSS; independent current-console proof records exact requestfailed and console locations. Local asset responses and JS exceptions separately passed. External resource loading NOT RUN.')
  matrix.append(r)
gaps=[('two-tab-conflict-and-repeat-save','admin','Two simultaneous native settings writes/stale conflict and duplicate submit replay NOT RUN.'),('real-browser-200-percent-zoom','guest','Only CSS zoom2 diagnostic; real browser chrome zoom NOT RUN.'),('real-disconnect-server-error-retry','admin','Only browser abort before server SIMULATED; actual disconnect/server500/retry preservation NOT RUN.'),('complete-admin-hidden-spec-event-save','admin','Hidden admin editors checked available; full native domain save cycle for Specialist/Event under OFF NOT RUN; Organization save/reload executed.'),('full-pixel-contrast-audit','guest','Native contacts H1 solid colors sampled PASS; all text, background-image composition, focus/disabled contrast and automated WCAG full audit NOT RUN.'),('current-snapshot-full-empty-default-repeat','guest','Initial empty/default variant matrix executed on entry runtime, not completely repeated after foreign drift. Current filled/settings/general pages rechecked; exact initial final-snapshot variants NOT RUN.'),('current-snapshot-full-language-menu-loop-repeat','guest','Initial native menus/language query-preservation loop passed on entry runtime; full loop not repeated after foreign drift. Relevant module10 source hashes unchanged, final-snapshot full loop NOT RUN.')]
gaps=[(s,r,'Native two-tab lost update and dblclick executed current RU1440; other language/width combinations NOT RUN.') if s=='two-tab-conflict-and-repeat-save' else (s,r,t) for s,r,t in gaps]
for scenario,role,reason in gaps:
 for lang in ['ru','az','en']:
  for width in [360,390,768,1024,1280,1440]:
   if scenario=='two-tab-conflict-and-repeat-save' and lang=='ru' and width==1440:continue
   if scenario=='two-tab-conflict-and-repeat-save':reason='Native two-tab lost-update + dblclick executed current RU1440; other language/width combinations NOT RUN.'
   matrix.append({'scenario':scenario,'status':'NOT RUN','role':role,'lang':lang,'width':width,'url':'','shot':'','reason':reason,'evidence':'coverage-gaps.json'})
for scenario,reason in [('production-and-external-integrations','Production/real Maps SDK, OAuth, analytics, email deliveries, external social/contact links NOT RUN; external transports blocked.'),('shared-cache-invalidation','Redis/multiworker cache propagation NOT RUN; current own LocMem native save→same-process reload/public executed.'),('full-test-suites','Complete Django/JS suites, CI and all browsers NOT RUN; selected unchanged tests only.'),('unpublish-archive-delete-native-lifecycle','Status/active/archive/deleted fixtures are initial data, not native transitions; full UI publication/archive/delete lifecycle belongs other modules and is NOT RUN here.'),('unsupported-500-403-render-matrix','Generic DEBUG=False404 rendered; deliberate server500 and complete role403 shared-template matrix NOT RUN.')]:matrix.append({'scenario':scenario,'status':'NOT RUN','role':'all','lang':'all','width':'all','reason':reason,'evidence':'coverage-gaps.json'})
dump('coverage-gaps.json',{'gaps':gaps,'limitations':'Every NOT RUN is explicit in matrix. An initial published/archived/deleted fixture does not prove its UI transition. CSS zoom is not browser chrome zoom. Source inspection is not browser evidence.'})
dump('matrix.json',matrix);dump('excluded-observations.json',excluded)
cols=['scenario','status','role','lang','width','url','shot','evidence','evidence_row','snapshot','classification','reason']
with (P/'matrix.csv').open('w',encoding='utf-8-sig',newline='') as f:
 w=csv.DictWriter(f,fieldnames=cols,extrasaction='ignore');w.writeheader();w.writerows(matrix)
raw={n:dict(collections.Counter(r['status'] for r in d.get('rows',[]))) for n,d in datasets.items()};counts=dict(collections.Counter(r['status'] for r in matrix))
dump('counts.json',{'acceptance_observations':counts,'acceptance_total':len(matrix),'excluded_observations':len(excluded),'raw_by_script':raw,'note':'Counts are individual observations, not unique user flows or assertion/test methods. Raw attempts unchanged; matrix references final datasets and explicit NOT RUNs.'})
manifest=[]
for f in sorted((P/'screenshots').glob('*.png')):
 data=f.read_bytes();w,h=struct.unpack('>II',data[16:24]);manifest.append({'path':f.relative_to(P).as_posix(),'sha256':hashlib.sha256(data).hexdigest(),'width':w,'height':h,'kind':'NATIVE Chromium screenshot','bytes':len(data)})
dump('screenshots-manifest.json',manifest)
unit=[]
for stem in ['tests','pages-tests']:
 log=(P/(stem+'.log')).read_text(encoding='utf-8');headers=[l for l in log.splitlines() if l.startswith(('FAIL:','ERROR:'))];ran=int(re.search(r'Ran (\d+) tests',log).group(1));fails={re.search(r'\((catalog\.[^)]+)\)',s).group(1) for s in headers if s.startswith('FAIL:')};errors={re.search(r'\((catalog\.[^)]+)\)',s).group(1) for s in headers if s.startswith('ERROR:')};unit.append({'name':stem,'methods':ran,'PASS':ran-len(fails|errors),'FAIL':len(fails),'ERROR':len(errors),'subtest_failure_headers':len([s for s in headers if s.startswith('FAIL:')]),'subtest_error_headers':len([s for s in headers if s.startswith('ERROR:')]),'headers':headers,'command':json.loads((P/(stem+'-command.json')).read_text())})
dump('test-summary.json',unit)
with urllib.request.urlopen('http://localhost:8823/qa/state/',timeout=10) as response:dump('state-final.json',json.load(response))
finddir=P/'findings';finddir.mkdir(exist_ok=True)
for f in F:
 e='\n'.join('- ['+p+'](../'+p+')' for p in f['evidence'])
 src='; '.join('`'+p+'`' for p in f['source'])
 text=f"""# {f['id']} — {f['title']}

**OPEN / {f['p']} / LOCAL C:\\kidsmap / module10-2026-10-10-r1 / 2026-10-10.** Классификация: {f['classification']}. Execution: /root sequential, свежие native Chromium и own isolated DB. Production UNKNOWN. Исполнитель аудита не менял application sources/существующие assertions; чужой drift зафиксирован в [SOURCE-DRIFT](../SOURCE-DRIFT.md).

**Роль:** {f['role']}. **URL/endpoint:** `{f['url']}`.

**Шаги:** {f['steps']}

**Ожидание:** {f['expect']}

**Факт:** {f['fact']}

**Перепроверка WORKTREE:** {f['current_snapshot_note']}

**Приоритет и эффект:** {f['impact']}

**Первопричина / гипотеза:** {f['root']}

**Source:** {src}. Source refs — объяснение, rendered evidence перечислено ниже. Confidence: высокий для наблюдаемого эффекта; confidence root указан отдельно.

**Доказательства:**

{e}

**Область исправления:** {f['scope']}

**Владелец / зависимости:** {f['dependencies']}

**Следующий шаг:** отдельный repair scope с конкретным планом. [Готовый самостоятельный промпт]({f['id']}-repair.txt). Аудит ничего не исправляет.
"""
 (finddir/(f['id']+'.md')).write_text(text,encoding='utf-8')
 prompt=f"""Работай в корне KidsMap; сначала определи фактический checkout (в аудите C:\\kidsmap). Прочитай AGENTS.md, .agents/README.md, .agents/registry.json, actual kidsmap-orchestrator, architecture/source-of-truth/audit-contract, docs/qa/module10-2026-10-10-r1/findings/{f['id']}.md и приложенные свежие evidence. Старые отчёты — только checklist.

Задача: {f['id']} «{f['title']}», приоритет {f['p']}. Сначала воспроизведи заново на текущем HEAD/WORKTREE и собственном изолированном стенде: {f['steps']}
Ожидание: {f['expect']}
Аудит наблюдал: {f['fact']}
Первопричина/гипотеза: {f['root']}
Область: {f['scope']}
Зависимости: {f['dependencies']}

Сохрани чужие изменения, active_run, стенды и журналы. Codebase Memory C-kidsmap сначала для broad exploration, freshness/coverage явно; verify source. Согласуй конкретный план и scope до application implementation согласно каноническим инструкциям. Если authorization на этот repair уже явно есть — не проси повторно. Приложенные findings сами по себе не разрешают fixes.
Только DJANGO_TESTING=1, собственные DB/cache/media/private-media/email, вымышленные данные, без inherited production credentials/внешних интеграций. Проверяемые действия — native UI, негативные HTTP только локально; no direct ORM transitions. Не менять существующие assertions, чтобы получить зелёный результат. No commit/push/deploy/production.
После согласованного исправления: точечные meaningful regression tests плюс реальный browser RU/AZ/EN ×360/390/768/1024/1280/1440 для затронутых состояний; save→reload→public/candidate/live, relevant keyboard/loading/error. Сохрани новый отчёт/screenshots с HEAD/WORKTREE, exact commands/counts/exit codes; отдельно baseline/environment/SIMULATED/NOT RUN. Не утверждай production fix по локальному результату.
"""
 (finddir/(f['id']+'-repair.txt')).write_text(prompt,encoding='utf-8')
index='# Подтверждённые проблемы модуля 10\n\n15 OPEN: 1 P1, 12 P2, 2 P3. Production не проверялся; аудит не исправлял приложение. SITE-QA-07 — существующие compiled locale artifacts; SITE-QA-14 — SIMULATED transport, подтверждённая потеря ввода в Chromium; SITE-QA-15 — настоящий lost update в двух вкладках.\n\n| ID | Приоритет | Проблема | Промпт |\n|---|---|---|---|\n'
for f in F:index+=f"| [{f['id']}](findings/{f['id']}.md) | {f['p']} | {f['title']} | [Копировать](findings/{f['id']}-repair.txt) |\n"
(P/'FINDINGS.md').write_text(index,encoding='utf-8');dump('findings.json',F)
snap=json.loads((P/'snapshot.json').read_text());run=datetime.datetime.now(datetime.timezone.utc).isoformat();shotcount=len(manifest)
group=collections.defaultdict(collections.Counter)
for row in matrix:group[(row['role'],row['lang'],str(row['width']))][row['status']]+=1
table='| Роль | Язык | Ширина | PASS | FAIL | NOT RUN |\n|---|---|---:|---:|---:|---:|\n'
for (role,lang,width),c in sorted(group.items()):table+=f"| {role} | {lang} | {width} | {c['PASS']} | {c['FAIL']} | {c['NOT RUN']} |\n"
(P/'coverage-by-role-language-width.md').write_text('# Матрица ролей / языков / ширин\n\nЭто counts наблюдений, не полная комбинационная приёмка каждого действия. Exact scenario/URL/evidence row в [matrix.csv](matrix.csv).\n\n'+table,encoding='utf-8')
report=f"""# Модуль 10 — настройки, разделы и общие страницы

**FAIL. Аудит одного модуля завершён с явными NOT RUN.** 15 подтверждённых проблем: 1 P1, 12 P2, 2 P3. Application fixes не выполнялись исполнителем аудита.

Роль/execution identity: `/root`, canonical orchestrator, Django, frontend-admin/public, browser-qa и bounded security-reviewer выполнены последовательно одним исполнителем; независимые subagents не запускались. Definitions: `.agents/agents/<role>/agent.md`; authoritative registry `.agents/registry.json`. Дата 2026-10-10; финальная сборка {run} UTC. Исторические отчёты использованы только как checklist/helper code, все результаты/снимки QA10 получены заново.

## 1. Состояние области

LOCAL checkout `C:\\kidsmap`, branch `{snap['branch']}`, HEAD `{snap['head']}`, dirty WORKTREE преимущественно QA/docs ([entry snapshot](snapshot.json)); приложение соответствует HEAD. Active_run `{snap['active_run']}`, не менялся. Source manifest: 2784 files, SHA256 digest `{snap['source_digest']}`. PRODUCTION version/данные/доступ UNKNOWN, не посещались. [Финальная проверка](verification.json), [runtime](runtime-final.json).

Собственный новый стенд: Django6.0.2/Python3.12.15, HTTP `127.0.0.1:8823` PID40936; отдельный own DEBUG=False error process `127.0.0.1:8824` PID17432. PostgreSQL17.11 container `kidsmap-module10-20261010-r1`, port55441, DBmodule10/testDBtest_module10, 175 migrations applied. Container ID `97fac7184d2c877743ba93c42342be06a186ae4a4f110eaf84918e16ec75d463`, own volume `09a95b93e1bef30fc385c0203f058ba2befadefe23261f72b5c24ffbc2512568`. Все данные вымышлены. LocMem cache/mail, отдельные media/private-media/cookies, unit test media/DB. External credentials scrubbed, .env при TESTING не загружается; server socket/browser routing ограничивают исходящие интеграции. [Isolation](isolation.json), [launcher](run.py), [settings](qa_settings.py).

Доказательство runtime identity: startup source hash guard, отсутствие autoreloader, unchanged current source manifest и listener PID; `/qa/version/` лишь возвращает manifest и не считается независимой attestation. Девять чужих HTTP и 11 containers, 9736 чужих файлов кроме журнала проверяются финально; исходники/чужой active_run не менялись. Все требуемые документы найдены ([inventory](documents.json)). Codebase Memory `C-kidsmap` вернул `Transport closed`, freshness/coverage UNKNOWN; bounded source fallback, без reindex/cache export ([record](graph-summary.json)).

## 2. Сильные стороны

Native save→reload подтверждает брендинг/title/subtitle/search label/decor, 9 trimmed public texts и загруженные файлы. Brand logo/footer phone/email обновляются на публичных страницах. Неверные email/URL и threshold favorite count отклоняются сервером без ложного сохранения; исправление threshold даёт правильный публичный счётчик RU/AZ/EN. Пустой EN title остаётся пустым в DB, default display не записывается как сохранённый перевод.

OFF/ON трёх flags сохраняет данные и независимость остальных flags. Org/Spec lists+details скрываются404; Event list/detail410. Catalog/map permanent Place сохраняется, temporary Place скрывается в map/catalog. Поддержанные lawful owner Spec2/Event2 OFF/ON работают; Organization workspace остаётся доступным. Admin Organization2 при OFF действительно сохранён через UI как draft, после reload/ON candidate сохранён, live content_version1/названия прежние ([readback](organization-readback.json)). Для Specialist/Event доказана доступность admin editor, полный hidden save cycle NOT RUN.

Общие страницы home/about/FAQ/contacts/privacy/terms/review-rules/listing-rules/add-place + empty catalog отрисованы RU/AZ/EN ×360/390/768/1024/1280/1440 до заполнения настроек. `for-business` — поддержанный legacy redirect к add-place; selected unchanged tests проверяют redirect. Filled public/settings matrix, языковой switch с сохранением catalog query/category, native mobile/desktop menu, footer/back-to-top/focus выполнены. FAQ Space/Enter после анимации 36/36 PASS. Contacts H1 computed solid contrast ≥3 во всех18 cells; это ограниченная выборка, не полный WCAG verdict.

## 3. Реальные проблемы

[Отдельные findings и 15 копируемых repair prompts](FINDINGS.md). Наиболее серьёзный SITE-QA-01: staff без model permissions читает медиахаб и загружает/удаляет глобальный публичный logo. Валидный CSRF проверен; без CSRF403. После фиксации evidence logo восстановлен через native admin UI. Production exploitation/integrations не проверялись.

Неприменённые публичные settings (AZ about/empty, contacts, CTA/placeholder, home hero PC/mobile), corrupt image acceptance, mobile form overflow, непоследовательный events OFF для legacy temporary URL, blank410, locale/admin modal states и input recovery описаны отдельно. Initial focus/Tab modal defect перепроверен после bringToFront/1250ms без screenshot до keyboard; Escape после анимации PASS. Неизвестная первопричина focus обозначена гипотезой. CSS zoom overflow не назначен app finding.

## 4. Tech debt

Обновлённые публичные шаблоны и старые SiteSettings controls расходятся; compiled locale artifacts не содержат часть уже существующих PO strings. Custom media endpoints обходят стандартный Django admin permission/validation lifecycle. Старые tests для legacy URLs/identity требуют отдельного contract review; assertions в аудите не менялись.

## 5. Risks

Все OPEN findings подтверждены только в LOCAL entry WORKTREE. Новая regression относительно исторического release не установлена: исходники не изменены во время аудита, исторические результаты не считаются свежей базой. SITE-QA-07 — pre-existing locale/environment artifact failure; остальные native failures — pre-existing application/UX/security, SITE-QA-14 также явно SIMULATED transport.

LocMem singleton invalidation наблюдалась после native save→reload/public в основном процессе. Multiworker/Redis не проверялись. Network abort before server и upload delay/error — SIMULATED, реальный disconnect/HTTP500 retry NOT RUN. Uploaded malformed image вызвал настоящий сохранённый broken logo; этот сбой не симуляция ответа сервера.

## 6. Dead/legacy candidates

Home hero/image settings с отсутствующим публичным consumer — candidates для product/source reconciliation, не доказательство ненужной DB структуры. Legacy temporary Place и for-business route сохраняют реальные контракты. Никаких удалений, migrations или cleanup не выполнялось.

## 7. Tests gaps и результаты

Acceptance observations: **{counts.get('PASS',0)} PASS / {counts.get('FAIL',0)} FAIL / {counts.get('NOT RUN',0)} NOT RUN**, {len(matrix)} всего; counts не равны уникальным сценариям. [Полная scenario/role/language/width матрица](matrix.csv), [JSON](matrix.json), [сводка по ролям/языкам/ширинам](coverage-by-role-language-width.md), [raw/excluded counts](counts.json), [точные исключения](excluded-observations.json).

Неизменённые Django tests: 46 методов, **41 PASS / 4 FAIL / 1 ERROR**. Основная выборка34:29PASS/4FAIL/1ERROR, unittest6failure+2error subtests, exit1,35.456s test-body (81.3s total). 12 PageSmoke methods:12PASS exit0,3.455s test-body (32.58s total). [Summary](test-summary.json), [основной log](tests.log), [page log](pages-tests.log), [команды](tests-command.json), [page command](pages-tests-command.json).

Один failed method — реально не локализованные section labels (SITE-QA-07, EN/AZ subtests). Три other FAIL methods и один ERROR method — baseline fixture/contracts: Specialist default-enabled test использует legacy/unverified identity (302 вместо ожидаемого200); Place old-language slug tests получают canonical301 вместо200; review block lookup получает пустое redirect body и ValueError. Native lawful canonical path проверяется отдельно и не считается passed на основании этих failed tests. Первоначальный PageSmoke run12/10PASS/2FAIL (6 subtests) имел own PUBLIC_BASE_URL mismatch localhost vs testserver; own unit runner исправлен, приложение/assertions не менялись; [attempt log](pages-tests.attempt1.log) сохранён.

Raw harness ошибки не скрыты: trailing-space expectation (12), wrong business entitlement/button and legacy identity, FAQ animation timing, too-early Escape check исключены/перепроверены. Все script attempts сохранены. Final modal focus FAIL после достаточного ожидания остаётся. DEBUG=True default404 диагностический overflow/lang — environment, заменён DEBUG=False rendered proof. CSS zoom2 — SIMULATED, realChrome200%zoom NOT RUN.

Explicit NOT RUN: two-tab/stale/duplicate settings writes в остальных language/width combinations (RU1440 выполнен), полный UI unpublish/archive/delete lifecycle (начальные fixture states доказательством переходов не являются), полный hidden Spec/Event save, realChrome200%zoom, full pixel contrast/error403/500 matrix, shared cache/multiworker, external integrations/production, full suites/CI/other browsers. [Пределы](coverage-gaps.json). Все основные 18 cells выполнены только для перечисленных public pages/settings/flags, не для каждой возможной мутации/роли.

Свежих native PNG **{shotcount}**, включая PC/mobile/error/loading/modal/footer, [SHA/dimensions manifest](screenshots-manifest.json). Нет derived снимков. Full-page images с lazy/animation ниже viewport могут содержать неинициализированные блоки; отсутствие такого блока не назначено finding без native scroll/viewport проверки. Viewport examples: [mobile modal](screenshots/modal-final-viewport.png), [PC home](screenshots/home-viewport-en-1440.png), [mobile contacts](screenshots/contacts-viewport-ru-390.png), [corrupt logo](screenshots/invalid-file-public-mobile.png), [mobile overflow](screenshots/admin-sitebrandingsettings-ru-360.png).

Console/network: initial native matrix наблюдает pageerror и local non-document HTTP≥400, без таких ошибок на нормальных страницах. Это ограниченная инструментальная выборка; не полный console/security audit. Expected404/410/denials, intentional abort и malformed-image failures отдельно; external SDK/integrations blocked, успешными не считаются.

## 8. Recommendations

Оформить отдельный план прежде всего для permission bypass, затем сохранённых/публичных settings, visibility/media/layout/input-recovery; prompts самостоятельные. Никакие fixes автоматически не применены. Полный список own synthetic settings edits: [settings-changes](settings-changes.json), [final DB read-only snapshot](state-final.json). Section flags ON, favorites OFF, валидный logo и EN title восстановлены. Organization2 оставлен со своим вымышленным draft candidate для review.

Журнал изменяется только в row10. [Текст следующего чата](next-chat.txt) направляет на **11 SEO, языковые URL и redirects**, один новый модуль;13 после01–12. Own HTTP/PG/browser оставлены для review; это не свежее evidence для следующего модуля. Чужие стенды/файлы/active_run сохранены. No commit/push/deploy/production.

## 9. P0/P1/P2/P3

P0:0; P1:1 (SITE-QA-01); P2:12 (02–10,13–15); P3:2 (11–12). Все OPEN, remediation не запускалась. [Finding index](FINDINGS.md). [Exact/replay commands](COMMANDS.md), [final preservation/source/runtime verification](verification.json). PASS этого preservation check не меняет функциональный FAIL модуля.
"""
(P/'REPORT.md').write_text(report,encoding='utf-8')
# Handoff uses the actual canonical next-module prompt verbatim.
canonical=(R/'docs/qa/module-acceptance-prompts.md').read_text(encoding='utf-8');block=canonical.split('## 11. SEO, языковые URL и redirects',1)[1].split('## 12.',1)[0];prompt=re.search(r'```text\n(.*?)\n```',block,re.S).group(1)
handoff=f"Продолжаем KidsMap. Выполни только один модуль: 11 «SEO, языковые URL и redirects». 01–10 завершены FAIL с указанными NOT RUN; 13 последним. Прочитай журнал docs/qa/module-acceptance-prompts.md и docs/qa/module10-2026-10-10-r1/REPORT.md. QA10 HEAD {snap['head']}, branch {snap['branch']}, active_run NONE. Данные/доказательства QA10 — исторический checklist, не свежая проверка11.\n\nСохрани чужие docs/изменения/active_run/стенды. QA10 own stand localhost8823 PID40936, DEBUGFalse8824 PID17432, PG55441/container kidsmap-module10-20261010-r1/volume09a95b93e1bef30fc385c0203f058ba2befadefe23261f72b5c24ffbc2512568, browser module10-r1 оставлены для review. Эти PID/порты на другом ПК не считать доступными. Для11 создай новый isolated stand. Не исправляй findings; отдельные prompts docs/qa/module10-2026-10-10-r1/FINDINGS.md.\n\n"+prompt+'\n\nПосле приёмки11 сохрани свежий отчёт/evidence/screenshots, измени только row11 и подготовь handoff12. No commit/push/deploy/production.\n'
(P/'next-chat.txt').write_text(handoff,encoding='utf-8')
commands='''# Команды и воспроизводимость QA10

Рабочий каталог C:\\kidsmap, shell PowerShell. Все команды ниже — собственный QA10; credentials только в ignored scratch, не в command artifacts. Native browser Chromium153.0.8010.12/headless shell1243, session module10-r1.

Bootstrap helpers: `prepare.py` (создана fresh preservation manifest и ignored credential), `run.py snapshot`, `run.py migrate` (175 migrations), `seed.py` (initial fictional data). Helper seed первые попытки упали на собственной гонке миграций и неправильном lon вместо lng; final seed успешен. Первый qa/state probe был исправлен только в own helper (Organization.archived_at вместо несуществующего deleted_at), собственный main process перезапущен после проверки его identity. Application sources не менялись.

Точные команды собственных runner, воспроизводимые из repo root:

```powershell
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/run.py snapshot
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/run.py migrate
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/seed.py
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/run.py serve
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/run.py serve-errors
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/extra-fixtures.py
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/lawful-fixtures.py
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/owned-organization.py
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/organization-readback.py
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/mo-check.py
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/acl-identity.py
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/tests-run.py
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/tests-run.py pages
wsl.exe -- docker inspect --format '{{.Id}} {{.Config.Image}} {{range .Mounts}}{{.Name}} {{.Destination}}{{end}}' kidsmap-module10-20261010-r1
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/build-report.py
.venv/Scripts/python.exe docs/qa/module10-2026-10-10-r1/verify.py
```

Внимание: bootstrap scripts не идемпотентны, не повторять seed/prepare/snapshot на существующей DB, чтобы не подменить entry. Для нового run нужны новое имя/порты/DB/scratch. PG own image postgres:17-alpine, loopback55441, user/DB module10, trust только own local container, отдельный volume; runtime inspect в verification. Полный исходный docker/browser-open shell invocation не был сохранён как отдельный command log; не восстанавливаем его по догадке. Browser executable/config фактически сохранён в ignored scratch/playwright.json; native replay wrapper drive.py содержит exact node CLI executable and run-code arguments без password в committed/effective source.

Unit exact selected labels, native process exit/duration и scrub counts: [tests-command.json](tests-command.json), [pages-tests-command.json](pages-tests-command.json). Первый pages attempt сохранён отдельно. Много failures на уровне наблюдений не означает CLI nonzero: CLI exit0 лишь показывает, что script завершился и вернул rows.

Browser native command ledger (включая failed harness attempts):

| UTC | Точная команда | CLI exit | Seconds | Result |
|---|---|---:|---:|---|
'''
for line in (P/'command-ledger.jsonl').read_text().splitlines():
 x=json.loads(line);commands+=f"| {x['utc']} | `{x['command']}` | {x['cli_exit_code']} | {x['duration_seconds']} | [{x['result']}]({x['result']}) |\n"
(P/'COMMANDS.md').write_text(commands,encoding='utf-8')
dump('report-build.json',{'utc':run,'findings':len(F),'severity':dict(collections.Counter(f['p'] for f in F)),'screenshots':shotcount,'counts':counts,'excluded':len(excluded),'tests':{'methods':sum(x['methods'] for x in unit),'PASS':sum(x['PASS'] for x in unit),'FAIL':sum(x['FAIL'] for x in unit),'ERROR':sum(x['ERROR'] for x in unit)}})
print((P/'report-build.json').read_text())
