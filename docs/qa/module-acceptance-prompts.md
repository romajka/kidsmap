# KidsMap — промпты приёмки по модулям

Дата подготовки: 2026-10-09. Режим: AUDIT ONLY. Это задания для новых проверок, а не отчёт об их выполнении.

## Работа на другом ПК

1. Этот файл переносится обычным Git commit/push/pull. Push не переносит незакоммиченный WORKTREE, тестовые DB, media, браузерные сессии или работающий стенд.
2. После получения ветки проверь текущие HEAD/WORKTREE и active_run. Не переноси дату или SHA исторического отчёта в новую приёмку.
3. Открывай отдельный чат для одного модуля и копируй полный блок ниже. На одном checkout выполняй модули последовательно. Для параллельной работы нужны раздельные checkout/DB/cache/media и согласованные границы.
4. На другом ПК определи реальный путь репозитория и создай собственный изолированный стенд. При отсутствии инструмента/документа/внешней интеграции укажи ограничение явно.
5. Аудит не разрешает исправление приложения. Каждый finding получает отдельный repair prompt; реализация требует согласованного scope.
6. После каждого модуля заполни только его строку журнала: status, snapshot, report/evidence, ограничения, следующий шаг. Не отмечай PASS по историческим отчётам. Отчёт с FAIL тоже означает завершённый аудит, если обязательные сценарии выполнены; открытые дефекты перечисляются отдельно.
7. Секреты, пароли, токены, env values, реальные пользовательские данные, production dumps и graph caches в Git не добавлять.

## Журнал этой серии

Все NOT RUN ниже относятся к новой серии заданий. Они не отменяют прежние локальные проверки.

