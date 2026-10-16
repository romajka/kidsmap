"""Read-only verification and owned report generation."""
import importlib.metadata,json,subprocess,urllib.request,hashlib,sys
from pathlib import Path
from bootstrap import ROOT,HERE,SCRATCH,source,write
entry=json.loads((HERE/'entry.json').read_text());server=json.loads((HERE/'server.json').read_text());setup=json.loads((HERE/'setup.json').read_text())
with urllib.request.urlopen(server['url']+'/qa/start-version/',timeout=10) as r: version=json.load(r)
write('runtime-version.json',version)
foreign={row['Names']:row['ID'] for row in entry['foreign_containers']}
now={row['Names']:row['ID'] for row in [json.loads(x) for x in subprocess.check_output(['docker','ps','--format','{{json .}}'],text=True).splitlines()]}
transfer=json.loads((ROOT/'docs/qa/continuation-2026-10-11/transfer-inputs.json').read_text())
missing={k:[x for x in transfer[k] if not (ROOT/x).is_file()] for k in ('required_entry_inputs','tracked_modified_before_guide','untracked_paths_at_preparation')}
inspect=json.loads(subprocess.check_output(['docker','inspect','--format','{{json .NetworkSettings.Ports}}',setup['container']],text=True))
checks={'HEAD_unchanged':subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==entry['head'],'source_preserved':source()==entry['source_files'],'runtime_entry_matches_startup':version['entry_matches_startup'],'runtime_startup_matches_disk':version['startup_matches_disk'],'own_process_pid':server['pid']==version['pid'],'foreign_running_container_identities':all(now.get(k)==v for k,v in foreign.items()),'active_run_preserved':'active_run: NONE' in (ROOT/'docs/task33/implementation-status.md').read_text(),'tracked_diff_empty':not subprocess.check_output(['git','diff','--name-only'],text=True).strip(),'inputs_complete':not any(missing.values()),'pg_loopback_only':inspect['5432/tcp']==[{'HostIp':'127.0.0.1','HostPort':str(setup['pg_port'])}]}
assert all(checks.values()),checks
write('verification.json',{'checks':checks,'missing':missing,'scope':'START only; no full module01 claim'})
versions={'Python':sys.version.split()[0],'Node':subprocess.check_output(['node','--version'],text=True).strip(),'Docker':subprocess.check_output(['docker','version','--format','{{.Client.Version}} / {{.Server.Version}}'],text=True).strip(),'msgfmt':subprocess.check_output(['msgfmt','--version'],text=True).splitlines()[0],'PostgreSQL':version['postgres']}
for name in ('Django','psycopg','django-allauth','django-jazzmin','Pillow','whitenoise','redis','mysqlclient'):
 try:versions[name]=importlib.metadata.version(name)
 except importlib.metadata.PackageNotFoundError:versions[name]='UNAVAILABLE in reused venv; not used by this QA profile'
