# Validation C — изменение schedule_mode

Дата: 2026-09-08. Вопрос: «Что нужно проверить при изменении schedule_mode?» Режим: AUDIT ONLY, post-update validation. Execution identity: runtime worker `/root/backend_discovery`, последовательно прочитал обновлённые `.agents/agents/kidsmap-orchestrator/agent.md` и `.agents/agents/django-reviewer/agent.md`; отдельных агентов не запускал. Это проверка обновлённых инструкций на реальном impact-вопросе, не application regression PASS.

## Routing и scope

Lead: **django-reviewer**. Он определяет смысл режимов и согласованный контракт draft → submit → moderation → publication → public visibility. Минимальная следующая поддержка: **database-reviewer** для изменения хранимых значений/дней и migration safety, **seo-reviewer** для openingHours/Event, **integration-reviewer** для матрицы инвариантов. При изменении редакторов затем последовательно frontend-admin (admin/volunteer/importer), frontend-reviewer (owner/public), browser-qa; security-reviewer только при изменении permission/proposal boundary. Это план handoff, не заявление об исполнении этих ролей. Не более трёх support одновременно.

Порядок: backend impact и semantic decision → DB/SEO review → конкретный план и разрешённая реализация → integration checks → затронутый frontend/browser → orchestrator сверяет evidence. В текущем запуске остановка после рекомендаций; запись разрешена только в этот отчёт.

## Snapshot, инструменты и повторное использование

`git rev-parse HEAD` вернул `d75b34f4db5d4ba484cf8392ff3ae0c9939031e2`. По handoff root рабочее дерево в начале чистое; сейчас agent-system документы изменяются root параллельно. PRODUCTION сейчас UNKNOWN, подключения не было. Исполняемый application code не менялся этим worker.

Ранее этот же worker исследовал pricing/schedule до обновления prompts. Этот контекст использован для навигации, а критические schedule выводы ниже перечитаны после обновления. Холодный запуск нового native Codex adapter этим не доказан. Broad architecture обзор не повторялся: используется discovery handoff.

После обновления: 5 Codebase Memory запросов: `list_projects`, `index_status`, `search_graph` (place_schedule, три нужных символа, total=3, has_more=false), `trace_path` inbound depth=1 для `sync_place_schedule` (два caller: form mixin save_schedule и legacy command _apply), `check_index_coverage` (16 точных application/test путей). Latest checked coverage generation `2026-09-08T05:29:58Z`: все 16 `no_recorded_issue`, `metadata_match`; это best-effort, не полнота call graph. `index_status` ready, но содержит частичные template parses и intentional exclusions. Его полный output оказался избыточным: следующий runner должен извлекать только root/status/counts/relevant gaps, не печатать весь список.

Source checks: четыре read-only shell вызова с `cat`, bounded `sed`, literal `rg` и `git rev-parse HEAD`. Первый прочитал 5 updated instruction/knowledge paths; второй — routing/registry и literal consumer matches; третий — источник formatter/form/importer/volunteer и HEAD; четвёртый — enum/readiness/owner rules/public query/export/SEO/review и test labels. Никаких application/DB/browser команд. Coverage проверена для: `models/place.py`; `services/{place_schedule,place_readiness,permanent_place_rules,content_quality,seo,volunteer_places}.py`; `forms.py`; `volunteer_forms.py`; `domain_admin/place.py`; `management/commands/migrate_legacy_schedules.py`; четырёх test modules ниже (всё под `src/catalog`), плюс `static/admin/js/kidsmap_place_json_import.js`. Дополнительный literal поиск test labels owner/admin/volunteer — навигация для будущего запуска, не доказательство покрытия.

## Evidence-backed impact

| Boundary | Проверенный AS-IS и требуемая проверка |
|---|---|
| Model | `src/catalog/models/place.py:28`, `Place.SCHEDULE_MODE_CHOICES`: regular, always_open, by_appointment, variable, events. Изменение choices требует отдельно проверить migration state, сохранённые значения и обратную совместимость; добавление enum не означает готовность consumers. |
| Parse / save | `services/place_schedule.py:parse_schedule_payload` возвращает default при malformed JSON. `forms.py:149` `_clean_schedule_editor` показывает interval errors только для regular; `save_schedule:174` синхронизирует только regular. `sync_place_schedule:415` сначала удаляет прежние дни. Нужно проверить invalid payload, regular→other→regular, транзакции и сохранность часов; source alone не доказывает runtime потерю данных. |
| Draft / submit / publish | `place_readiness._check_schedule:276` требует meaningful structured hours для regular; другие режимы не требуют Event. `permanent_place_rules.publication_errors:34` принимает legacy text для regular. Это owner/admin расхождение; owner также имеет отдельный 120-character/price gate. Public queryset `content_quality.py:253` допускает текст/дни или явно перечисленные четыре nonregular режима. Новый режим должен попасть в правильный контракт, а не автоматически получать publication. Existing-live admin compatibility — отдельный сохранённый контракт из discovery, не повод требовать readiness от всех legacy public записей. |
| Public modes | `place_schedule.build_public_schedule_rows:514`: always_open/by_appointment — labels; variable — localized note/default; events — будущие events или events_empty; regular — structured rows, иначе legacy text. `build_open_status:616`: always_open=true; regular считает время/день; прочие дают `{}`. Нельзя показывать «закрыто» там, где часы неизвестны. Проверить midnight/overnight/weekday/timezone, closed/24h days. |
| JSON | `static/admin/js/kidsmap_place_json_import.js:setStructuredSchedule:80` принимает массив, JSON string или days-wrapper и emits `km:schedule-import`; импорт :490 принимает schedule_days/structured_schedule/локализованный alias. Prompt :271 имеет ручные пояснения пяти режимов и fallback enum. `PlaceAdmin.export_place_json_view:3967` экспортирует mode/notes, но в полном payload нет structured days и legacy schedule. Полный schedule export→import round trip сейчас нельзя обещать. |
| Volunteer | `volunteer_forms.py:CONTENT_FIELDS` включает mode/text/notes; initializer отдельно нормализует hostile schedule JSON. `services/volunteer_places.py` сохраняет structured proposal, review атомарен; перед изменением published candidate проверяет readiness (:185), затем `form.save_schedule(candidate):197`. Проверить proposal/review/stale revision и невозможность обойти boundary. |
| SEO | `services/seo.py:415` отдельно строит 24/7 openingHours и regular day intervals. Для variable/by_appointment/events не выдумывать регулярные часы; изменение режима требует явного решения schema. Event-сущность и временный Place не взаимозаменяемы. |
| Legacy | `management/commands/migrate_legacy_schedules.py:_plan_for_place` пропускает nonregular и уже содержательные дни; ambiguity → manual_review; `_apply` использует atomic и повторную проверку. Проверить idempotency, interrupted runs/concurrency и сохранность текста на disposable DB. Не запускать command на production ради проверки. |