| № | Модуль | Состояние выполнения | HEAD / WORKTREE snapshot | Новый отчёт / evidence | Ограничения / следующий шаг |
|---|---|---|---|---|---|
| 01 | Постоянные места | DONE — scoped PASS (PLACE-QA-01–07 recheck + PLACE-QA-08 repair; full module01 NOT RUN) | C:\kidsmap; task33-progress; 8d188b316f800fbedf0b1e376905dfd4924cb1b6; dirty WORKTREE preserved; active_run NONE; recheck localhost:8841; repair localhost:8842 + new isolated fresh PO/MO | [Fresh recheck 2026-10-11](module01-recheck-2026-10-11-r1/REPORT.md), [verification](module01-recheck-2026-10-11-r1/verification.json), [matrix](module01-recheck-2026-10-11-r1/matrix.csv), [screenshots](module01-recheck-2026-10-11-r1/screenshots-manifest.json); [PLACE-QA-08 repair](place-qa08-fix-2026-10-11-r1/REPORT.md), [repair verification](place-qa08-fix-2026-10-11-r1/verification.json); [история r2](module01-2026-10-09-r2/REPORT.md), [r1](module01-2026-10-09-r1/REPORT.md) | 7 existing fixes verified in WORKTREE/fresh locale profile; 38 Django +34 Node +9 locale-helper PASS; browser252P/6F(one cause)/12NR;164 native PNG; PLACE-QA-08 alias CROSS-QA-03 closed in fresh isolated repair profile: 6 Django PASS, browser87P/0F, 24 native PNG; full module acceptance NOT RUN; [repair prompt](module01-recheck-2026-10-11-r1/PLACE-QA-08-repair.txt), [handoff](module01-recheck-2026-10-11-r1/next-chat.txt) |
| 02 | Организации, готовые места и сотрудники | DONE — FAIL (audit complete) | C:\kidsmap; task33-progress; 8d188b316f800fbedf0b1e376905dfd4924cb1b6; entry QA-only dirty; active_run NONE unchanged | [Отчёт](module02-2026-10-09-r1/REPORT.md), [evidence](module02-2026-10-09-r1/verification.json), [matrix](module02-2026-10-09-r1/matrix.csv), [screenshots](module02-2026-10-09-r1/screenshots-manifest.json) | 4 OPEN ORG-QA (3 P2, 1 P3); 216 tests OK; 308 PNG; external integrations/full suites NOT RUN; Далее 03; repair отдельным scope; [handoff](module02-2026-10-09-r1/next-chat.txt) |
| 03 | Специалисты и приватные документы | DONE — FAIL (fresh audit complete; limits NOT RUN) | C:\kidsmap; task33-progress; 8d188b316f800fbedf0b1e376905dfd4924cb1b6; entry QA-only dirty; active_run NONE unchanged; runtime WORKTREE + existing .mo | [Отчёт](module03-2026-10-10-r1/REPORT.md), [evidence](module03-2026-10-10-r1/verification.json), [matrix](module03-2026-10-10-r1/matrix.csv), [screenshots](module03-2026-10-10-r1/screenshots-manifest.json) | 3 OPEN SPEC-QA (2 P2, 1 P3); 106/107 Django PASS, 1 Windows ERROR; 455 PNG; locale/environment/integration/coverage limits documented; Далее 04; repair отдельным scope; [handoff](module03-2026-10-10-r1/next-chat.txt) |
| 04 | Мероприятия | DONE — FAIL (fresh audit complete; limits NOT RUN) | C:\kidsmap; task33-progress; 8d188b316f800fbedf0b1e376905dfd4924cb1b6; QA/docs dirty preserved; active_run NONE unchanged; runtime WORKTREE + existing .mo | [Отчёт](module04-2026-10-10-r1/REPORT.md), [verification](module04-2026-10-10-r1/verification.json), [matrix](module04-2026-10-10-r1/matrix.csv), [screenshots](module04-2026-10-10-r1/screenshots-manifest.json) | 3 OPEN P2 EVENT-QA; 118/129 Django PASS, 2 baseline FAIL, 9 environment preflight NOT RUN; 328 PNG; limits and SIMULATED integrations recorded; Далее 05; repairs отдельно; [handoff](module04-2026-10-10-r1/next-chat.txt) |
| 05 | Программы, занятия, группы, тарифы и расписание | DONE — FAIL (fresh audit complete; limits NOT RUN) | C:\kidsmap; task33-progress; 8d188b316f800fbedf0b1e376905dfd4924cb1b6; dirty QA/docs preserved; active_run NONE unchanged; runtime WORKTREE + existing .mo | [Отчёт](module05-2026-10-10-r1/REPORT.md), [verification](module05-2026-10-10-r1/verification.json), [matrix](module05-2026-10-10-r1/matrix.csv), [screenshots](module05-2026-10-10-r1/screenshots-manifest.json) | 8 OPEN OFFER-QA (6 P2, 2 P3; locale source/environment mixed);250/250 Django PASS;688 rendered PNG +4 crops/contact; limits/SIMULATED recorded; Далее06; repairs отдельно; [handoff](module05-2026-10-10-r1/next-chat.txt) |
| 06 | Публичный каталог, поиск, фильтры и карта | DONE — FAIL (fresh audit complete; limits NOT RUN) | C:\kidsmap; task33-progress; 8d188b316f800fbedf0b1e376905dfd4924cb1b6; dirty QA/docs; active_run NONE unchanged; runtime WORKTREE + existing .mo | [Отчёт](module06-2026-10-10-r1/REPORT.md), [verification](module06-2026-10-10-r1/verification.json), [matrix](module06-2026-10-10-r1/matrix.csv), [screenshots](module06-2026-10-10-r1/screenshots-manifest.json) | 4 OPEN PUBLIC-QA (3 app P2, 1 environment P3); Django93 methods:92 PASS, 1 method/2 subtest FAIL; JS6/6 PASS; 616 native PNG +13 DERIVED; SDK/conflicts/shared cache NOT RUN; foreign ledger drift recorded, no rollback; Далее07; [handoff](module06-2026-10-10-r1/next-chat.txt) |
| 07 | Аккаунты, команда, права и приватность | DONE — FAIL (fresh audit complete; limits NOT RUN) | C:\kidsmap; task33-progress; 8d188b316f800fbedf0b1e376905dfd4924cb1b6; dirty QA/docs preserved; active_run NONE; runtime WORKTREE + existing .mo | [Отчёт](module07-2026-10-10-r1/REPORT.md), [verification](module07-2026-10-10-r1/verification.json), [matrix](module07-2026-10-10-r1/matrix.csv), [screenshots](module07-2026-10-10-r1/screenshots-manifest.json) | 5 OPEN P2 ACCESS-QA;281/282 Django PASS,1 Windows preflight FAIL/body NOT RUN;2404 PASS/66 FAIL observations;695 native PNG;retention/clock SIMULATED and gaps recorded; Далее08; repairs отдельно; [handoff](module07-2026-10-10-r1/next-chat.txt) |
| 08 | Админка, модерация и волонтёрский кабинет | DONE — FAIL (fresh audit complete; limits NOT RUN) | C:\kidsmap; task33-progress; 8d188b316f800fbedf0b1e376905dfd4924cb1b6; dirty QA/docs preserved; active_run NONE; runtime WORKTREE + existing .mo | [Отчёт](module08-2026-10-10-r1/REPORT.md), [verification](module08-2026-10-10-r1/verification.json), [matrix](module08-2026-10-10-r1/matrix.csv), [screenshots](module08-2026-10-10-r1/screenshots-manifest.json) | 8 OPEN P2 MOD-QA;215/215 Django PASS;1791 PASS/165 FAIL observations;776 native PNG;SIMULATED transport/gaps recorded; Далее09; repairs отдельно; [handoff](module08-2026-10-10-r1/next-chat.txt) |
| 09 | Отзывы, избранное и уведомления | DONE — FAIL (fresh audit complete; limits NOT RUN) | C:\kidsmap; task33-progress; 8d188b316f800fbedf0b1e376905dfd4924cb1b6; dirty QA/docs preserved; active_run NONE; runtime WORKTREE + existing .mo | [Отчёт](module09-2026-10-10-r1/REPORT.md), [verification](module09-2026-10-10-r1/verification.json), [matrix](module09-2026-10-10-r1/matrix.csv), [screenshots](module09-2026-10-10-r1/screenshots-manifest.json) | 9 OPEN SOCIAL-QA (8 P2,1 P3);67/77 Django PASS,10 socket-runner environment ERROR/body NOT RUN;3314 PASS/207 FAIL observations;1515 native PNG;SIMULATED/gaps recorded; Далее10; repairs отдельно; [handoff](module09-2026-10-10-r1/next-chat.txt) |
| 10 | Настройки, разделы и общие страницы | DONE — FAIL (fresh audit complete; limits NOT RUN) | C:\kidsmap; task33-progress; 8d188b316f800fbedf0b1e376905dfd4924cb1b6; dirty QA/docs preserved; active_run NONE; entry→current WORKTREE drift recorded/preserved; current runtime matched + existing .mo | [Отчёт](module10-2026-10-10-r1/REPORT.md), [verification](module10-2026-10-10-r1/verification.json), [matrix](module10-2026-10-10-r1/matrix.csv), [screenshots](module10-2026-10-10-r1/screenshots-manifest.json) | 15 OPEN SITE-QA (1 P1,12 P2,2 P3);41/46 Django PASS,4 baseline/locale FAIL,1 baseline ERROR;3611 PASS/319 FAIL/347 NOT RUN observations;1605 native PNG;SIMULATED/gaps recorded; Далее11; repairs отдельно; [handoff](module10-2026-10-10-r1/next-chat.txt) |
| 11 | SEO, языковые URL и redirects | DONE — FAIL (fresh audit complete; limits NOT RUN) | C:\kidsmap; task33-progress; 8d188b316f800fbedf0b1e376905dfd4924cb1b6; dirty foreign WORKTREE preserved; active_run NONE unchanged; runtime WORKTREE + existing .mo matched | [Отчёт](module11-2026-10-11-r1/REPORT.md), [verification](module11-2026-10-11-r1/verification.json), [matrix](module11-2026-10-11-r1/matrix.csv), [screenshots](module11-2026-10-11-r1/screenshots-manifest.json) | 7 OPEN SEO-QA (6 P2,1 P3); 106/110 main Django PASS,4 flag-compatibility failures then 4/4 legacy PASS;33 extra PASS,9 environment/business NOT RUN;2753 PASS/153 FAIL/175 NOT RUN observations;724 native PNG;SIMULATED/gaps recorded; Далее 12; repairs отдельно; [handoff](module11-2026-10-11-r1/next-chat.txt) |
| 12 | Просмотры, счётчики и аналитика | DONE — FAIL | 2026-10-11 / module12-2026-10-11-r1 | [REPORT](module12-2026-10-11-r1/REPORT.md), [findings + repair prompts](module12-2026-10-11-r1/FINDINGS.md) | 8OPEN ANALYTICS-QA (6P2/2P3); existing60/60PASS, own4PASS/5FAIL; 542PASS/79FAIL/25NOTRUN observations; 200nativePNG; realGA/production NOTRUN; source/foreign preserved; Далее13; [handoff](module12-2026-10-11-r1/next-chat.txt) |
| 13 | Финальная межмодульная приёмка и сводка | DONE — FAIL (fresh audit complete; mandatory limits NOT RUN) | C:\kidsmap; task33-progress; 8d188b316f800fbedf0b1e376905dfd4924cb1b6; dirty WORKTREE e13c36f2af3aca03513ff860a1dee7c02a8cb2ab8214c89bcffd7dd5fe5914b1; active_run NONE unchanged; runtime source matched | [Отчёт](module13-2026-10-11-r1/REPORT.md), [MASTER](module13-2026-10-11-r1/MASTER_AUDIT.md), [evidence](module13-2026-10-11-r1/verification.json), [matrix](module13-2026-10-11-r1/matrix.csv), [PNG manifest](module13-2026-10-11-r1/screenshots-manifest.json), [repair prompts](module13-2026-10-11-r1/FINDINGS.md) | 10 fresh IDs /9 causes (7 old,3 CROSS); browser2576 PASS/32 FAIL/73 NOT RUN; Django2036 PASS/11 baseline FAIL/43 NOT RUN; JS20 scripts PASS;846 retained PNG incl12 derived; revoke UI/legacy guards/real integrations/devices/actual GitHub NOT RUN; all13 audit rows DONE; next scoped repair plan, no automatic fixes; [handoff](module13-2026-10-11-r1/next-chat.txt) |

