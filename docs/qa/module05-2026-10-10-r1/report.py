"""Generate own nine-section audit report using current evidence counts."""
from pathlib import Path
import json,collections
P=Path(__file__).resolve().parent;R=P.parents[2];s=json.loads((P/'results-summary.json').read_text(encoding='utf-8'));snap=json.loads((P/'snapshot.json').read_text(encoding='utf-8'))
runrows='\n'.join('| '+r['name']+' | '+str(r['rows'])+' | '+str(r['raw_counts'])+' | '+('HARNESS ERROR' if r['harness_error'] else '0 CLI; inspected JSON')+' |' for r in s['selected_runs'])
text=f'''# Модуль05 — программы, занятия, группы, тарифы, расписание

2026-10-10 · module05-2026-10-10-r1 · **DONE — FAIL**. Выполнен только05; следующий06,13 после остальных. Исполнитель `/root`, один lead, sequential canonical orchestration/backend/database/browser/admin/public review; независимые специалисты не запускались. Definition: `.agents/agents/kidsmap-orchestrator/agent.md`, active registry. AUDIT ONLY, app/rules/migrations/assertions не исправлялись, commit/push/deploy/production не выполнялись.

## 1. Состояние области

Фактический checkout `C:/kidsmap`; branch `{snap['branch']}`; LOCAL HEAD `{snap['head']}`. Dirty WORKTREE при входе — QA/docs/plans, включая чужие reports; [полный snapshot](snapshot.json). active_run **NONE**, чужой файл implementation-status.md не изменён. Production **UNKNOWN / NOT RUN**. Для AS IS исследован весь текущий source manifest, а не только commit:2784 файла src/static/config/locale/root templates, digest `{snap['source_digest']}`. Existing compiled .mo включены; их сборка не выполнялась.

Новый собственный stand: `http://localhost:8816`, PostgreSQL `127.0.0.1:55436`, container `kidsmap-module05-20261010-r1`, DB module05 / test_module05. Python3.12.15, Django6.0.2,175 migrations. `DJANGO_TESTING=1`, loopback-only socket guard, no checkout .env loading, distinct LocMem cache/email, cookies, media/private-media/test-media в ignored `.tmp/module05-20261010-r1`. Только fictional owner/employee/outsider/staff,6 synthetic Places,2 organizations. Начальные окружение/role grants seeded; Program/Activity/Group/Price/review/confirm/detach под проверкой создавались и менялись UI, не ORM-save. Негативный tamper менял только исходящий native multipart на собственном stand. DB evidence читался в explicit READ ONLY transaction +10s statement timeout.

Native Chromium153.0.8010.12 на Windows, headless CLI session module05-r1. Это реально rendered browser, CSS viewport emulation; physical devices/другие engines NOT RUN. [browser metadata](browser-meta.result.txt), [isolation](isolation.json), [runtime/preservation verification](verification.json). Startup launcher проверяет source hashes, фиксирует sys.path на C:/kidsmap/src; сервер без autoreloader. `/qa/version/` только возвращает QA manifest: это не самостоятельное доказательство loaded source. Совпадение подтверждается совместно launcher assertion, проверкой current hashes всех2784 файлов и PID/command readback в verification. В браузере каждый independent native save использовал новые contexts, cache/foreign sessions не переиспользовались.

Прочитаны AGENTS.md, canonical registry/orchestrator/shared contracts/knowledge и docs/qa/content-entry-audit-2026-10-06.md как checklist, module05 prompt. Недостающие обязательные документы: **нет**. Карта Place01 не входит в scope05. Codebase Memory C-kidsmap: ready,96161 nodes/189648 edges, generation2026-10-10T07:09:29Z; metadata_changed/coverage unavailable и partial template parses. Graph — research hint; выводы сверены source. Graph caches в artifacts не сохранялись. [AS IS contract](source-contract.md).

Program принадлежит Organization; Activity — Place и optional shared Program той же сети; локальные Group age/conditions/schedule принадлежат Activity; PricingPlan — Place XOR Group. Часы Place и schedule_text группы разные. Текст общей программы и nested offers проходят candidate review, а отдельные schedule fields могут применяться immediately. Catalog AS IS фильтрует по age/category/subcategory/query и показывает соответствующий group's own price; legacy price_max/price sorting намеренно отключены.

## 2. Сильные стороны

- Native создание общей программы/связанного branch Activity и отдельного local Activity; draft/save/reload/new login/submit/approve. Несколько занятий в Place5, группы4–6/12–15/8–10, два тарифа одной группы. Native admin draft/reload/private candidate/approval, unpublish→public404→republish→public200.
- Explicit group condition confirmation сохранена; pending change даёт409; после approved изменения confirmation cleared. Common approved names/description распространились на branch до detach; pending candidate не показывался public. Пустые RU/EN пользовательские поля остались пустыми в data, public fallback честно отмечает AZ; Activity3 реальные RU/EN names сохранились.
- Все13 product types прошли UI save и чтение в новой session при one_time. exact>0, free, from, range, on_request; exact empty/0 →422 с сохранением ввода; USD retained,30 переключений price kind без зависания. Общий admission42 AZN отдельной карточки и group35 AZN показываются отдельно на public. Recurring owner Group путь FAIL, см.02.
- Пять opening modes реально сохранялись; regular7days/выходные/два интервала, overlap/reversed/incomplete →422. Group schedules сохранились отдельно. Legacy Place3 price31–35 и text schedule сохранены после unrelated edit; [state-entry](state-entry.json), [state-final](state-final.json). Events дополнительно прошёл save/reload/fresh client на чистой карточке; старый mixed-candidate reload mismatch оставлен FAIL и связан с restoration risk07, не замаскирован новым PASS.
- Foreign activity/group/plan IDs →422; insufficient employee/outsider Program→404; invalid second group не применил изменение первой; [atomic evidence](atomic-evidence.json). Две реальные вкладки Program дали409 и retained input в18 клетках; duplicate Enter дал только1 native POST; aborted network сохраняет ввод и успешный retry. Все процессы использовали UI/native sessions.
- Native detach preview/consent/confirm: shared Activity1 стал local snapshot; Groups/Plans целиком unchanged до/после; employee network edit revoked. Photo/owner preservation только initial fixture invariants, отдельный forensic сравнение всех media metadata NOT RUN. [pre-detach](state-pre-detach.json), [post-detach](state-post-detach.json), [native detach](detach.result.txt).
- Native JSON v2 download→import textarea→invalid JSON→Escape→confirm import→admin save draft→review→reexport сохранил nested pricing и IDs. [roundtrip](roundtrip.result.txt), [fictional export](pricing-export-v2.json). Это тарифный roundtrip; structured hours/legacy schedule/media bytes не входят в export.

## 3. Реальные проблемы

**8 OPEN:6 P2 +2 P3.** Каждая имеет отдельный repro, evidence, cause/hypothesis, scope/dependencies и копируемый prompt: [FINDINGS](FINDINGS.md).

| ID | Приоритет | Поведение |
|---|---|---|
| [OFFER-QA-01](findings/OFFER-QA-01.md) | P2 | Удалённая Group остаётся DB/public после approved candidate |
| [OFFER-QA-02](findings/OFFER-QA-02.md) | P2 | Owner recurring tariff требует count, которого нет в UI |
| [OFFER-QA-03](findings/OFFER-QA-03.md) | P2 | Ошибка price ведёт focus к program select |
| [OFFER-QA-04](findings/OFFER-QA-04.md) | P2 | При1024px schedule interval/copy controls обрезаны |
| [OFFER-QA-05](findings/OFFER-QA-05.md) | P3 | Admin badge требует внутреннего горизонтального скролла |
| [OFFER-QA-06](findings/OFFER-QA-06.md) | P3 | Missing AZ/EN status translations + outdated existing .mo |
| [OFFER-QA-07](findings/OFFER-QA-07.md) | P2 | Normal edit молча применяет obsolete server copy |
| [OFFER-QA-08](findings/OFFER-QA-08.md) | P2 | Declined Program owner не видит reason/proposed text |

Classification: pre-existing baseline текущего LOCAL WORKTREE. Сравнение с прошлым SHA/production **NOT RUN**; REGRESSION не установлена.06 содержит подтверждённый ENVIRONMENT компонент .po/.mo и source translation gaps. Отказ программы повторён: revision1 declined с persisted reason, owner всё равно показывает только статус и approved text. [rejection evidence](rejection-repro.result.txt).

## 4. Tech debt

Error messages одновременно serving copy и машинный routing; nested omission не согласован с UI remove; working copies требуют явной связи с candidate/source version. Locale source/compiled artifacts расходятся. Это выводы конкретных boundary checks, не предложение общего refactor. Старые отчёты не являются свежим доказательством.

## 5. Risks

07 проявился после сохранения/публикации B при ordinary /edit/; /edit/?fresh=1 reload ранее PASS. Source form version3, draft1, отсутствует conflict warning. Это разные наблюдаемые пути. Потеря production данных не доказана.01 сохраняет неверное публичное предложение после успешного moderator decision.05 ограничен начальной читаемостью: overflow-auto позволяет внутренний scroll, отсутствие любой возможности прочитать не заявляется.

External font/map/SDK/CDN/geolocation transport блокирован; **SIMULATED absence**, integrations NOT RUN. Console record из clipping run:152 ERR_FAILED именно в этом blocked setup,0 pageerrors,0 local HTTP>=400. Native negative422/409/404 ожидаемы; matrix наблюдала1 draft409. Контактный fake номер не проверялся внешним звонком. Никаких live OAuth/email/payment/API запросов.

Чужие listeners8811/6112,8812/40848,8815/43232 сохранены при final readback; чужие module containers55431–55435 не управлялись. Отдельный чужой55440 наблюдался в середине и отсутствовал позднее; мы не выдавали ему stop/remove/mutation, дальнейшая судьба UNKNOWN. Собственный HTTP PID40212 и volume перечислены в verification. New foreign QA/plans inventoried и не редактировались.

**Preservation comparison: concurrent drift.** Из4460 prior files (без journal) пять чужих файлов `docs/qa/place-qa05-plan-2026-10-10/` изменились относительно entry: browser-command-ledger.jsonl, command-ledger.jsonl, pw.py, runtime.py, server-process.json. Origin UNKNOWN; мы не писали в этот каталог. Текущие версии сохранены, не заменены entry snapshot. Strict verification native exit1 и pass=false именно из-за этого сравнения; source_changed пуст, own_scope_integrity_pass=true, active_run unchanged, row05 only, secret/link/syntax/git-diff checks0. Это не application failure и не повод откатывать параллельную работу. [Hashes/details](verification.json).

## 6. Dead/legacy candidates

Удалений и dead-code решений нет. Legacy scalar prices/text schedules используются и пережили unrelated UI edit. Model/service archive существует; inspected business/owner editor не предоставляет native archive action. Native archive **NOT RUN**, существующие backend tests archive PASS; это не подтверждение browser archive flow и не разрешение удаления DB structures.

## 7. Tests gaps и точные результаты

Fresh final Django **250/250 PASS**, native exits0/0:119 tests48.366s +131 tests39.866s,13 targeted suites. [tests.log](tests.log), [tests-extra.log](tests-extra.log), [exact commands](COMMANDS.md), [native command JSON](tests-command.json), [extra commands](tests-extra-command.json). Existing assertions unchanged. Первый119 запуск:13 detach failures из-за QA CSRF cookie name; [raw environment attempt](tests-cookie-environment-attempt1.log). Исправлен только собственный test-process adapter на csrftoken, app/server cookie isolation сохранена; same tests119 PASS. Baseline application failures в этих final suites:0; полный suite NOT RUN.

Browser matrix **{s['matrix_rows']} rows: {s['matrix_counts']['PASS']} PASS / {s['matrix_counts']['FAIL']} FAIL / {s['matrix_counts']['NOT RUN']} NOT RUN**. FAIL rows повторяют8 findings и одно retained reload mismatch; это не39 независимых дефектов. [matrix.csv](matrix.csv), [run summary](results-summary.json).288 admin tab geometry rows,324 owner/admin/public layout/keyboard/row/native foreign-access rows,18 real conflict rows и18 held-POST/error/duplicate rows плюс отдельные functional scenarios. Матрица RU/AZ/EN×360/390/768/1024/1280/1440 полностью пройдена для основных rendered filled/empty/long/open select/tab/keyboard и applicable loading/error/conflict states. Некоторые functional rows не записывали фактическую ширину/язык/роль: **UNRECORDED**, их параметры не выдумываются; новые explicit matrix cells имеют runtime width/lang. Geometry PASS не означает semantic/translation PASS.

Сохранено **{s['browser_screenshots']} fresh rendered PNG +{s['derived_images']} derived inspection crops/contact sheet = {s['screenshots']} PNG**. [sha256/pixel-size manifest](screenshots-manifest.json). Метки1440 в некоторых старых helper filenames не являются измерением viewport; actual PNG dimensions перечислены в manifest. Скриншоты повторных попыток одного имени отражают latest capture; raw attempt files сохраняются для классификации harness, не для утверждения текущего состояния.

| Native run | Rows | Raw statuses | CLI |
|---|---:|---|---|
{runrows}

Raw CLI exit0 может содержать JSON error; все results проверены. Неверные initial fixture paid→tariffs/subcategory, login selectors, escaped JS syntax, protocol body-after-navigation, wrong tab vs pill/transition wait и пропущенный import confirmation классифицированы HARNESS/ENVIRONMENT, attempts сохранены. Старая цена max25 при age13 была неверным ожиданием: текущий AS IS игнорирует price_max. Fresh corrected DOM checks подтверждают age5→25 AZN, age13→80 AZN, age8→15/18 AZN одной matched Group. [catalog corrected](catalog-corrected.result.txt). Неверное ожидание слова «Отсоединено» исправлено classification по факту «Отсоединение подтверждено», readonly program_id NULL, unchanged groups/prices и employee denial; сам raw result сохранён.

NOT RUN: native archive без exposed action, JSON v1 rendered roundtrip, full Place schedule/media export roundtrip, complete group recurring/installment positive (02), полное произведение every mutation×role×language×width, physical devices/other heights/engines, exhaustive currency/unit/billing combos и bad-range-age native mutations (backend boundaries tested), production/external integrations/full suites/previous-version regression. Никакие ограничения не повышены до PASS. [coverage rows](matrix.csv).

## 8. Recommendations

Решить восемь отдельных reviewable scopes из findings; текущий AUDIT не разрешает fixes. Затем повторить соответствующие native scenarios на новом source snapshot и начать06 отдельным запуском. Контракт удаления/архива и версии working copies согласовать с candidate/live и history; локализацию проверить на реально поставляемых .mo. [Готовый следующий prompt06](next-chat.txt). [Список всех13 исходных промптов](PROMPTS-INDEX.md).

## 9. P0/P1/P2/P3

P0/P1: подтверждённых findings нет в выполненном scope. P2:01/02/03/04/07/08. P3:05/06. Security/production аварий не заявляется. **FAIL** относится к текущей проверке05 и этим доказательствам; общий вывод «всё работает» не делается.
'''
(P/'REPORT.md').write_text(text,encoding='utf-8')
commands='''# Exact commands — module05 fresh isolated QA

PowerShell, cwd C:/kidsmap. Python native Windows, WSL только Docker. Не выполнять повторно bootstrap на существующей DB; на другом ПК использовать новый run/ports/container/settings. Scratch password генерируется seed.py и не переносится в report.

```powershell
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/prepare.py
wsl.exe -- docker run -d --name kidsmap-module05-20261010-r1 -p 127.0.0.1:55436:5432 -e POSTGRES_DB=module05 -e POSTGRES_USER=module05 -e POSTGRES_HOST_AUTH_METHOD=trust postgres:17-alpine
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/run.py snapshot
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/run.py migrate
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/seed.py
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/fixture-correction.py
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/run.py serve
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/fixture-add.py
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/fixture-admin-access.py
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/fixture-restore.py
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/tests-run.py
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/tests-extra.py
```

Bootstrap/175 migrations/fixtures exits0; fixture-correction исправлял исключительно начальные invented surroundings, до первого audited offering. Проверяемые transitions выполнялись browser; отдельные suites используют собственный test_module05, independent from stand DB.

Browser CLI start использует cached @playwright/cli, config .tmp/module05-20261010-r1/playwright.json; native Chromium binary1243. Exact session:

```powershell
node C:/Users/Ramin/AppData/Local/npm-cache/_npx/31e32ef8478fbf80/node_modules/@playwright/cli/playwright-cli.js -s=module05-r1 open --config=.tmp/module05-20261010-r1/playwright.json
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/drive.py functional3.js
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/drive.py functional4.js
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/drive.py matrix.js
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/drive.py admin-matrix.js
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/drive.py schedule-fresh.js
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/drive.py pricing.js
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/server-state.py final
node docs/qa/module05-2026-10-10-r1/check-js.cjs
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/finalize.py
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/author.py
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/report.py
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/update-journal.py
.venv/Scripts/python.exe docs/qa/module05-2026-10-10-r1/verify.py
```

Все additional browser команды, даты, native exit codes, elapsed seconds и repetitions: [command-ledger.jsonl](command-ledger.jsonl). Выполнялись также probe, functional1/2, save-probe, lifecycle, diagnostics, restore/restore-read, adversarial, multiple, admin-lifecycle, detach, roundtrip, common, catalog-corrected, conflict-matrix, events-recheck, rejection/rejection-repro, clipping/badge-diagnostic и browser-meta. Каждый .js — native run-code через drive.py; executed credential не сохраняется, .effective.js содержит placeholder. Последовательность существенна: это fixture run, а не idempotent suite. По месту ledger raw outputs использованы как evidence; audit conclusion не приравнивает CLI0 к PASS.

119 final test native command и exit0: [tests-command.json](tests-command.json).131 extra и exit0: [tests-extra-command.json](tests-extra-command.json). Первый cookie-environment119 exit1 (13 failures), собственный adapter corrected без app/assertion edits, repeat0. Verify/generation commands exits записаны в [verification.json](verification.json) и [verification-command.json](verification-command.json). Source and prior hashes сохранены [snapshot](snapshot.json), [preservation](preservation-entry.json). No commit/push/deploy/cleanup.
'''
(P/'COMMANDS.md').write_text(commands,encoding='utf-8');print('Nine-section report and exact command handoff written.')
