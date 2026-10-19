import ast,hashlib,json,subprocess,shutil
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import urlopen
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/social07-pc-fix-r1';O=R/'docs/qa/social-qa07-fix-2026-10-17-pc-r1';P=R/'docs/qa/social-qa07-recheck-2026-10-17-pc-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d): (O/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
e=json.loads((Q/'entry.json').read_text());sources=json.loads((Q/'expected-source.json').read_text())['sources']
assert len(sources)==1022 and all(sha(R/p)==h for p,h in sources.items())
assert sum(sources[p]==h for p,h in e['sources'].items())==1020
assert all(sha(R/p)==h for p,h in e['shared_mo'].items());assert sha(R/'.cbmignore')==e['cbmignore_sha256']
assert all(sha(P/p)==h for p,h in e['prior_plan_files'].items())
for name,h in e['prior_packages'].items():
 folder=O.parent/name
 assert sha(folder/'artifact-manifest.json')==h['manifest_sha256'] and sha(folder/'verification.json')==h['verification_sha256']
 for p,v in json.loads((folder/'artifact-manifest.json').read_text()).items():assert sha(folder/p)==v,(name,p)
m=json.loads((Q/'matrix.json').read_text());assert len(m)==66
assert all(all(r['controls'].values()) and all(r['source'].values()) and not r['pageerrors'] and not r['http_failures'] and not r['request_failed'] for r in m)
edges=json.loads((Q/'edges.json').read_text());redirect=json.loads((Q/'redirect.json').read_text())
assert all(all(r['checks'].values()) for d in [edges,redirect] for r in d['rows'])
assert not edges['pageerrors'] and not edges['requestfailed']
assert (Q/'tests.exit').read_text().strip()=='0';assert 'Ran 11 tests' in (Q/'tests.log').read_text() and '\nOK\n' in (Q/'tests.log').read_text()
git=json.loads((Q/'git-final.json').read_text(encoding='utf-8-sig'));assert git['head']==e['head'] and git['branch']==e['branch'] and git['task33_ref']==e['task33_ref'] and git['index_tree']==e['index_tree'] and not git['staged']
active=[s for s in (R/'docs/task33/implementation-status.md').read_text().splitlines() if s.startswith('active_run:')];assert active==['active_run: NONE']
containers=subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines();assert set(e['containers']).issubset(containers) and len(containers)==len(e['containers'])+1
info=json.loads(urlopen('http://127.0.0.1:33348/qa/info/').read());assert info==json.loads((Q/'live-initial.json').read_text())
state=json.loads(urlopen('http://127.0.0.1:33348/qa/state/').read());assert all(state[k]==0 for k in state if k.endswith('_reviews'))
for p in ['src/catalog/controllers/typed_reviews.py','src/catalog/testcases/test_social_qa07_activity_review_title.py']:ast.parse((R/p).read_text())
assert (R/'src/catalog/controllers/typed_reviews.py').read_text()==(P/'candidate-typed_reviews.py').read_text()
assert (R/'src/catalog/testcases/test_social_qa07_activity_review_title.py').read_text()==(P/'candidate_tests.py').read_text()
# All evidence copies are selected, non-sensitive own fictional artifacts.
for n in ['manual-visual-review.md','ownership.json','ownership-proof.py','preparation-attempts.json','tests.log','tests.exit','tests-harness-gate-attempt1.log','seed-harness-gate-attempt1.log','matrix.json','edges.json','redirect.json','browser-commands.jsonl','browser-initial-cli.txt','edges-cli.txt','redirect-cli.txt','live-initial.json','git-final.json','targets.json','edge-targets.json','cell-body.js','matrix.py','edge-body.js','edges.js','redirect.js','browser_driver.py','run_json.py','fixtures.py','runtime.py','qa_urls.py','playwright.json','tests.sh','start-app.sh','bootstrap.py','bootstrap-retry.py','apply-approved.py','prepare-helpers.py','wait-ready.py']:
 shutil.copyfile(Q/n,O/n)
shutil.copyfile(Q/'locales/manifest.json',O/'locales-manifest.json');shutil.copyfile(P/'proposed.diff',O/'applied.diff');shutil.copyfile(P/'candidate-manifest.json',O/'approved-candidate-manifest.json')
(O/'png').mkdir(exist_ok=False)
for p in (Q/'png').glob('*.png'):shutil.copyfile(p,O/'png'/p.name)
assert len(list((O/'png').glob('*.png')))==135
save('png-manifest.json',{p.relative_to(O).as_posix():sha(p) for p in (O/'png').glob('*.png')});save('source-final.json',{'sources':sources});save('live-final.json',info);save('business-final.json',state);save('containers-final.json',containers)
summary={'utc':datetime.now(timezone.utc).isoformat(),'status':'SOCIAL-QA-07 CLOSED LOCAL scoped PASS; module09 OPEN','head':git['head'],'branch':git['branch'],'source_files':len(sources),'unchanged_prior_sources':1020,'tests':{'new':9,'affected_existing':2,'total':11,'seconds':5.415,'failures':0,'errors':0,'exit':0},'native':{'cells':66,'controlsPASS':sum(sum(r['controls'].values()) for r in m),'sourcePASS':sum(sum(r['source'].values()) for r in m),'sourceFAIL':0,'edge_rows':len(edges['rows']),'edge_checksPASS':sum(sum(r['checks'].values()) for r in edges['rows']),'redirect_rows':len(redirect['rows']),'redirect_checksPASS':sum(sum(r['checks'].values()) for r in redirect['rows']),'png':135,'pageerrors':0,'unexpected_http_failures':0,'requestfailed':0},'preservation':{'prior_plan_files':len(e['prior_plan_files']),'prior_packages':len(e['prior_packages']),'entry_containers':len(e['containers']),'final_containers':len(containers),'sharedMO':True,'cbmignore':True,'HEAD_index_task33':True,'active_run_NONE':True},'not_run':['SOCIAL08-09','full ACCEPT09','global corpus','physical devices','real screenreader/full WCAG','other browsers','production/deployment','external services']}
save('results.json',summary)
(O/'REPORT.md').write_text('''# SOCIAL-QA-07 — CLOSED LOCAL, scoped PASS

На текущем dirty WORKTREE исправлено техническое имя Activity object (pk) в заголовке отзывов. Контроллер получает название Activity из того же public presentation resolver, что и карточка занятия, с текущей локалью и разрешённым AZ fallback/snapshot/live Program. Другие виды объектов сохраняют прежний путь. Пустое каноническое имя остаётся пустым; скрытое имя draft не раскрывается даже в разрешённом staff просмотре. Повторный вызов resolver добавляет read-only чтения; оптимизация вне scope.

Пользователь «одобряю» одобрил точный двухфайловый IMPLEMENTATION_PLAN предыдущего PLAN07. Применены только controller expression и новый test_social_qa07_activity_review_title.py. Существующие dirty03 hunks сохранены. 1022 source files: один новый, один изменённый, остальные 1020 побайтно прежние. Снимок HEAD852938d96764ae315b92859e3651e5ea62054a36; ветка codex/module09-transfer-2026-10-16-r1. LOCAL HEAD, dirty WORKTREE и production различаются; production не проверялся и не изменялся.

## RED → GREEN

Неизменившийся RED сохранён в ../social-qa07-recheck-2026-10-17-pc-r1/: 9 новых методов, 7failed/2passed, 18 failing assertions/subtests; native66cells:540controlPASS/144sourceFAIL. Патч и assertions совпадают с одобренными кандидатами, старые assertions не редактировались.

После патча один успешный targeted запуск: 11 уникальных методов (9 новых + 2 affected03), 5.415s, 0 failures/errors, exit0. Проверены requested names для guest/author, RU/AZ/EN, AZ fallback, snapshot, live Program, escaping, canonical empty, другие kinds, hidden404, staff privacy, existing conflict409 render/CAS. tests.log содержит точные результаты; 409/404 строки ожидаемы в целевых тестах.

Неизменённая native матрица: 66cells,540controlPASS/144sourcePASS/0FAIL,114PNG. Localized Activity: guest/author×RU/AZ/EN×360/390/768/1024/1280/1440 (36cells); fallback/snapshot12cells390; Place/Specialist/Event18cells390. Реальный detail→native reviews link→reload, h1/title, роль формы, overflow и business aggregates. Дополнительные 28rows (27cases+aggregate): escaping/empty/live Program guest+author, hidden guest+author404/staff200 на трёх локалях,21PNG. Legacy /az/ redirect для guest/author:2rows,10checks,301→canonical200. Точные дополнительные counts — results.json. Ожидаемые hidden404 отдельно от unexpected HTTP failures. Pageerrors/requestfailed0; основная матрица HTTP failures0. Новые локальные PNG доступны, старые не догружались.

## Изоляция и сохранность

Новый own m09s07-fix-r1-app, Chromium155.0.8059.12/session social07-pc-fix-r1, loopback33348; проверенный внутренний PLAN07 network/fictional PostgreSQL17.11 переиспользован по ownership proof. App mount repository RO, только own scratch RW; Python3.12.15/Django6.0.2, DJANGO_TESTING1, env очищен, собственные cache/media/private-media/email. TestDB test_m09s07_fix_r1 отдельна от normal fictionalDB. В normal ownDB добавлены только fictional edge fixtures; браузерные GET не изменили business aggregates, reviews0. До setup свежая native компиляция RU/AZ/EN в own MO, manifest verify, sole LOCALE_PATHS. Внешние browser requests блокируются allowlist localhost; реальные сервисы не проверялись.

Все 40 входных container ID/name/state сохранены, добавлен один own app (итого41); это не доказательство непрерывности всех процессов компьютера. Предыдущие 8 packages и все151 files PLAN07 неизменны. SharedMO, .cbmignore, HEAD/index/task33-progress и active_run:NONE сохранены. Guide получает отдельную append note с обратной hash-проверкой старых bytes. Без reset/clean/stash/checkout switching/commit/push/deploy/production.

## Ошибки подготовки

До патча WSL git status -uall работал медленно; остановлен только собственный child git и использован Windows git. Начальный apply-check без предусмотренного планом ignore-space-change дал newline/whitespace mismatch, без mutation; точный diff затем прошёл check и применён с одобренным flag. Первый seed/test gate остановился до тестов из-за ошибочно переименованного QA PG hostname; исправлен только own QA profile, исходники/assertions прежние. Failed logs сохранены. Один составной запуск proxy/readiness отклонён автоматической проверкой без подробной причины (blocked by policy); раздельные узкие команды успешно выполнены. Ни один из этих запусков не засчитан как application test failure или PASS.

## Границы

Закрыт только SOCIAL-QA-07 в указанном LOCAL snapshot. SOCIAL08–09, full ACCEPT09, global tests, realSR/fullWCAG, physical devices, другие браузеры, production/external services NOT RUN. Следующий шаг — отдельный свежий PLAN SOCIAL-QA-08; автоматическое начало не разрешено. Никаких новых approvals для уже исполненного07 не требуется.
''',encoding='utf-8')
(O/'commands.md').write_text('''# Commands and outcomes

Executed from C:/kidsmap using Windows PowerShell and Ubuntu-24.04 WSL. Runtime scripts are evidence, not continuation commands.

- Windows git status --porcelain=v1 -uall and refs/index/source hashes: exit0. Own initial WSL status child terminated after slow traversal, not application run.
- bootstrap/apply-approved.py: gates source1021/old artifact hashes/internal own PG/RO mount; initial apply-check whitespace failure1; git apply --check --ignore-space-change and git apply --ignore-space-change exact approved diff exit0; candidate text equality/source1022 gate exit0.
- scripts/build_isolated_locales.py build --output /mnt/c/kidsmap/.tmp/social07-pc-fix-r1/locales --locales ru az en --compiler native: exit0,3catalogues; verify before each setup.
- start-app.sh: initial gate1, corrected isolated hostname, retry0; own fixture seed/serve only. No old prepare scripts executed.
- docker exec m09s07-fix-r1-app python /mnt/c/kidsmap/.tmp/social07-pc-fix-r1/runtime.py test catalog.testcases.test_social_qa07_activity_review_title.SocialQA07TitleTests catalog.testcases.test_social_qa03_conflict_recovery.TypedReviewConflictRecoveryTests.test_stale_draft_renders_with_latest_version_and_no_write catalog.testcases.test_social_qa03_conflict_recovery.TypedReviewConflictRecoveryTests.test_conflicting_script_text_is_escaped_and_preserved: exit0,11tests,5.415s. Pre-test QA host gate failure preserved separately.
- browser_driver.py open --config /mnt/c/kidsmap/.tmp/social07-pc-fix-r1/playwright.json:0; browser-initial.js:0; matrix.py:0,66cells. Each CLI call logged browser-commands.jsonl; matrix source/control assertions unchanged from PLAN07.
- run_json.py edges and run_json.py redirect:0, raw outputs/results retained; assertions all true.
- git-final.ps1:0. publish.py and verify_integrity.py check current sources, prior files, container states, refs/index/MO/active_run, manifest, counts and guide reverse hash: exit0 required before closure.
''')
(O/'status-note.md').write_text('''## SOCIAL-QA-07 — LOCAL closure на этом ПК (2026-10-17)

Пользователь одобрил PLAN07; двухфайловый patch применён к dirty WORKTREE HEAD852938d. Отзывы Activity используют каноническое публичное имя вместо Activity object (pk). Source1022; остальные1020 прежние. Targeted11tests PASS, native66cells:540controlPASS/144sourcePASS, edge28rows и301redirect2rows PASS,135новыхPNG. Пустое public имя остаётся пустым; staff draft name не раскрыт. [Отчёт](social-qa07-fix-2026-10-17-pc-r1/REPORT.md), [verification](social-qa07-fix-2026-10-17-pc-r1/verification.json). Сохранены40входныхcontainers/старыеpackages/refs/index/MO/active_run:NONE; guide history прежняя. SOCIAL01–07 CLOSED LOCAL только в проверенных границах; module09 OPEN. Следующий шаг — отдельный свежий PLAN SOCIAL-QA-08; SOCIAL08–09/fullACCEPT09/global/module10 NOTRUN. Commit/push/deploy/production не выполнялись.
''',encoding='utf-8')
(O/'NEXT_PROMPT.txt').write_text('Продолжить KidsMap C:/kidsmap, ветка codex/module09-transfer-2026-10-16-r1, HEAD852938d96764ae315b92859e3651e5ea62054a36. Сначала прочитать AGENTS/canonical entry/guide и SOCIAL07 fix REPORT/verification/source-final. Сохранить dirty WORKTREE; без reset/clean/stash/switch/commit/push/deploy/production, active_run не назначать. SOCIAL01–07 CLOSED LOCAL scoped; module09 OPEN. Следующий шаг только свежий PLAN SOCIAL-QA-08 по guide: isolation/source/meaningful reproduction/cause/exact scope; implementation08 требует approval. Старые PNG не догружать, новые07 доступны. Старые runtime scripts не запускать автоматически. Существующее approval07 исполнено и повторно не требуется.\n',encoding='utf-8')
g=R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md';b=g.read_bytes();assert sha(g)==e['guide_sha256'];note=(O/'status-note.md').read_bytes().rstrip(b'\n')+b'\n\n';marker='## Сколько задач осталось и как идти'.encode();assert b.count(marker)==1;g.write_bytes(b.replace(marker,note+marker,1));assert hashlib.sha256(g.read_bytes().replace(note,b'',1)).hexdigest()==e['guide_sha256']
shutil.copyfile(Path(__file__),O/'publish.py')
print(json.dumps(summary,ensure_ascii=False))