## Текст для нового чата

```text
Продолжаем KidsMap на этом ПК. Прочитай docs/qa/module-acceptance-prompts.md целиком и AGENTS.md. Следуй каноническим инструкциям .agents.

Определи текущий checkout, HEAD/WORKTREE, active_run и наличие нужных документов. Посмотри журнал новой серии в файле; выбери первый незавершённый модуль среди 01–12. Если серия ещё не начата, начни с 01 «Постоянные места». Модуль 13 выполняй после остальных.

Выполни выбранный промпт до отчёта, только один модуль за этот запуск. Приложение не исправляй. Создай на этом ПК изолированный локальный стенд; не считай старые адреса, тестовые DB и исторические PASS свежими доказательствами.

После проверки сохрани новый отчёт/evidence, обнови только строку этого модуля в журнале файла и дай готовый текст для следующего чата. Сохрани чужие изменения. Без commit/push/deploy/production.
```

## 01. Постоянные места

```text
Работай в корне репозитория KidsMap. На исходном ПК это /home/ramin/kidsmap; на другом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Проведи функциональную и визуальную приёмку постоянных мест: кабинет владельца, административный редактор и публичная карточка.

Проверь:
1. Создание самостоятельного места и филиала, разные категории и подкатегории.
2. Названия AZ/RU/EN, пустые переводы и языковой fallback. Раздели отображение другого языка и реально сохранённый перевод.
3. Описание, возраст, контакты, адрес, регион/район, карту и ручные координаты. Отсутствие точки, 0/0, неверную/неполную пару, отказ геолокации и отсутствие SDK. Перепроверь docs/qa/admin-place-map-fix-2026-10-09.md, если файл доступен.
4. Бесплатный/платный вход, общий билет, цену по мероприятию. Повторное переключение режимов и повторное редактирование не должны вызывать зависание.
5. Часы работы места отдельно от расписания занятий.
6. Главное фото, галерею, порядок, замену/удаление и ошибку файла. Сверь данные после reload и на публичной карточке.
7. Навигацию по длинной форме, готовность по серверным требованиям, сводку/переход к ошибке и честное состояние сохранения.

Выполни настоящий путь через UI: создание → частичное заполнение → черновик → reload → выход/вход → продолжение → ошибка → исправление → отправка → отказ с причиной → повторная отправка → одобрение → публичная карточка → изменение опубликованного. По коду установи, какие изменения ждут модерации; сверяй candidate и live.

Негативно проверь чужой ID, недостаточные права, повторное нажатие, две вкладки, сетевую ошибку и сохранность ввода. Проверяемые переходы не выполняй прямым ORM-сохранением. Префикс дефектов PLACE-QA-xx.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.
```