write('tools.json',versions)
write('screenshots-manifest.json',[{'path':p.name,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(HERE.glob('start-*.png'))])
manifest=json.loads((SCRATCH/'locales/manifest.json').read_text());write('locale-manifest.json',manifest)
browser=json.loads((HERE/'browser-smoke.txt').read_text().split('### Result\n')[1].split('\n')[0]);write('browser-smoke.json',browser)
assert all(p['status']==200 for p in browser['pages']) and not browser['pageerrors'] and not browser['local_errors']
readback=json.loads((HERE/'readback.json').read_text())
guide=(ROOT/'docs/qa/continuation-and-repair-prompts-2026-10-11.md').read_text();accept=guide.split('### ACCEPT-01. Постоянные места\n')[1].split('```text\n')[1].split('```')[0]
(HERE/'next-prompt.txt').write_text('Используй собственный стенд START из docs/qa/start-local-2026-10-12-r1/REPORT.md. Сначала повторно проверь snapshot/runtime/locale manifest; не трогай чужие процессы. Учти helper suite WSL-only и неполный набор зависимостей reused venv; исходные assertions не менять.\n\n'+accept)
(HERE/'REPORT.md').write_text(f'''# START LOCAL QA — 2026-10-12 r1

Режим START, без application fixes. Один исполнитель /root по канонической kidsmap-orchestrator; независимые специалисты не запускались.

## Checkout и доставка

- Checkout: `{ROOT}`, branch `task33-progress`, HEAD `{entry['head']}`.
- На входе чистый WORKTREE, active_run NONE. На выходе только собственный untracked каталог `{HERE.relative_to(ROOT)}`; scratch ignored. Tracked diff пустой, исходники/shared MO побайтно сохранены.
- Прочитаны guide (вступление, статус, 13 модулей, этапы и Git-перенос), AGENTS и канонические README/registry/orchestrator/architecture/source-of-truth/audit-contract, isolated-locale-build и тестовые settings. Исторические отчёты module01 recheck, PLACE-QA-08 и module13 сопоставлены в этой переписке; их runtime факты не перенесены.
- Все 167 required inputs, 18 modified inventory paths и 12442 transfer inventory paths присутствуют. Missing: 0. PLACE fixes/helper/regression tests присутствуют в HEAD; функциональная полнота доставки этим не доказана.
- PLACE-QA-01–08 имеют исторические scoped результаты; PLACE-QA-08=CROSS-QA-03. Full module01 NOT RUN. Очередь 76 ID/73 группы, guide 88 блоков — 73 PLAN/13 ACCEPT/2 service.

## Собственный runtime

- URL: {server['url']}; PID {server['pid']}; `{HERE/'runtime.py'}`.
- PostgreSQL {version['postgres']}: container `{setup['container']}`, volume `{setup['volume']}`, host `127.0.0.1:{setup['pg_port']}`, DB/user `{setup['database']}`. Только loopback PortBinding проверен Docker inspect.
- {readback['migration_rows']} migration rows, 2 synthetic users, 1 unpublished synthetic Place. Фикстуры создавались только в новой собственной DB; это setup, не проверенный UI lifecycle.
- DJANGO_TESTING=1, DEBUG=False, LocMem cache/email, собственные media/private-media/staticfiles. Внешние ключи пустые; окружение allowlisted, manage.py/.env не загружались.
- Python socket connect/connect_ex разрешает только свой PostgreSQL; отрицательный egress probe остановлен до соединения. libpq использует явно настроенную единственную QA DB. Это runtime guard, не OS network sandbox. В браузере все origin вне собственного loopback блокируются.
- Пароли/secret key хранятся только в ignored scratch с mode600. Значения в отчёт/evidence не включены.
- Source entry=startup=current: {version['source_files']} файлов, SHA digest `{version['source_digest']}`. Runtime attestation выполнен на работающем процессе; app source и общие MO сохранены.
- RU/AZ/EN собраны native GNU msgfmt в `{SCRATCH/'locales'}`; manifest verified до django.setup, единственный LOCALE_PATHS `{version['sole_locale_root']}`. [Manifest](locale-manifest.json).

## Свежие проверки и команды

[Ledger](commands.jsonl), [tools](tools.json), [read-only readback](readback.json), [runtime](runtime-version.json), [preservation](verification.json).

- `.venv/bin/python {HERE.relative_to(ROOT)}/bootstrap.py`: exit1 на собственной seed ошибке после успешной миграции; последующее resume завершено exit0.
- `runtime.py check`: exit0, 0 issues. `runtime.py test catalog.testcases.test_place_qa08_district_localization`: 2 tests PASS, exit0. Это targeted locale check, не полная module01 regression.
- `build_isolated_locales.py build/verify --compiler native`: exit0; 3 текущих каталога. Собственный native probe: build/verify PASS и stale-source rejection с ожидаемым exit1.
- Исходная helper suite `python -m unittest discover -s scripts/tests -p test_build_isolated_locales.py`: exit1, 9 tests, 6 failures/1 skip/2 passes. Шесть failures: hardcoded wsl.exe отсутствует на Linux; два passing negative tests не являются доказательством компиляции. Windows junction NOT RUN. Тест/его assertions не изменены и не выдаются за PASS.
- `.venv/bin/python {HERE.relative_to(ROOT)}/runtime.py readback`: exit0, READ ONLY transaction, statement timeout10s/lock timeout2s, aggregate counts; внешнее соединение отвергнуто.
- `playwright-cli -s=kidsmap-start-20261012-r1 open about:blank --browser chrome`: exit0. Chrome {browser['browser']}.
- `playwright-cli -s=kidsmap-start-20261012-r1 run-code --filename {HERE.relative_to(ROOT)}/browser-smoke.js`: final exit0, AZ/RU/EN homepage+admin login 4 HTTP200, 0 pageerrors/0 local HTTP>=400. Google Fonts deliberately blocked; font fallback возможен. 4 native viewport PNG, [manifest](screenshots-manifest.json). RU390 PNG визуально просмотрен; full visual acceptance не заявлен.

## Ошибки собственной обвязки и ограничения

- Seed attempt1 повторно создавал EDU, которую уже создаёт taxonomy migration; исправлен собственный fixture setup на get_or_create, без сброса DB/потери данных. Raw failure сохранён в ignored scratch; ledger фиксирует exit1.
- Первый browser probe вызвал unavailable URL global в CLI sandbox. Сохранён [attempt1](browser-smoke-attempt1.txt), собственный QA script исправлен, final result отдельно. CLI exit0 сам по себе не доказывает успех: final JSON/страницы проверены.
- Reused venv: Python3.12.3/Django6.0.2/psycopg3.2.10, остальные версии в tools.json. Redis/mysqlclient отсутствуют; profile использует PostgreSQL+LocMem, поэтому startup прошёл. Полная parity с requirements и полный Django/JS corpus NOT RUN. Node20.20.2 доступен; все Node regression dependencies/test suites не проверены.
- Full module01, lifecycle/save/moderation/publication, роли/ACL, concurrency/recovery, полная states×18 cells matrix, остальные modules, real providers/GPS/OAuth/GA/SMTP/IndexNow, devices/screenreader/production NOT RUN. Приложение не исправлялось; historical PASS не подтверждает эти области.

## Сохранность и handoff

10 final checks PASS, input missing0; foreign running container IDs preserved, active_run NONE unchanged. Стенд оставлен запущенным. Собственная browser session закрывается после smoke; чужие сессии не затрагиваются. Нет commit/push/deploy/production, сбросов или чужих остановок.

Для продолжения: [полный ACCEPT-01 prompt](next-prompt.txt). Это следующий отдельный выбранный scope, сейчас не выполняется. При reuse подтвердить HEAD/source/locale gate заново. Для перезапуска только собственного процесса проверить PID и cmdline из server.json, завершить только его и запустить `.venv/bin/python {HERE.relative_to(ROOT)}/runtime.py serve`; не запускать bootstrap повторно и не reseed существующую DB. Credentials остаются в scratch; не переносить в Git.

Документация Django6.0 для settings initialization/LocMem/email проверена через Context7: https://docs.djangoproject.com/en/6.0/topics/settings/ и https://docs.djangoproject.com/en/6.0/topics/email/ .
''')
print(json.dumps({'checks':checks,'url':server['url'],'report':str(HERE/'REPORT.md')}))
