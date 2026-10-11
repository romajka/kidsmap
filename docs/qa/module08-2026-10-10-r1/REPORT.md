# Модуль08 — админка, модерация и волонтёрский кабинет

**DONE — FAIL**, fresh run module08-2026-10-10-r1,2026-10-10,Asia/Baku. Восемь OPEN P2; application fixes/commit/push/deploy/production отсутствуют. Execution identity: один /root, роли orchestrator/frontend-admin/Django-security/browser-qa последовательно; независимые specialists не запускались. Definitions: .agents/agents/kidsmap-orchestrator/agent.md, frontend-admin и browser-qa; scope строго один модуль08. Исторический content-entry audit использован как checklist.

## 1. Состояние области

Checkout **C:\kidsmap**, branch **task33-progress**, HEAD **8d188b316f800fbedf0b1e376905dfd4924cb1b6**, active_run **NONE**. Entry dirty — QA/docs предыдущих модулей/repair plans плюс уже созданная own run08 папка, см. [snapshot](snapshot.json). Tracked приложение не изменено. Runtime — текущий WORKTREE и существующие compiled .mo, не production и не стенд исходного Linux ПК. Source manifest: **2784 файла**, SHA256 **933b55c01caf9ab69bce9d81d23b69e87c262ffcf5d192917e8d9272b0f7ee83**. Startup guard run.py сверил source перед запуском, autoreloader выключен; финальная manifest/HEAD/PID проверка в [verification](verification.json). /qa/version только возвращает manifest, сам по себе не является независимой аттестацией. [Runtime identity](runtime-final.json), [isolation](isolation.json).

Stand новый: HTTP localhost8821, PID42060, PG localhost55439/module08/test_module08, новый контейнер kidsmap-module08-20261010-r1, unique volume. Python 3.12.15, Django 6.0.2, PostgreSQL17.11, Chromium153.0.8010.12/headless shell1243, own browser sessionmodule08-r1. Отдельные LocMem cache/email, media/private-media, session/CSRF cookies. DJANGO_TESTING=1, inherited credentials очищены, checkout .env не загружается в testing, server external sockets и browser non-local transport блокированы. Google/maps/OAuth/IndexNow/GA отключены. [Own QA launcher](run.py), [QA settings](qa_settings.py), [allowlisted read-only state endpoint](qa_urls.py).

Исходные фикстуры:9 actors/7places/32orgs/34revisions/event/specialist/private fake document; [fixtures](fixtures.json). Дополнительные NEW initial-only valid Event2+Org36 и synthetic specialization1 отдельно: [extra fixtures](extra-fixtures.json), [taxonomy](extra-taxonomy.json). Не исправляли существующие проверяемые переходы ORM: они выполнялись native UI/HTTP. Final read-only fictional state: [state-final](state-final.json). Setup races/неполные initial fixtures и собственные selector/async/confirm ошибки описаны в [commands](commands.md), не выданы за defects.

Нужные документы доступны, missing=[] в [documents](documents.json); прочитаны также canonical knowledge/rules/role definitions и применимые skills. Codebase Memory C-kidsmap использован первым для architecture/coverage: root совпадает, index ready; initial125509nodes/227637edges,74 partial parses/60 unindexed dirs, timestamp/generation свежести UNKNOWN. Во время QA architecture index вырос до135543nodes/237881edges. Граф — исследовательские hints; Django permissions, URL registration и critical source edges проверены текстом/файлами. Caches графа не сохранялись.

Фактические поверхности: Django Place/Organization/Event/Specialist changelists; /admin/volunteer/ и edit/proposal; moderation hub и content detail; superadmin legacy review; moderation SLA; staffaccessuser role UI. Hub объединяет Place/Organization/Program/Activity/OfferingGroup/affiliation, Event/Specialist идут через отдельные admin surfaces. [Source mapping](SOURCE-MAP.md).

| Роль initial fixture | Фактический доступ в RU/AZ/EN |
|---|---|
| anonymous, owner, outsider | admin302; direct protected mutations/state без разрешения не проходят |
| volunteer / volunteer_b | собственные authored owner=NULL объекты; чужой ID404, moderation403 |
| moderator preset | hub200 для affiliation scope, content detail404; legacy review403 |
| reviewer / reviewer_b: explicit change_place permission | content hub/detail200, legacy review403; private document404 |
| staff без business permissions | защищённые surfaces403 |
| admin superuser | нужные очереди/review200, fake private document200 |

