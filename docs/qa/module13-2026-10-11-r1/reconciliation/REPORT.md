# Module13 — историческая сверка и coverage handoff

Роль kidsmap-orchestrator; execution identity `/root/cross_reconcile`; definition `.agents/agents/kidsmap-orchestrator/agent.md`. Дата2026-10-11. AUDIT ONLY, ownership только `reconciliation/`. Root владеет свежим стендом/браузером/итоговым решением. Приложение, rules, migrations, assertions, journal и чужие stands здесь не изменялись.

## 1. Состояние области

Checkout `C:/kidsmap`, branch `task33-progress`, HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`; dirty WORKTREE, parent active_run `NONE`. Прочитаны13 исторических REPORT файлов (01r1/r2 +02–12), исходные finding-файлы и canonical module13 prompt. Исторические наблюдения не fresh evidence. Production UNKNOWN/NOT RUN; runtime подключений этим исполнителем не было. Явный [свежий handoff root](fresh-root-evidence.json) импортирует только три перепроверенные причины и новый root finding; native browser лично выполнял /root. [Полный inventory](historical-findings.json), [scenario/role/snapshot coverage](coverage.csv), [source route/model/admin declarations](source-coverage.csv).

Один HEAD скрывает изменение WORKTREE: у recorded manifests модулей01–10 сейчас16 изменённых файлов; у01–04 также более узкий manifest2776 без root templates, у05–10 manifest2784. Модуль10 после drift имеет отдельный final current-snapshot2788 и fresh-repeat claims в своём историческом отчёте; entry результаты не приравниваются к current. Модули11/12 recorded2788 hashes совпадают с диском, но старые фикстуры/результаты всё равно не свежая приёмка13. Подробные drift arrays сохранены в JSON.

| Модуль | Исторические IDs/P | Recorded manifest→disk | Исторический отчёт |
|---|---|---|---|
| 01 Постоянные места | 7: {'P2': 5, 'P1': 1, 'P3': 1} | 2776 recorded, 16 changed, 0 missing | [REPORT](../../module01-2026-10-09-r2/REPORT.md) |
| 02 Организации/подключения/сотрудники | 4: {'P2': 3, 'P3': 1} | 2776 recorded, 16 changed, 0 missing | [REPORT](../../module02-2026-10-09-r1/REPORT.md) |
| 03 Специалисты/сотрудничество | 3: {'P2': 2, 'P3': 1} | 2776 recorded, 16 changed, 0 missing | [REPORT](../../module03-2026-10-10-r1/REPORT.md) |
| 04 Мероприятия | 3: {'P2': 3} | 2776 recorded, 16 changed, 0 missing | [REPORT](../../module04-2026-10-10-r1/REPORT.md) |
| 05 Программы/занятия/группы/цены | 8: {'P2': 6, 'P3': 2} | 2784 recorded, 16 changed, 0 missing | [REPORT](../../module05-2026-10-10-r1/REPORT.md) |
| 06 Публичный каталог/карта | 4: {'P2': 3, 'P3': 1} | 2784 recorded, 16 changed, 0 missing | [REPORT](../../module06-2026-10-10-r1/REPORT.md) |
| 07 Аккаунт/права/приглашения | 5: {'P2': 5} | 2784 recorded, 16 changed, 0 missing | [REPORT](../../module07-2026-10-10-r1/REPORT.md) |
| 08 Модерация | 8: {'P2': 8} | 2784 recorded, 16 changed, 0 missing | [REPORT](../../module08-2026-10-10-r1/REPORT.md) |
| 09 Отзывы/избранное/уведомления | 9: {'P2': 8, 'P3': 1} | 2784 recorded, 16 changed, 0 missing | [REPORT](../../module09-2026-10-10-r1/REPORT.md) |
| 10 Настройки/разделы/общие страницы | 15: {'P1': 1, 'P2': 12, 'P3': 2} | 2784 recorded, 16 changed, 0 missing; final 2788 recorded/0 changed | [REPORT](../../module10-2026-10-10-r1/REPORT.md) |
| 11 SEO/URL | 7: {'P2': 6, 'P3': 1} | 2788 recorded, 0 changed, 0 missing | [REPORT](../../module11-2026-10-11-r1/REPORT.md) |
| 12 Аналитика | 8: {'P2': 6, 'P3': 2} | 2788 recorded, 0 changed, 0 missing | [REPORT](../../module12-2026-10-11-r1/REPORT.md) |

## 2. Сильные стороны

Все12 областей имеют собственные dated reports, snapshot/evidence и отрицательные сценарии. Исходные IDs и repair prompts сохранены. Повторный01-r2 сохраняет пять исходных ID и добавляет два, без создания дублей. Module09 отдельно повторял MOD-QA-03 без нового SOCIAL ID. Source guard и явные NOT RUN/SIMULATED границы доступны в reports; это структура доказательств, а не текущий product PASS.

## 3. Реальные проблемы

Исторический inventory:86 finding occurrences →81 unique IDs, P0=0/P1=2/P2=67/P3=12. После объединения только проверенных одинаковых причин —77 исторических buckets. Семь PLACE-QA-01…07 имеют последующий repair claim; они не объявляются автоматически свежими OPEN или PASS. Остальные74 ID (71 buckets) исторически не имеют такого repair claim. Из явного parent handoff свежо FAIL только SITE-QA-01 P1, ANALYTICS-QA-01 P2 и общий ORG-QA-02/ACCESS-QA-03 P2; для остальных fresh status NOT RUN в этом inventory. Full current OPEN count принадлежит root итоговому отчёту.

| Проверенный общий root cause | Сохранённые IDs | Что объединяется / граница |
|---|---|---|
| NETWORK-GRANT-UI | ORG-QA-02, ACCESS-QA-03 | One missing management surface for network grants and invitations; same organization_workspace.html markup and invitation-only JS. Canonical business_team action/CAS and recipient inbox; retain separate recipient-decline ACCESS-QA-02. |
| COMPILED-LOCALE-FRESHNESS | PLACE-QA-06, EVENT-QA-01, PUBLIC-QA-03, SITE-QA-07 | Existing ignored compiled catalogs differ from tracked PO; failure applies to runtime locale profile. PLACE-QA-06 has later isolated-builder repair claim. Verify effective LOCALE_PATHS, frozen PO hashes and manifest before startup; rebuilding does not repair missing/fuzzy/wrong source translations. |

ORG-QA-02/ACCESS-QA-03 source проверен: grants/invitations строки без action controls в organization_workspace.html:462–496; JS с255 обслуживает приглашения. ACCESS-QA-02 recipient decline отдельно: другая поверхность/переход. SITE-QA-01 media write и ANALYTICS-QA-01 statistics read имеют похожий missing-model-permission pattern, но разные custom admin handlers, scopes и acceptance; их IDs не объединены.

Compiled freshness объединяет environment фактор, не все переводы. EVENT-QA-03/OFFER-QA-06/ACCESS-QA-05/ANALYTICS-QA-08 дополнительно содержат source missing/fuzzy/wrong meanings. PLACE-QA-06 later repair — isolated build helper, не массовая замена shared ignored MO. Effective locale profile нужен в каждом свежем результате. Дополнительно выполнен [свежий direct asset readback](current-shared-locale-readback.json): shared ignored MO сверены с PO через GNUTranslations без Django.setup/DB/locale writes. Это asset/source evidence, не rendered browser или attestation effective root LOCALE_PATHS.

Все81 finding и исходные links/prompts: [repair queue](repair-queue.md), JSON включает evidence_links/source/dependencies/severity и SHA исторических файлов. Новые CROSS-QA IDs этим исполнителем не назначаются. Parent передал новый CROSS-QA-01 P2: после native будущего переноса Event остаётся на своей карточке/в общей афише, но исчезает из feed организатора; root оформляет отдельный finding/prompt.

| Fresh parent scenario | Роль/язык/ширина | Результат/доказательство |
|---|---|---|
| staff-without-model-permission-media-denied | staff/ru/1440 | FAIL: [row1](../../module13-2026-10-11-r1/acl-native.result.txt), [PNG](../../module13-2026-10-11-r1/screenshots/staff-media-no-permissions-1440.png) |
| staff-without-permission-native-logo-upload-denied | staff/ru/1440 | FAIL: [row2](../../module13-2026-10-11-r1/acl-native.result.txt) |
| unauthorized-logo-public-effect | staff/ru/1440 | FAIL: [row3](../../module13-2026-10-11-r1/acl-native.result.txt), [PNG](../../module13-2026-10-11-r1/screenshots/staff-global-logo-public-1440.png) |
| staff-without-analytics-permission-denied | staff/ru/1440 | FAIL: [row4](../../module13-2026-10-11-r1/acl-native.result.txt), [PNG](../../module13-2026-10-11-r1/screenshots/staff-analytics-1440.png) |
| network-employee-revoke-control-available | owner/ru/1440 | FAIL: [row7](../../module13-2026-10-11-r1/cross-effects.result.txt), [PNG](../../module13-2026-10-11-r1/screenshots/org-team-controls-1440.png) |
| network-employee-native-revocation | owner/ru/1440 | NOT RUN: [row8](../../module13-2026-10-11-r1/cross-effects.result.txt) |
| future-rescheduled-event-remains-in-organizer-feed | guest/ru/1440 | FAIL: [row3](../../module13-2026-10-11-r1/event-cross.result.txt), [PNG](../../module13-2026-10-11-r1/screenshots/organization-event-after-1440.png) |

## 4. Tech debt

Исторические matrix schemas отличаются: module04 разделяет geometry/document-language и copy_status вместо одного status; module07 хранит observations/not_run; module10 строки с entry/current snapshot. Coverage CSV сохраняет исходный status в отдельной колонке, fresh_module13_status всегда NOT RUN в этом support scope. Counts не суммируются в количество уникальных transactions/tests.

Source map охватывает static declarations моделей (включая abstract/proxy candidates), явные admin.register decorators и path/re_path calls. Это navigation mapping, не runtime app registry/доказательство coverage каждого endpoint. Dynamic ORM, proxy replacement registration и settings gates требуют root native/source подтверждения.

## 5. Risks

Исторический SITE-QA-01 P1 global logo upload/delete без model permission важнее layout polish. PLACE-QA-03 P1 имеет более позднее исправление в грязном WORKTREE: publication.propose:355–369 содержит scalar projection rebase; root обязан воспроизвести mixed price+identity→submit→approve, CAS и live preservation на новом стенде. Само наличие patch не PASS.

Граф C-kidsmap callable/ready, но cited paths coverage_unavailable/partial и metadata_changed, recorded metadata truncated. Бounded source fallback использован. ajax_upload inbound trace дал0callers, однако site.py:get_urls явным образом подключает handler через admin_view; нулевой graph trace не доказательство dead code. [Компактные graph bounds](graph-summary.json). Реальные SDK/GA/SMTP/OAuth и production не использованы.

## 6. Dead/legacy candidates

STATUS UNKNOWN/ACTIVE; удаление не предлагается. Legacy scalar pricing, temporary Place, readonly diagnostic admins, conversion/SEO metadata models и compatibility facades не объявлены dead. Coverage gaps в conversion/SEO audit writes не являются дефектом или основанием удалить model/table. DB/data/deletion audit NOT RUN.

## 7. Tests gaps

В этом support scope выполнены document inventory, SHA drift comparison, AST declarations, direct assets readback и bounded source review. Собственных backend/JS/browser lifecycle tests нет: NOT RUN;7 явно импортированных parent native rows имеют6FAIL/1NOTRUN, атрибуция сохранена. Coverage CSV имеет20362 записей: {'HISTORICAL_OBSERVATION': 20167, 'HISTORICAL_EXPLICIT_GAP': 188, 'FRESH_PARENT_HANDOFF': 7}; исторические строки fresh_module13_status NOT RUN. [18 обязательных сценариев/внешних/операционных gaps](mandatory-gaps.csv) остаются checklist, их полный результат root ведёт отдельно.

Команды: `.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/reconciliation/inventory.py`; `.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/reconciliation/asset_readback.py`; `.venv/Scripts/python.exe docs/qa/module13-2026-10-11-r1/reconciliation/assemble.py`; source reads `rg`/PowerShell Get-Content и Codebase Memory list_projects/index_status/get_architecture/search_graph/trace_path/check_index_coverage. Native script exits/artifact validation отдельно в [command-results.json](command-results.json) после проверки. Ранний ad-hoc metadata-print attempt имел собственный IndexError при поиске отсутствующего module04 matrix.json (там CSV), assemble first attempt — QA parser list/dict mismatch ([attempt](assemble.attempt1.json)); они не считаются app/test failures и не поддерживают findings.

Исторические обязательные ограничения: full suites ранее не запускались; Windows donor/socket/tmp preflight bodies зачастую NOT RUN; native employee revoke/role/cancel и recipient decline отсутствуют; полный Specialist author rejected proposal correction/все practice permutations не установлены; exact recurring group positive blocked; real device/engine/screenreader/multiworker cache/real integrations не проверены. Root должен продолжить независимые проверки, а blocked переходы оставить NOT RUN с доказанной причиной.

## 8. Recommendations

Порядок: (1) fresh SITE-QA-01 permission boundary + отдельный ANALYTICS-QA-01; (2) fresh repaired PLACE01–07 в фактическом locale profile, особенно pricing candidate/CAS; (3) canonical network request/confirm, employee controls/recipient decline, organization autosave и stale offerings restore; (4) group removal/recurring/moderation; (5) files/private docs/primary delete/photo moderation; (6) OFF/ON/direct legacy URL, review pagination, slug aliases/sitemap/SEO editor; (7) analytics origin/failure handling; (8) build freshness и отдельно source translations; (9) geometry/focus/copy. Исходные самостоятельные prompts linked в repair queue. Перед любым исправлением нужен конкретный user-approved scope.

Named handoff: `/root` kidsmap-orchestrator — соединить inventory с собственными fresh module13 rows без автоматического наследования PASS/OPEN; django-reviewer — disputed workflow/permission rules; integration-reviewer — full isolated suites/Windows guards; browser-qa lead — ten-step native pipeline и18 cells. Acceptance: каждый fresh статус имеет новый snapshot/result/PNG или честный NOT RUN; оригинальные IDs не потеряны.

## 9. P0/P1/P2/P3

Исторические unique IDs: P0=0, P1=2, P2=67, P3=12; repaired claim7 (1P1/5P2/1P3), remaining historical unresolved claims74 (1P1/62P2/11P3). Это не новый current defect count. Ограниченный свежий parent handoff:1P1/2P2 historical root causes (4IDs), плюс новый parent CROSS-QA-01 P2. Остальные не повышены до OPEN/PASS по истории. Общий project PASS и production readiness не заявляются.
