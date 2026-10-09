> **Последний аудит Task33: 2026-10-04.** Итоговый сквозной аудит 2026-10-04 завершён: рассмотрены все 28 этапов и 306 требований. Основная система реализована, окончательная полнота задумки НЕ подтверждена: taxonomy/search gap, красная регрессия, UI-дефекты и внешние release gates. Fresh host 1817: 109F/11E, Task33 579/580; exact image 1817: 108F/12E; browser FAIL: 816 contexts, 1724/1724 checks. Native recovery 98 tables / 25 public + 2 private files PASS. Application fixes/commit/push/production NOT_RUN. [Итоговый отчёт](../task33/final-audit/REPORT.md) · [HTML / screenshots](../task33/final-audit/report.html).

---

# KidsMap — аудит проекта 2026-09-08

> Обновление после отдельного разрешения пользователя: **SEC-01, SEC-02, BE-01, OPS-01, DB-01 исправлены в локальном WORKTREE** и проверены регрессионными тестами. [Изменения, red/green результаты и ограничения](2026-09-08-project/P1_FIXES.md). Production не обновлялся. Ниже сохранён исходный аудит до исправлений.

Координатор `/root`, kidsmap-orchestrator. Авторизация: «подключи комадку пускай првоерят мой проект». LOCAL HEAD `d75b34f4db5d4ba484cf8392ff3ae0c9939031e2`; предшествующие изменения команды в WORKTREE сохранены. PRODUCTION revision/data/config UNKNOWN, подключений не было. Аудит разрешает отчёты и изолированные проверки, не исправления приложения.

## 1. Состояние проекта

Найдены конкретные риски безопасности и потери данных. Рекомендация: сначала согласовать исправления P1 и регрессионные проверки. Текущая авария, взлом и число затронутых пользователей не установлены.

Задействованы 11 канонических ролей: часть последовательно теми же работниками, release/analytics — координатором. Не более трёх специалистов одновременно. Это не 11 независимых параллельных запусков. Распределение: [RUN](2026-09-08-project/RUN.md). [Предыдущий итог создания команды](2026-09-08-project/TEAM_CREATION_MASTER.md) сохранён дословно; его относительные ссылки рассчитаны на прежнее расположение в docs/agent-audits.

## 2. Сильные стороны

Есть отдельные сервисы тарифов, расписания, публичной видимости и volunteer-доступа, ограничения моделей и содержательные регрессионные тесты. Выбранные pricing/readiness/legacy/JSON-roundtrip тесты прошли на изолированной SQLite. Django system check и проверка отсутствующих миграций прошли. Это не проверка PostgreSQL, production или реального OAuth.

## 3. Главные проблемы

| Приоритет / ID | Проблема и триггер | Доказательство |
|---|---|---|
| P1 SEC-01 | Повторная проверка уже подтверждённого email возвращает пользователя до проверки challenge; endpoint выполняет вход | Source-цепочка подтверждена; полное HTTP-воспроизведение не запускалось. [Security](2026-09-08-project/security.md) |
| P1 SEC-02 | JSON-LD с пользовательскими строками не защищает HTML script-границу и вставляется через safe | Source + ограниченная проверка структуры сериализации; выполнение в браузере не проверялось. Публичность зависит от модерации. [Security](2026-09-08-project/security.md) |
| P1 BE-01 | Обычное сохранение опубликованной legacy-карточки стирает scalar-цену при пустых relational-тарифах | Синтетическая карточка: **80–120 → None/None**, форма валидна, статус остаётся published. [Backend](2026-09-08-project/backend.md), [QA](2026-09-08-project/qa.md) |
| P1 OPS-01 | Сбой pg_dump скрывается успешным gzip; backup сообщает успех и удаляет старые копии | Копия исходного скрипта + заглушка Docker + временные фикстуры: dump exit23, script exit0, старая синтетическая копия удалена. Реальный backup не затронут. [Devops](2026-09-08-project/devops.md) |
| P1 DB-01 | migrate_pricing_plans --apply реконструирует современные тарифы из неполных legacy-проекций и удаляет отсутствующие строки | Source подтверждает потерю addon/метаданных при указанной структуре; отдельная runtime-фикстура не запускалась. [Database](2026-09-08-project/database.md) |