## Future verification / handoff

Ни один тест не выполнен. Будущий integration-reviewer сначала подтверждает изоляцию: `DJANGO_TESTING=1`, disposable DB/cache/media/email, выключенные external integrations, отсутствие production credentials. Затем в таком окружении точный основной набор:

```sh
DJANGO_TESTING=1 python manage.py test catalog.testcases.place_readiness catalog.testcases.legacy_migrations catalog.testcases.test_json_roundtrip_audit catalog.testcases.test_place_json_and_pricing_modes
```

Owner/admin/volunteer labels выбрать по изменённым callers: `catalog.testcases.owner.TestOwnerPlaceManagementAndPermissions`, `catalog.testcases.place_readiness.PlaceAdminFormReadinessTests`, `catalog.testcases.test_volunteer_admin`. Проверить discovery и соответствие fixtures до запуска; одних env-флагов недостаточно для изоляции. `catalog.testcases.place_readiness`/`legacy_migrations` надо задавать явно — discovery context установил, что `catalog/tests.py` не импортирует их.

Acceptance: все пять режимов; empty/all-closed/multiple/overlapping/24h/overnight intervals; malformed payload без непредусмотренной порчи сохранённых дней; draft vs submit vs new/republication vs existing-live compatibility; owner/admin/volunteer round trips; export/import days omission отдельным expected limitation или согласованным change; no upcoming Event не блокирует events-mode; catalog/map/detail/readiness/SEO результаты согласованы с утверждённым контрактом. Проверять direct POST и tampered mode, а не только dropdown. Тестовые failures сначала классифицировать: baseline/regression/environment; названия существующих тестов не доказывают, что они проходят.

Browser handoff после согласованных UI изменений: AZ/RU/EN, 390/768/1024/1280/1440, при серьёзном redesign 320/360; DOM/console/network/static404/overflow/keyboard/focus; mode switch, error persistence, importer events и save/reload. Реальное public/map rendered поведение сейчас UNKNOWN.

## Оценка updated prompts и UNKNOWN

Updated orchestrator/engineering contract успешно направляют к одному backend lead, source-first verification после graph, distinct publication contracts, минимальной поддержке и честным NOT RUN границам. Schedule knowledge точно ведёт к реальным symbols и отмечает export omission/owner divergence. Django definition теперь явно включает volunteer и не выдаёт split rules за единый AS-IS.

Остаточные улучшения prompts: приводить компактную проекцию `index_status` (полный ответ расходует контекст); schedule checklist можно явно дополнить regular→nonregular→regular с сохранёнными днями и разницей unknown/open=false. `READ FIRST` содержит большой обязательный список исторических страниц; для bounded задачи инженерный контракт разрешает reuse, но стоит яснее отделить обязательные current snapshot/contract от conditional domain pages. Эти замечания не блокируют source-only impact ответ.

UNKNOWN: текущие production значения/схема/числа, concurrency behavior, текущая suite baseline, rendered translations/map consistency, native adapter fresh-session loading. Изменений application нет; data/schema migration или унификация owner/admin правил требуют отдельного конкретного плана в разрешённом scope.

## Post-feedback revalidation

2026-09-08, тот же worker. После исправлений root повторно прочитаны `.agents/rules/engineering-contract.md:Discover with bounded context`, `.agents/knowledge/schedule.md` и actual `src/catalog/services/place_schedule.py:616–668` (`build_open_status`). Команда: bounded `sed` двух файлов + `cat` компактного schedule knowledge; exit 0. Дополнительных graph запросов не было: использована уже проверенная coverage и неизменённый application snapshot.

Результат: замечания к prompts выше устранены. Engineering contract теперь требует компактную проекцию index status с сохранением coverage/pagination limits и прямо определяет READ FIRST как scoped navigation. Schedule verification явно включает regular → other → regular и retained days/text. Документация верно различает `{}` (невозможно определить) и populated `is_open=false` (подтверждённое закрытие). В source always_open возвращает populated true; остальные nonregular режимы возвращают `{}`; regular closed-day возвращает populated false. Это согласуется с обновлённым требованием не изображать неизвестные часы как закрытие.

Revalidation подтверждает исправление инструкций и их соответствие прочитанному source; application tests/browser/DB по-прежнему NOT RUN. Новых блокирующих prompt deficiencies в этих исправленных разделах не найдено.