Это scope/perms конкретных fictional actors, не универсальный вывод по названию роли. [195 ACL checks](acl.result.txt) включают negative GET/POST и сравнение allowlisted place/org/revision/photo/event/spec состояния и двух counts; они не проверяют абсолютно все DB таблицы/логи/session writes.

## 2. Сильные стороны

| Сценарий | Роль / язык / ширина | Свежий результат |
|---|---|---|
| Pending org→return reason→draft correction/reload→resubmit→approve→postpublished candidate→final reject | volunteer/reviewer RU390/1440 | PASS; live не заменяется draft/pending/rejected candidate |
| Два reviewers с одной version, один решает, другой stale | reviewer/reviewer_b RU1440 | PASS;409, allowlisted state без изменений |
| Две вкладки volunteer editor | volunteer RU390 | PASS; stale draft не перезаписывает первый, ввод остаётся |
| Native volunteer main photo upload/draft/reload/submit/legacy approval/public reload | volunteer/admin/anonymous RU390/1440 | PASS; настоящие normalized media и live readback |
| Owner main+gallery ready→draft→reload→pending→native hub approve→public reload | owner/admin RU1440; anonymous RU/AZ/EN390 | PASS data pipeline; review preview FAIL MOD-QA-02 |
| Processed action / invalid action / missing reason / stale / CSRF | selected roles RU/AZ/EN | PASS denied/no allowed side effects; actual409/403 |
| Частичная массовая публикация Place | admin RU1440 | PASS: ровно1 published,1 quality skipped; неполная карточка остаётся draft |
| Event2 rejected с собственной причиной→pending→published | admin RU1440 | PASS native UI; валидный organizer, photo; Event1 fixture invalid excluded |
| Specialist required error→выбор synthetic direction→rejected reason→pending→published→reload | admin RU1440 | PASS native Save confirmation и state; error summary FAIL MOD-QA-07 |
| Role revoke в staffaccessuser UI и старая вкладка | former volunteer_b RU390 | PASS native403; fresh GET403; содержание не изменилось |
| Native own draft delete cancel/accept/reload | volunteer RU390 | PASS; отмена не меняет state, подтверждение soft-deletes только own fixture6 |
| Place/Organization/Event/Specialist native search/empty result | admin RU/AZ/EN × all6 widths | По точным rows searches.result; никаких ORM substitutions |
| Filled/empty/error/conflict/long comparison/SLA и keyboard filter focus | admin/volunteer RU/AZ/EN × all6 widths | Rendered evidence; missing pagination/overflow/sidebar — отдельные FAIL |
| Native open/close filter panels | admin RU/AZ/EN × all6 widths | Place controls/focus PASS; Event/Specialist empty panels FAIL MOD-QA-08 |
| Loading/repeat guard/conflict/error/retry | admin RU/AZ/EN × all6 widths | PASS handler checks, **SIMULATED** delayed409/aborted AJAX; не реальная внешняя интеграция |

Основные [flows](flows.result.txt), [flows2](flows2.result.txt), [role/delete readback](flows3-resume.result.txt), [valid gallery](gallery-finish.result.txt), [Event](editor-finish.result.txt), [Specialist](specialist-valid-finish.result.txt). Новые org33–35 созданные UI в RU/AZ/EN390 завершены declined/draft: fresh final readback PASS3, original flows3 потерял observation array после screenshot timeout; поэтому полный массив промежуточных PAS не восстановлен догадками. PNG сохранены.

215/215 unchanged targeted Django tests PASS,0failures/0errors/0skips,147.499s, native exit0. [Exact argv](tests-command.json), [log](tests.log). Test suites: publication/admin_editors/volunteer_hub/completion_moderation/volunteer_admin/volunteer_dashboard/moderation_sla/place_readiness/admin_candidate_cover/specialist_privacy. Full suite NOT RUN.

## 3. Реальные проблемы

Каждый defect отдельно с role, endpoint, repro, expectation/fact, cause/hypothesis, source, evidence, impact и repair scope. [Finding index](FINDINGS.md).