## 02. Организации, готовые места и сотрудники

```text
Работай в корне репозитория KidsMap. На исходном ПК это /home/ramin/kidsmap; на другом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Проведи полную функциональную и визуальную приёмку управления организациями. Дополнительно прочитай docs/qa/organization-deep-audit-2026-10-08.md, если доступен, и перепроверь исторические ORG findings.

Изучи canonical request_join, confirm_join, detach, affiliation_current и версии владения. Проверяемые связи выполняй через реальные UI/API, не присваиванием organization_id.

Позитивные сценарии:
1. Создать организацию без филиалов, сохранить, reload, отредактировать. Проверить доступные процессы модерации/публичного отображения по текущему контракту.
2. Найти готовые места по названию/адресу; увидеть текущую сеть, доступность и состояние запроса.
3. Подключить 10 существующих мест без пересоздания. Сверить ID, владельца, фото, занятия, группы, цены и расписание до/после.
4. Пройти необходимые согласия сторон, отмену/отказ/повтор запроса.
5. Создать новый филиал отдельно от подключения готовой карточки.
6. Массовая операция: выбор → организация → preview/conflicts → подтверждение → результат по каждой карточке.
7. Отвязать место и выполнить разрешённый перенос в другую сеть с объяснением последствий.
8. Приглашение сотрудника, понятность ролей, принятие/отказ/отзыв и удаление доступа.

Негативно: другая сеть; чужой приватный draft по угаданному ID; недостаточные права; старое согласие после смены владельца; изменение между preview и confirm; mixed batch с частичным отказом; двойное подтверждение; lost response/retry; истёкшее приглашение. Проверь legacy endpoints и API, не только новый интерфейс.

Запрос не должен выдавать права или раскрывать приватные метаданные. Отвязка должна учитывать общие программы и доступ сотрудников по действующему контракту. Префикс ORG-QA-xx.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.
```

## 03. Специалисты и приватные документы