Другие существенные результаты:

- **BE-03 P2:** некорректный JSON расписания принимается как семь закрытых дней. Изолированное сохранение owner draft сократило число открытых дней с шести до нуля.
- **QA-01 P2:** стандартное discovery пропускает **138 существующих тестов в 11 модулях**. Выбранные запуски дали **538 выполнений тестов, 13 записей падений в 12 методах**, без errors. Это не 538 уникальных тестов. Часть падений — прежние ожидания телефонных ссылок/текстов; они не доказывают поломку продукта.
- **AN-01 P2:** выбор 90 дней передаёт в GA ключ year, соответствующий 365 дням.
- **BE-02/BE-04:** расходятся owner/admin требования публикации; JSON export не сохраняет полное расписание для обратного импорта.
- **DB-02/DB-03:** две price migration-команды по-разному трактуют старые поля; проверка перед apply использует ранее загруженное состояние. PostgreSQL interleaving не проверен.
- **SEC-03/SEC-04:** условные риски прямого доступа к private media и suggestions для custom staff без прав модели; ограничения в security report.
- **OPS-02:** failure trap запускает web, но не восстанавливает предыдущие image/revision/schema. Это пробел rollback-процедуры, не наблюдавшийся outage.

Браузер: **80 уникальных сочетаний страницы/языка/ширины**, а не 80 полных пользовательских сценариев. Подтверждены overflow каталога (768→803px), admin-редактора (390→804px), 404 после прямого staff login и отсутствие выбора price_mode у волонтёра. Переполнение при заблокированном Google Fonts выделено как условная устойчивость к отсутствию CDN. Обычный owner login и добавление в избранное работают. [Browser](2026-09-08-project/browser.md).

UI source: UIA-01 — preview показывает другую валюту как ₼ и теряет смысл «от»; UIA-02 совпадает с BR-006; UIA-03 — отсутствуют цели aria-describedby. UIP-01 — очистка подкатегории недоступна с клавиатуры. QA-03/BR-005 — один localization gap; в сводке P2 из-за затронутых accessible names, без отдельного счёта двух дефектов.

SEO-01/02/03 P2: ограниченный аудит удаляет посторонние открытые issues; auto-fix помечает FIXED без семантической проверки; rollback рейтинга не восстанавливает старые значения. **Историческое утверждение о записи dry-run опровергнуто:** текущий fix dry-run возвращает несохранённый объект. Реальный audit запуск всё ещё имеет записи/удаления; команды не выполнялись. [SEO](2026-09-08-project/seo.md).

Общие причины не посчитаны дважды: QA-воспроизведения BE-01/BE-03 принадлежат backend; JSON-LD остаётся SEC-02; UI source и browser связываются по одному сценарию.

## 4. Технический долг

Legacy-поля служат одновременно входом миграции и текущей проекцией тарифов. Контракты сохранения и публикации расходятся между формами. Тестовое обнаружение, JS-зависимости и браузерные проверки требуют воспроизводимого запуска. Не назначается отдельный дефект каждому проявлению одной причины.

## 5. Риски и границы

SQLite/DEBUG/локальные фикстуры отличаются от production. PostgreSQL, конкурентные записи, текущие ограничения БД, восстановление backup и реальный deploy не проверены. Внешние браузерные ресурсы и интеграции блокировались; отсутствие CDN следует отличать от нормального rendered-поведения. Реальные Google OAuth/GA и production SEO неизвестны.

Часть security runtime-проверок была остановлена платформенным cyber-фильтром. Это не отказ sandbox auto-review. Полные auth/injection воспроизведения прекращены; соответствующие выводы ограничены source и уже выполненной структурной проверкой сериализации.

## 6. Legacy / кандидаты на удаление

Удалений не рекомендовано без отдельного доказательства. Старые pricing/schedule поля и команды имеют потребителей. Отсутствие узла в графе или теста в discovery не означает dead code. Исторические production-отчёты остаются датированными наблюдениями.

## 7. Проверки и пробелы