| ID | Приоритет | Факт | Repair prompt |
|---|---|---|---|
| [MOD-QA-01](findings/MOD-QA-01.md) | P2 | В центре модерации нет перехода к следующим страницам | [Промпт](repair-prompts/MOD-QA-01.txt) |
| [MOD-QA-02](findings/MOD-QA-02.md) | P2 | Фото и галерея в централизованной модерации отображаются путями | [Промпт](repair-prompts/MOD-QA-02.txt) |
| [MOD-QA-03](findings/MOD-QA-03.md) | P2 | Панель очередей выходит за экран при ширине 1024 | [Промпт](repair-prompts/MOD-QA-03.txt) |
| [MOD-QA-04](findings/MOD-QA-04.md) | P2 | Escape не закрывает мобильную административную навигацию | [Промпт](repair-prompts/MOD-QA-04.txt) |
| [MOD-QA-05](findings/MOD-QA-05.md) | P2 | В подтверждении снятия с публикации фокус остаётся на BODY | [Промпт](repair-prompts/MOD-QA-05.txt) |
| [MOD-QA-06](findings/MOD-QA-06.md) | P2 | AZ/EN подтверждение снятия с публикации написано по-русски | [Промпт](repair-prompts/MOD-QA-06.txt) |
| [MOD-QA-07](findings/MOD-QA-07.md) | P2 | Сводка ошибки специалиста разбивает HTML на отдельные символы | [Промпт](repair-prompts/MOD-QA-07.txt) |
| [MOD-QA-08](findings/MOD-QA-08.md) | P2 | Панели фильтров мероприятий и специалистов открываются пустыми | [Промпт](repair-prompts/MOD-QA-08.txt) |

Классификация: все8 — baseline текущего неизменённого локального source; доказанного regression от этого QA нет. Production applicability UNKNOWN. External font blocks/setup/harness failures — environment/QA, не новые application findings. 2px volunteer edit overflow RU/AZ360 сохранён как manual_review/NOT RUN по видимому ущербу, отдельный defect не назначен. Source-only hardcoded toasts и specialist bulk readiness bypass требуют отдельного product/contract решения, не объявлены подтверждённой потерей данных.

## 4. Tech debt

Shared changelist renderer содержит place-specific whitelist и CSS среди surfaces других моделей. Media comparison строковый вместо typed rendering. Focus selector допускает SVG href. Specialist template смешивает AdminField и underlying BoundField error semantics. Content revisions используют version/content_version/dependencies, Event/Specialist другие admin contracts; нельзя применять один optimistic-lock pipeline по названию «модерация». Legacy review всё ещё wired и полезен для superadmin photo preview; compatibility не является разрешением удалить его.

## 5. Risks

В пределах выполненных native negative tests не подтверждены чужое сохранение/обход роли/private-doc leakage. Это ограниченная выборка endpoints и allowlisted state, не доказательство безопасности всех APIs. Отсутствующий preview повышает риск принять неподходящие фото; missing pagination скрывает часть backlog. Keyboard/navigation issues затрудняют административную работу. UI .mo/fallback environment может влиять на тексты; MOD-QA-06 отдельно подтверждён hardcoded source.

Фонты fonts.googleapis.com намеренно blocked. В main matrix diagnostics666 net::ERR_FAILED от fonts и18 ожидаемых400 invalid-filter console messages; local requestfailed0, других captured JS exceptions там нет. [Диагностика](matrix.result.txt), [SIMULATED failures](supplement.result.txt). Для дополнительных flows нет исчерпывающего единого network HAR; точные captured responses указаны в raw rows. Event flatpickr CDN также blocked; корректные сохранённые даты valid Event2 проверены родной form, внешний SDK не выдаётся за PASS.

## 6. Dead/legacy candidates

Удаление не предлагалось/не выполнялось. Legacy volunteer review действующий, его ACL отличается от hub; удаление без migration/role workflow review недопустимо. Недоступный object assignment API не объявлен dead code: workspace реально опирается на created_by/owner=NULL, роль можно отозвать. Graph orphan/dead analysis не использован для удаления.

## 7. Tests gaps

Authoritative [matrix CSV](matrix.csv)/[JSON](matrix.json), [summary](results-summary.json), [scope gaps](coverage-gaps.json), [excluded attempts](excluded-observations.json). Observations: **PASS=1791 / FAIL=165 / NOT RUN=4**, всего **1960**; дополнительно **11 scope NOT RUN**, то есть NOT RUN aggregate включая scope=15. Это assertion/control observations с повторами, не число независимых полноценных пользовательских путей и не число defects.