```text
Работай в корне репозитория KidsMap. На исходном ПК это /home/ramin/kidsmap; на другом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Проведи функциональную и визуальную приёмку специалистов: предложение профиля, личный кабинет, административный редактор и публичная карточка.

Проверь:
1. Имя, фото, направления, возраст детей, языки, формат, описание, образование, стоимость.
2. Пустой стаж и 0 лет, отрицательные/чрезмерные значения.
3. Поиск направлений на телефоне, отсутствие дублей, удаление выбранного.
4. Несколько мест приёма: адрес/филиал, отдельная цена и телефон каждого; онлайн/смешанный формат.
5. Разделение автора предложения, специалиста, сотрудничества с сетью и места приёма.
6. Приглашение сетью, принятие/отказ/отзыв/повтор и изменение полномочий.
7. Подтверждение личности и claim существующего профиля по предусмотренному процессу.
8. Приватность документов личности; публикацию сертификатов с необходимыми согласиями.

Пройди реальный UI: частичное предложение → черновик с первого и остальных доступных этапов → reload → продолжение → ошибки → отправка → модерация/отказ → исправление → публикация → редактирование опубликованного. Сверь места приёма, файлы и публичную версию.

Проверь две вкладки, повтор отправки, ошибку файла/сети, чужой draft/profile/document ID. Матрица доступа: гость, автор предложения, специалист, сотрудник сети, владелец сети, модератор, администратор. Прямое скачивание документа, доступ после отзыва роли, безопасное публичное media. Автор предложения не получает личные права. Префикс SPEC-QA-xx.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.
```

## 04. Мероприятия

```text
Работай в корне репозитория KidsMap. На исходном ПК это /home/ramin/kidsmap; на другом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Проведи функциональную и визуальную приёмку мероприятий: кабинет владельца, административный редактор, управление событием и публичная карточка.

Изучи существующие 3 этапа; не придумывай второй процесс.
1. Организация/специалист как организатор; ровно один организатор; отсутствие доступного организатора и отзыв права во время ввода.
2. Площадка отдельно от организатора: собственный адрес, разрешённая площадка KidsMap, недоступная/скрытая площадка.
3. Очно/онлайн, переключение туда/обратно, обязательность полей и сохранность скрытых значений по контракту.
4. Asia/Baku: дата, начало/окончание, полночь, одинаковое время, окончание раньше начала, истёкшее событие.
5. Возраст, цена, контакты, описание и переводы.
6. Фото/порядок галереи/ошибки файла/предпросмотр.
7. Черновик с каждого этапа, reload, повторное открытие.
8. Отправка, отказ/исправление, одобрение и изменение опубликованного.
9. Отмена/перенос: причина, новая дата, публичный статус, список/поиск и старая ссылка.

Негативно: чужие права/ID, двойная отправка, две вкладки, изменение организатора/площадки другим редактором, сбой сети/карты, ошибки публикации. Административные подписи и состояния новая/draft/pending/published/rejected должны соответствовать серверу.

Выбор формата проверь клавиатурой и по доступному имени/состоянию. Обещания о проверенных профилях, записи участников и рассылке сопоставь с реально реализованным процессом. Сохранение/публикацию докажи round-trip, не одним preview. Префикс EVENT-QA-xx.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.
```

## 05. Программы, занятия, группы, тарифы и расписание

```text
Работай в корне репозитория KidsMap. На исходном ПК это /home/ramin/kidsmap; на другом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Проведи отдельную функциональную и визуальную приёмку программ, занятий, групп, тарифов и расписания.

Установи действующий контракт Program, Activity, OfferingGroup, PricingPlan и расписаний. Не смешивай сеть, место, занятие, группу и тариф.

Проверь:
1. Общую программу организации и самостоятельное занятие места; создание/редактирование/архив и поддержанные состояния публикации.
2. Несколько занятий/групп одного места: названия, классификацию, возраст, формат и условия.
3. Подтверждение условий группы и изменение подтверждённых данных.
4. Бесплатно, общий билет, разовое посещение, абонемент и другие реально поддержанные тарифы; цена 0/пусто, валюта, единица оплаты, несколько тарифов.
5. Принадлежность тарифа группе; цена одной группы не должна смешиваться с возрастом другой.
6. Все поддержанные режимы часов работы места отдельно от расписания занятий. Несколько интервалов, выходные, пересечения, неверные интервалы, смену режима.
7. Структурированные данные и legacy fallback: редактирование не стирает старые цены/расписание без предусмотренного действия.
8. Отвязку филиала: общие программы, локальные группы, доступ сотрудников.
9. Public card/catalog/search/filter: цена/возраст/расписание относятся к одному подходящему предложению.

Сохранение/reload, ошибки, повтор, две вкладки, чужие ID, атомарность неудачной операции. Сверь связанные записи до/после. Если импорт/экспорт существует, проверь round-trip на своих локальных фикстурах. Отдельно мобильное добавление/удаление строк и ошибки внутри скрытых блоков. Префикс OFFER-QA-xx.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.
```

## 06. Публичный каталог, поиск, фильтры и карта