Точные команды, изоляция, результаты и классификация падений: [QA](2026-09-08-project/qa.md). Дополнительно выполнены три безвредных наблюдения сохранения данных, backup failure на синтетических файлах, shell syntax checks и Node AI-referral tracking test. Зелёные observation-тесты подтверждают выполнение наблюдения, а не корректность сохранения данных.

Domain reports: [Backend](2026-09-08-project/backend.md), [Security](2026-09-08-project/security.md), [Database](2026-09-08-project/database.md), [QA](2026-09-08-project/qa.md), [Admin UI](2026-09-08-project/frontend-admin.md), [Public UI](2026-09-08-project/frontend-public.md), [Browser](2026-09-08-project/browser.md), [SEO](2026-09-08-project/seo.md), [Devops](2026-09-08-project/devops.md), [Analytics](2026-09-08-project/analytics.md).

## 8. Рекомендованный порядок исправлений

1. Security: SEC-01/02 с проверками одноразового challenge и корректного HTML-контекста сериализации.
2. Сохранение данных: BE-01/03 и DB-01; сначала preservation-тесты, затем изменения путей сохранения. Отдельно выбрать семантику DB-02.
3. Backup: правильно обрабатывать сбой dump, не начинать retention после неуспеха; проверить восстановление на одноразовой PostgreSQL.
4. QA: подключить пропущенные тесты, классифицировать красный baseline и выполнить согласованный набор на изолированной PostgreSQL.
5. Исправить подтверждённые UI, analytics и SEO расхождения с целевыми проверками.

Это предложение будущего объёма. Исправления приложения, production, commit/push данным аудитом не разрешены.

## 9. Решение по приоритетам

**P0 не установлен. P1: SEC-01, SEC-02, BE-01, OPS-01, DB-01.** Остальные дефекты и условные риски — P2/P3 с границами в domain reports. Сначала согласовать узкий план P1; проект не объявляется полностью проверенным или готовым к релизу.

Final scope verification: all2686 tracked-file hashes match the audit start, application/infra diff against HEAD is empty, git diff --check passes. Ten domain reports have nine required sections; master links resolve. Local fixture server session ended with exit0. Only audit documentation was produced/updated; application and prior tracked work were preserved.

## Дополнение 2026-09-16: поисковая выдача и индексируемость

Новый отдельный AUDIT ONLY: [подробный отчёт](SEO_SEARCH_AUDIT_2026-09-16.md), [реестр 288 URL](SEO_URL_INVENTORY_2026-09-16.md), [source review](SEO_SOURCE_2026-09-16.md). Текущий local/server HEAD `01d330ba97397951d7f493670573391708436393`; старые выводы этого документа не переобъявляются актуальными.

Все 270 sitemap URL отвечают 200, имеют self-canonical и открыты для индексации; все 75 опубликованных карточек представлены на AZ/RU/EN. Выявлены политика noindex/canonical пагинации, вероятный дубль ABBA 19/20, FAQ вне sitemap и противоречивые условия внешней вакансии Holo. Чужие snippets сами по себе не доказывают санкций. AZJOB отдаёт разные ответы по User-Agent, поэтому первоначальная гипотеза удаления объявления не подтверждена. Фактический Google index и эффективность ожидают Search Console; доступа к кабинету в сессии пока нет. Приложение/production не изменялись; рекомендации не являются разрешением на исправления.

### Последующее внедрение 16 сентября (новое разрешение пользователя)

Пользователь подключил Search Console, затем прямо поручил выполнить SEO-улучшения с доступом к Git/серверу. Выпущен `f8005bb0a2308588b183a09890f35b659bc3f44f`: host redirect и отдельный robots для admin, индексируемая чистая пагинация каталога, FAQ в sitemap. 16 точечных Django-тестов успешны; публичные HTTPS-проверки успешны. Sitemap теперь 273 URL, включая 225 URL карточек. IndexNow принял 240 canonical URL (HTTP 200). Карточки 59, 63 и 45 уже индексируются по индивидуальной инспекции GSC — старые исключения не являются текущими дефектами. [Результат и границы](SEO_IMPLEMENTATION_2026-09-16.md).


## Дополнение 2026-10-07: текущая локальная приёмка заполнения