| Run | PASS | FAIL | NOT RUN |
|---|---|---|---|
| flows | 10 | 1 | 0 |
| flows2 | 11 | 0 | 0 |
| matrix | 1132 | 36 | 2 |
| acl | 195 | 0 | 0 |
| supplement | 132 | 51 | 0 |
| flows3-resume | 11 | 0 | 0 |
| gallery-finish | 5 | 1 | 0 |
| final-proof | 11 | 34 | 2 |
| editor-finish | 3 | 0 | 0 |
| specialist-finish | 6 | 6 | 0 |
| specialist-valid-finish | 4 | 0 | 0 |
| drawers | 126 | 36 | 0 |
| searches | 143 | 0 | 0 |
| search-retry | 2 | 0 | 0 |

Browser: все18 RU/AZ/EN×360/390/768/1024/1280/1440; headless Chromium, viewport height950. Native PNG **776**, SHA/dimensions в [manifest](screenshots-manifest.json); включая прозрачно сохранённые harness diagnostic screenshots.21 DERIVED contact sheets [manifest](contacts-manifest.json),18 исходных обзоров399 top viewport crops и3 filter обзора54 frames визуально просмотрены; критические PC/mobile defects дополнительно открыты крупными native кадрами. Contact sheets не заменяют исходные PNG и не доказывают пиксели всех scroll positions. System select popup pixels/screens reader/real touch device NOT RUN.

Loading/error quick actions задерживались/abortились route interception; native server stale409 отдельно проверен. No actual maps/OAuth/SMTP/integrations. Полный cross-product mutations×9roles×18cells NOT RUN; основные complex flows RU390/1440, публичные photos RU/AZ/EN390. Нет parallel batch stress, полного audit event retention/LogEntry UI history, real assignment feature и >page-size pagination данных Event/Specialist. Program/activity/group полный editor lifecycle — scope05, здесь только queues/hub/targeted tests. Event/Specialist VolunteerPlaceRevision candidate/live pipeline неприменим к фактически иной реализации; не помечен PASS по аналогии.

Own failures: malformed initial gallery/string вместо dictionary (правильный server отказ), wrong legacy role403, strict duplicate search/login selector, async photo processing/redirect ожидание старой кнопки, Save confirm auto-dismiss, no initial specialization lookup, hidden mobile nav вместо section-jump, fullpage screenshot timeout, search debounce/Enter retry. Исправлялись только QA scripts/NEW fictional fixtures.396 observation rows исключены/заменены; raw attempts/CLI exit1 сохранены. Неполные первичные Event fixtures не замаскированы под regression. [Commands и exits](commands.md).

## 8. Recommendations

Сначала отдельный согласованный scope MOD-QA-05/01/02, затем responsive/filter rendering MOD-QA-03/08 и sidebar/i18n MOD-QA-04/06. MOD-QA-07 передать владельцу модуля03 с этим fresh evidence. Не менять assertions/права/publication rules ради зелёного; каждому исправлению нужен собственный rendered regression и native save/reload.

В глобальный MASTER_AUDIT выводы этого модуля передать при module13; чужой MASTER сейчас не перезаписывался. Строка08 журнала обновлена, следующий module09. [Готовый текст следующему чату](next-chat.txt), [канонические13 prompts](../module-acceptance-prompts.md).

Сохранность: проверены2784 source files,7161 foreign files вне журнала, active_run,7 foreign HTTP listeners и9 foreign Docker containers; exact final hashes/drift/PIDs/IDs и только row08 diff в [verification](verification.json). Собственный stand08 оставлен для локальной повторной проверки. Production не подключался; foreign stand/data/credentials не использовались.

## 9. P0/P1/P2/P3

P0/P1: подтверждённых findings0. P2:8 OPEN (MOD-QA-01…08), severity обоснована в каждом файле. P3: подтверждённых отдельных findings0;2px manual_review не повышен до defect. Окончательный module verdict **FAIL** по UX/moderation accessibility и отображению, несмотря на215 passing targeted tests. Вывод относится к описанному локальному snapshot и реально выполненным cells.