```text
Работай в корне репозитория KidsMap. На исходном ПК это /home/ramin/kidsmap; на другом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Проведи функциональную и визуальную приёмку главной, списков мест/организаций/специалистов/мероприятий, публичных карточек, поиска и карты.

Контролируемый набор: published/draft/pending/rejected/inactive/archived; разные районы, категории, возрасты, цены и группы.

Проверь:
1. Главную, меню, навигацию, карточки и переходы между сущностями.
2. Поиск по названию/адресу/реально поддержанным полям; AZ/RU/EN, частичный запрос, пустой результат. Опечатки проверяй как обязательную функцию только при подтверждённой поддержке.
3. Фильтры отдельно/совместно, сброс, сортировку, pagination, URL params, Back/Forward, reload, прямую ссылку.
4. Согласованность списка, количества и карты.
5. Совпадение возраста/цены/направления с одной подходящей группой.
6. Группировку площадок, одинаковые координаты разных мест, карточки без точки, popup и правильную карточку.
7. Отсутствие приватных/неодобренных данных в HTML/API/search suggestions/map.
8. Актуальность после публикации, изменения, отмены события и скрытия раздела; действующую инвалидацию локального cache.
9. Контакты, раскрытие телефона, внешние ссылки, фото/галерею и пустые состояния.

Отказ карты/сети проверяй локально. Раздели adapter simulation и реально проверенный SDK. Не используй production-карточки или внешние production-ключи. Проверь реальные клики и геометрию, а не только screenshot. Префикс PUBLIC-QA-xx.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.
```

## 07. Аккаунты, команда, права и приватность

```text
Работай в корне репозитория KidsMap. На исходном ПК это /home/ramin/kidsmap; на другом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Проведи функциональную, визуальную и негативную приёмку аккаунтов, команд и прав доступа.

Проверь:
1. Регистрацию, email confirmation, login/logout, восстановление пароля, профиль по реализованным процессам.
2. Неверные данные, email normalization, дубли, истёкшие/повторные токены, повтор запросов. Email перехватывай локально.
3. next/redirect, CSRF, создание/завершение сессии.
4. Google OAuth: локальные ошибки/adapters отдельно; внешнюю авторизацию без разрешённых тестовых credentials отметь NOT RUN.
5. Команду места/организации: приглашение, принятие/отказ/отзыв, смену роли, удаление сотрудника и потерю доступа в открытой вкладке.
6. Удаление аккаунта: связанные владение, связи, приглашения и приватные данные, только на своих фикстурах.
7. Прямые URL/API/download, подмену ID и доступ после изменения роли/владельца.
8. Автор предложения, специалист, владелец места/сети, сотрудник, волонтёр, модератор, администратор: точные границы.
9. Приватные документы в HTML/API/media/download/cache; сертификаты по предусмотренным согласиям.

Матрица роль × действие × сущность. Докажи отказ реальным HTTP и отсутствием побочных изменений: скрытая кнопка не является ACL. Негативные запросы только localhost/synthetic objects. Не сохраняй пароли, токены или env values в отчёте.

Подтверждённую утечку сообщи сразу, но автоматически не исправляй. Префикс ACCESS-QA-xx.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.
```

## 08. Админка, модерация и волонтёрский кабинет

```text
Работай в корне репозитория KidsMap. На исходном ПК это /home/ramin/kidsmap; на другом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Проведи функциональную и визуальную приёмку общих административных и модерационных процессов.

Установи реально существующие admin/volunteer поверхности и права.

Проверь:
1. Очереди мест/организаций/мероприятий/специалистов: поиск, фильтры, pagination, счётчики, переходы.
2. Одобрение, отказ с причиной, повторную отправку, отзыв заявки, действие над обработанной заявкой.
3. Candidate/live до решения/после одобрения/после отказа, включая фото и связанные данные.
4. Readiness: new/draft/pending/published/rejected по серверным требованиям.
5. Два модератора/две вкладки, stale version, повтор, частичный отказ batch.
6. Волонтёра: назначенные объекты, ограничения полей, отправку на проверку, отзыв назначения.
7. Прямые admin URL/API и действие без роли.
8. Журнал действий и причины решений без доступа к документам лишним ролям.
9. Mass actions: preview/confirmation/results и сохранность данных. Удаление только если предусмотрено и только своих фикстур.

Не дублируй полный обход каждого редактора: scope — очереди, решения, версии, массовые действия, admin navigation. Смежный finding передавай владельцу модуля со ссылкой на evidence.

Отдельно таблицы/sidebar/открытые фильтры/модалки/ошибки на телефоне и клавиатуру. Префикс MOD-QA-xx.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.
```

## 09. Отзывы, избранное и уведомления