Решение: **FAIL**, 22 отдельные задачи (6 P1, 14 P2, 2 P3). [Свежий отчёт](/home/ramin/kidsmap/docs/qa/content-entry-acceptance-2026-10-07.md), [реестр задач](/home/ramin/kidsmap/docs/qa/content-entry-acceptance-2026-10-07/findings.json), [версия и сохранность](/home/ramin/kidsmap/docs/qa/content-entry-acceptance-2026-10-07/version-snapshot.json).

Исполнитель — один Codex /root (kidsmap-orchestrator), без независимых аудитов подагентов. LOCAL HEAD 2da9d33abbc53d1ac71bcb7e15a0170bef6277d5 + начальный dirty WORKTREE (109 записей), source digest 146a8499b61ea65cfe70640f38816d1ee83b903f877d46a9bf06fa5a47e27a9a. Отдельный QA http://localhost:8783/qa/, PostgreSQL/DB/media/cache/mail изолированы, только вымышленные данные; исторические отчёты и design-прототипы не засчитаны свежим доказательством.

P1: stale admin Event/Specialist молча теряет первое изменение; частичный Event draft без категории и каталог Specialist дают 500; UI модерации Place/Specialist блокируется. Все проблемы оформлены отдельно, приложение и тесты не исправлялись. 173 targeted tests OK; дополнительный набор 89 — 1 ERROR фикстуры. 240 страниц + 96 этапных снимков RU/AZ/EN, 360/390/768/1440 без document overflow; это не PASS полного функционального пути. UI/service обходы и NOT RUN перечислены в отчёте. Production не проверялась и не менялась; commit/push/deploy не выполнялись. Следующий шаг — решение пользователя по отдельным scope, не автоматическое внедрение находок.


## Content entry reacceptance —2026-10-09 (LOCAL only)

[Свежий отчёт](/home/ramin/kidsmap/docs/qa/content-reacceptance-2026-10-09.md), [таблица](/home/ramin/kidsmap/docs/qa/content-reacceptance-2026-10-09/evidence.json), [отдельная задача](/home/ramin/kidsmap/docs/qa/content-reacceptance-2026-10-09/findings.json). Root/kidsmap-orchestrator, последовательная приёмка, без независимых агентов и изменений приложения. HEAD2da9d33a + dirty217; source2766 SHA2103684f9e10e93c0fe4fed68c79ffd7215b15804124537abf3fdcc18f22e989 совпал до/после. Full catalog1909PASS,JS38PASS, browser478PASS/2FAIL: один P3 перевод поля даты личности Specialist RU/AZ. Изолированный synthetic stand8790; прежние631строка/17моделей8788 сохранены. Решение: PASS выполненных сценариев с указанными NOT RUN, полная приёмка открыта. Старые findings не закрываются автоматически этим числом тестов. Исправление CE-RA-01 требует отдельного принятия scope; готовый промпт в отчёте. Production/commit/push/deploy NOT RUN.


## Content completion —2026-10-09, approved local scope

[Отчёт](/home/ramin/kidsmap/docs/qa/content-completion-2026-10-09.md), [evidence](/home/ramin/kidsmap/docs/qa/content-completion-2026-10-09/evidence.json), [задачи](/home/ramin/kidsmap/docs/qa/content-completion-2026-10-09/findings.json), [собственный diff](/home/ramin/kidsmap/docs/qa/content-completion-2026-10-09/local.diff). CE-RA-01 FIXED LOCAL,48targeted/24labels/96keyboard-geometry PASS. Business-consent10/replay/preservation, shared-program detach/access, online owner event, Place/Org CAS, admin3entity lifecycle/public выполнены на synthetic8790. Решение **FAIL**: CE-C-01 P2 admin draft cover lost on publication; CE-C-02 P3 map copy contradicts optional server coordinates. Оба OPEN, готовые отдельные промпты, приложение по новым findings не исправлялось. Raw231PASS/4FAIL включает2repro одного фото и1false harness expectation; adjudication в evidence. NOT RUN в отчёте; независимых подагентов не было. Чужие изменения сохранены; production/commit/push/deploy NOT RUN.