```text
Работай в корне репозитория KidsMap. На исходном ПК это /home/ramin/kidsmap; на другом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Проведи функциональную и визуальную приёмку отзывов, избранного и внутренних уведомлений.

Проверь реально поддержанные процессы:
1. Отзывы о сайте и типах карточек: создание, оценку, required fields, редактирование, модерацию, отказ, public display.
2. Ответ/решение владельца: только разрешённые объекты и действия.
3. Голоса/полезность, повтор нажатия, корректность счётчиков.
4. Рейтинг/количество после одобрения, скрытия и изменения.
5. Длинный текст, спецсимволы, безопасное HTML display, pagination, empty state.
6. Favorite add/remove, double click, reload, login/logout, сохранность списка.
7. Favorite скрытой/архивной/недоступной карточки без утечки приватных данных.
8. Read/unread уведомления, счётчик, переход к объекту, принятие приглашения.
9. Повторное/stale уведомление, удалённый объект, отозванное приглашение, чужой notification ID.

Гость/автор/владелец/сотрудник/модератор/admin по действующим правилам. Сверь сохранённые записи и счётчики; анимация UI не доказывает сохранение. Негативные HTTP/API только локально.

Отдельно accessible rating controls, меню уведомлений и формы на телефоне. Отсутствующую функцию не называй дефектом без подтверждённого требования. Префикс SOCIAL-QA-xx.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.
```

## 10. Настройки, разделы и общие страницы

```text
Работай в корне репозитория KidsMap. На исходном ПК это /home/ramin/kidsmap; на другом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Проведи функциональную и визуальную приёмку настроек сайта, переключателей разделов и общих страниц.

Разрешено менять настройки только собственной изолированной тестовой DB.

Проверь:
1. Реальные branding/contacts/footer/hero PC/mobile/empty states/public text settings.
2. Главную, о проекте, FAQ, контакты, правила/privacy/terms и страницу бизнеса, если существует.
3. Save через админку, reload, public display, действующую инвалидацию cache.
4. Поочерёдное OFF/ON организаций/специалистов/мероприятий и других существующих flags.
5. Влияние flag на меню/home/catalog/search/map/direct URL/API/account по фактическому контракту.
6. Сохранность данных и admin editing при скрытом публичном разделе.
7. Language switch: текущую страницу/params, active language, fallback, ошибки и общие переводы.
8. Header/footer/mobile menu/breadcrumbs/shared buttons/forms/toast/modal/404 и поддержанные error pages.
9. Неверные ссылки/контакты, длинные тексты, missing images, save failure.

Раздели скрытие раздела, unpublish карточки, архив и удаление. Проверяй публичный результат, не только flag DB.

Дополнительно контраст/читаемость/200% zoom, открытые меню/модалки и fixed elements. В отчёте перечисли собственные изменения тестовых настроек. Префикс SITE-QA-xx.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.
```

## 11. SEO, языковые URL и redirects

```text
Работай в корне репозитория KidsMap. На исходном ПК это /home/ramin/kidsmap; на другом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Проведи локальную функциональную и визуальную приёмку URL, redirects и SEO.

Прочитай актуальную SEO source-map. Не отправляй IndexNow/Search Console запросы. SEO-команды сначала проверь на побочные записи.

Проверь:
1. URL мест/организаций/специалистов/мероприятий/занятий/реальных SEO landing pages.
2. Старый URL, неверный slug, rename и несколько rename: конечную сущность, HTTP status, число redirects, отсутствие loop, допустимые params.
3. AZ/RU/EN/default-language redirects, canonical/hreflang/language switch.
4. title/description/headings/Open Graph/images и preview без обращения к внешним ботам.
5. robots/sitemap/structured data по фактической public visibility.
6. Draft/pending/rejected/inactive/archived и disabled sections: отсутствие приватных данных в sitemap/HTML/JSON-LD/metadata.
7. Pagination/filter/empty/direct URL и действующий indexability contract.
8. Ссылки между сетью/филиалом/занятием/специалистом/событием после изменения/отвязки.
9. Escaping пользовательского текста в metadata/JSON-LD.

Не предполага́й наличие новостей/статей: найди реальные routes/models. Если модуль есть, включи его rename/redirect/SEO; иначе явно укажи отсутствие в текущем коде.

HTTP/head/schema проверь отдельно от visual browser: заголовки/breadcrumbs/links/страница после redirect. Локальную корректность не называй подтверждённой индексацией поисковиком. Префикс SEO-QA-xx.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.
```

## 12. Просмотры, счётчики и аналитика

```text
Работай в корне репозитория KidsMap. На исходном ПК это /home/ramin/kidsmap; на другом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Проведи функциональную и визуальную приёмку просмотров и аналитики.

Прочитай analytics source-map. Внешнюю отправку событий и реальные Google Analytics запросы отключи.

Установи определение view/unique visitor/event и ключ агрегирования: object/URL/slug/session/actor или фактический другой ключ. Не выдумывай методику.

Проверь:
1. Карточку гостем/login user/owner/staff: какие просмотры учитываются и исключаются.
2. Reload/Back/Forward/two tabs/repeated event request и текущую дедупликацию.
3. Rename карточки: заход по старой redirect-ссылке и новой. Докажи delta и выясни, суммируются ли просмотры у одной сущности.
4. Несколько rename, языковые URL, query params, устройства.
5. Phone/contact clicks/transitions и реализованные funnel events.
6. Invalid payload, чужой/private object ID, repeat, disabled analytics, локальный backend failure.
7. Owner/admin graphs: dates/periods/Asia/Baku/day-month boundaries/empty/totals.
8. DB aggregates/API/graphs consistency; отсутствие доступа к чужим данным.
9. Cancel/hide/archive и сохранность истории по контракту.

Фиксируй before/after каждого контролируемого действия. Adapter = SIMULATED, внешняя интеграция = NOT RUN, если не выполнена реально.

Отдельно period filters/graphs/tables/empty-error states. В findings укажи ожидаемый/фактический delta. Префикс ANALYTICS-QA-xx.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.
```

## 13. Финальная межмодульная приёмка и сводка

```text
Работай в корне репозитория KidsMap. На исходном ПК это /home/ramin/kidsmap; на другом ПК сначала определи фактический путь checkout. Прочитай AGENTS.md, канонические инструкции .agents и docs/qa/content-entry-audit-2026-10-06.md. Исторические отчёты используй только как чек-лист для свежей проверки.

Зафиксируй HEAD, branch, dirty WORKTREE, active_run и фактическую версию работающего стенда. Подтверди соответствие запущенных исходников WORKTREE. Сохрани чужие изменения, чужой active_run и чужие стенды. Недостающие документы явно перечисли; не подменяй их догадками.

Режим AUDIT ONLY: приложение, правила, миграции и существующие assertions не исправляй. Разрешены собственные QA-скрипты, изолированные фикстуры и новый отчёт. Только DJANGO_TESTING=1, отдельные DB/cache/media/private-media/email, вымышленные данные; без production credentials, внешних интеграций, commit/push/deploy. На другом ПК создай новый изолированный стенд; локальные адреса, PID, volumes и сессии исходного ПК не считаются доступными.

Запускай после отдельных модульных аудитов. Проведи финальную межмодульную приёмку и сведи новые результаты.

Прочитай модульные отчёты текущей серии. Сопоставь routes/models/admin surfaces с coverage; найди непроверенные области. Отчёты другого snapshot не считаются автоматически свежими: изменившиеся критичные сценарии перепроверь.

Пройди один реальный путь:
1. Создать организацию без филиалов.
2. Создать/опубликовать места и подключить готовые через canonical request/confirm.
3. Добавить программу/занятия/группы/тарифы/расписания.
4. Предложить специалиста, пройти подтверждения, сотрудничество с сетью и несколько мест приёма.
5. Очное событие на площадке филиала и online event с доступным организатором.
6. Draft/reload/submit/reject/correct/approve/public card.
7. Edit published/two-tab conflict/live preservation.
8. Detach branch/revoke employee/change cooperation/reschedule-cancel event: связанные программы/ACL/public display.
9. Public sections OFF/ON: menu/direct URLs/search/map/data preservation.
10. Фото/галерею/private docs/reviews/favorites/redirects/view counters в местах пересечения модулей.

Позитивные/негативные пути, повторы, partial failure. Полные применимые backend/JS-наборы запускай только подтверждённым изолированным launcher. Ничего не ослабляй/отключай ради green. Недоступный набор = NOT RUN с причиной.

Сведи дубли по первопричине, сохрани исходные IDs/evidence. Итог дополнительно:
— module/scenario/role/snapshot/PASS/FAIL/NOT RUN/evidence;
— открытые P0–P3, coverage gaps, внешние/device/browser ограничения;
— counts/exit codes, screenshots, порядок исправления с зависимостями;
— отдельные repair prompts.
Новый префикс CROSS-QA-xx. Общий PASS проекта не заявляй при невыполненных обязательных сценариях. Локальная приёмка не доказывает production-состояние.

Реальный браузер: RU/AZ/EN × 360/390/768/1024/1280/1440. Проверь применимые пустые, заполненные, loading/error/conflict состояния, длинные тексты, открытые селекты/модалки, Tab/Shift+Tab/Enter/Space/Escape, видимый фокус, перекрытия/обрезку/overflow и console/network. Сохрани свежие скриншоты PC/mobile, включая ошибки. Source inspection, jsdom и HTTP 200 не заменяют rendered browser и сохранение/reload.

Сохрани новый отчёт и evidence в docs/qa с уникальным module/date/run именем, без secrets и приватных данных. Верни PASS/FAIL/NOT RUN по сценарию/роли/языку/ширине, snapshot, точные команды, counts/exit codes и ссылки на доказательства. Отдели regression, pre-existing baseline failure, environment failure и SIMULATED integrations. Недоступные проверки и ограничения явно оставь NOT RUN; по возможности продолжи независимые проверки.

Каждый подтверждённый дефект оформи отдельно: ID указанного префикса, роль, URL/endpoint, шаги, ожидание, факт, доказательство, первопричина или неподтверждённая гипотеза, P0–P3 с обоснованием, область исправления и зависимости. Дай самостоятельный копируемый промпт на исправление каждого дефекта. Не исправляй автоматически и не выдумывай findings. Вывод «всё работает» допустим только в пределах реально выполненных сценариев.
```