## CE-C-01 —2026-10-09, approved local scope

[Отчёт](/home/ramin/kidsmap/docs/qa/ce-c01-fix-2026-10-09.md), [diff](/home/ramin/kidsmap/docs/qa/ce-c01-fix-2026-10-09/local.diff), [evidence](/home/ramin/kidsmap/docs/qa/ce-c01-fix-2026-10-09/evidence.json). CE-C-01 P2 FIXED LOCAL: main/fallback candidate photo survives POST without upload; explicit removal also survives draft→submit→review→publication. Two existing application files plus seven-test regression; other source and locale byte-identical. Current HEAD2da9d33a, source2768 SHA37ee6734cd60b82e248b3939f4dd001fa1dae586baf58eaad80bacb1472a034c matched isolated8790. Fresh PostgreSQL151PASS; final Chromium49PASS/0FAIL, RU/AZ/EN×360/390/768/1024/1280/1440, keyboard Enter/modal, public naturalWidth>0;10screenshots. RED and intermediate harness runs separated in evidence. Один root/kidsmap-orchestrator, последовательное выполнение, без независимых подагентов. CE-C-02 P3 OPEN, общая приёмка и NOT RUN остаются открыты. Production/commit/push/deploy NOT RUN; own active_run NONE.


## CE-C-02 —2026-10-09, approved local copy scope

[Отчёт](/home/ramin/kidsmap/docs/qa/ce-c02-fix-2026-10-09.md), [diff](/home/ramin/kidsmap/docs/qa/ce-c02-fix-2026-10-09/local.diff), [evidence](/home/ramin/kidsmap/docs/qa/ce-c02-fix-2026-10-09/evidence.json). CE-C-02 P3 FIXED LOCAL: подсказка карты теперь соответствует необязательным серверным coordinates; одна строка template + RU/AZ/EN PO/MO, остальные source/translations сохранены. HEAD2da9d33a, source2768 SHA7e78ba73f65870ce3fa2e7e7df5753d5764a79c8bf30ac8131122d8d1da72b96 matched isolated8790. Readiness33PASS; fresh Chromium66PASS/18FAIL, где18FAIL — один CE-C-03 P3: карта без ключа имеет активную кнопку без подключённого handler. CE-C-04 P3 — mobile caption clipping подтверждён red/green390 отдельно. Оба OPEN, отдельные repair prompts; JS/CSS не исправлялись. Native no-pin create/draft/reload/publish/public и сохранение существующей точки через review PASS;11screenshots. Root/kidsmap-orchestrator последовательно, без независимых агентов. Решение: copy scope завершён, весь map UI НЕ принят; full project sign-off/NOT RUN остаются открыты. Production/commit/push/deploy NOT RUN; own active_run NONE.


## Administrative Place map —2026-10-09, approved completion

[Отчёт](/home/ramin/kidsmap/docs/qa/admin-place-map-fix-2026-10-09.md), [diff](/home/ramin/kidsmap/docs/qa/admin-place-map-fix-2026-10-09/local.diff), [evidence](/home/ramin/kidsmap/docs/qa/admin-place-map-fix-2026-10-09/evidence.json). CE-C-03 и CE-C-04 FIXED LOCAL; все дополнительные подтверждённые дефекты этого map flow устранены. Root/kidsmap-orchestrator последовательно, без независимых агентов. HEAD2da9d33a, source2769 SHAaba704c7f1b63588abcea683f3f713cfff6081a6f92d7949860313ee522771f2 matched isolated8790;14file allowlist и сохранность остальных source/translation проверены.107 server PASS плюс повтор14; JS7 PASS после RED; fresh browser222PASS/0FAIL, RU/AZ/EN и360/390/768/1024/1280/1440, native positive/negative/CAS/review/public, keyboard/focus/inner clipping. Local SDK/denied adapters отделены от actual external integrations NOT RUN. Очистка географии/mandatory address/optional coordinates/ACL/publication неизменны. Решение: выполненный map scope PASS, общий project/production sign-off NOT RUN; новых подтверждённых OPEN в этом scope нет. Own active_run NONE, commit/push/deploy/production NOT RUN; прежние QA отчёты сохранены.
