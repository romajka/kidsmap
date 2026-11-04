# KidsMap — готовность сайта, 2026-11-02

Решение: действующий каталог пригоден для использования. Главные открытые задачи — актуальность контента, цены, пустые разделы и подтверждение эксплуатационной готовности. Полная готовность всех кабинетов, внешних интеграций, восстановления и коммерческого роста не подтверждена. Критических сбоев или обхода авторизации в проверенной выборке не обнаружено; это не полный аудит безопасности.

Текущий этап READ-ONLY: приложение, данные и конфигурация production не менялись. Изменён только этот отчёт. Предыдущие изменения названий категорий и счётчика относятся к отдельно завершённой работе в этой беседе.

## Снимок и доказательства

- LOCAL HEAD: `9cecbe15205c76fb7b9d0cc4416b9cd0f7808366`, ветка `codex/admin-draft-recovery-2026-10-26`; девять исходно изменённых файлов сохранены. Локальные тесты относятся к WORKTREE, не к чистому HEAD.
- PRODUCTION: образ `kidsmap:catalog-count-20261102`, метка `9cecbe15205c-catalog-count-20261102`; патч счётчика пока не зафиксирован в Git. Семь проверенных файлов сервисов авторизации, удаления, доступа, расписаний, поиска и готовности совпали с локальными по хешам. Полное совпадение всех исходников не утверждается.
- Проверены живые главная, карта, каталог, поиск British (четыре результата), мобильная панель фильтров, карточка British Academy, пустые разделы организаций и специалистов. Мобильный браузер: 390×844; это не тест физических устройств.
- Read-only PostgreSQL: агрегаты через публичный queryset, явные read-only транзакции и таймауты. Публично доступны 128 мест; внутренний статус published у 139 записей сам по себе не означает публичную видимость. Ожидающих миграций нет.
- Свежие LOCAL проверки: 66 backend + 91 security = 157 PASS, изолированные SQLite/cache/media/email, без production credentials. PostgreSQL-конкурентность и полный набор тестов не запускались; SQLite предупреждает о неподдерживаемом NULLS DISTINCT.
- Backend: place_readiness, test_owner_readiness_projection, test_place_age_program, test_filtered_tariff_presentation, test_public_map_paging. Security: test_email_verification_consumption, test_google_auth, test_password_reset, test_task33_specialist_privacy, test_task33_specialist_security_review, test_project_fixes_email.EmailChangeChallengeTests.
- Исполнители: ведущий `/root`, django-reviewer, security-reviewer, seo-reviewer по каноническим определениям. Production SSH/браузер проверял ведущий; SEO-специалист независимо выполнял публичные GET. Их локальные результаты не представлены как production acceptance.
- Детальные отчёты текущей сессии: `/tmp/kidsmap-readiness-backend-20261102.json`, `/tmp/kidsmap-readiness-security-20261102.json`, `/tmp/kidsmap-readiness-seo-20261102.json` (временные файлы). Уточнение к security-отчёту: последующая проверка ведущего выявила ноль заявок на удаление, включая просроченные.

## Таблица готовности

«Готово» означает прохождение указанной проверки, а не сертификацию всей подсистемы. «Не проверено» не означает неисправность.

| Область | Статус | Наблюдение и следующий шаг |
|---|---|---|
| Публичный каталог | Готово в выборке | 128 мест, карточки и поиск открываются. |
| Визуальный интерфейс | Готово в выборке | Главная, каталог и карточка выглядят последовательно; полного редизайна не требуется. |
| Мобильный интерфейс | Частично | Поиск, карточка и панель фильтров работают при 390×844; реальные Safari/Android не проверены. |
| Карта | Готово в выборке | Google-карта отрисована, показано 128/128; у всех публичных мест есть координаты. Точность каждого пина не сверялась. |
| Поиск и фильтры | Частично | Живой поиск работает; локальные проверки категории, возраста и тарифов проходят. Все сочетания на production не перебирались. |
| Категории | Частично | 12 категорий, названия сокращены; спорт 55, развлечения 19, парки 17, музеи 15, образование 7, творчество 4, водный отдых 3, зоопарки/наука/театр по 2, поддержка/танцы по 1. Приоритет — наполнение существующих. |
| Позиционирование | Требует правки | Главная обещает найти кружок, хотя каталог включает отдых и парки. Предлагается «Места и занятия для детей в Азербайджане». |
| Обещания на главной | Требует правки | «Точное расписание и цены… без лишних звонков» не соответствует 48 карточкам с ценой по запросу. |
| Организации и специалисты | Не готово по наполнению | Оба публичных раздела пусты и стоят в главной навигации. Скрыть до появления полезного наполнения либо наполнить. |
| Основные поля карточек | Готово по заполнению | У всех 128 есть адрес, координаты и основное фото. Это не доказательство достоверности и прав на фото. |
| Цены | Частично | Представление карточек: exact 11, free 15, from 30, custom 3, on_request 48, range 12, mixed 7, free_entry 2. Проверять по источникам, неизвестное не угадывать. |
| Расписания | Частично | 97 регулярных расписаний имеют публичные строки; 13 по записи, 12 круглосуточных, по 3 событийных и переменных. Фактические часы с учреждениями не сверялись. |
| Актуальность сведений | Частично | У 113/128 нет last_verified_at, за последние 30 дней отмеченных проверок нет. Это отсутствие зафиксированной проверки, не доказанная устарелость. |
| Контакты | Частично | Восемь мест без публичных контактов — все парки/площадки, что само по себе допустимо. Доставка звонков/WhatsApp не проверялась. |
| Переводы | Частично | По одной карточке без RU/EN названия и описания; в RU-подборке обнаружен AZ-фрагмент. Нужна редакторская вычитка. |
| Отзывы и доверие | Частично | На главной четыре отзыва — пока слабая база для выбора по рейтингу. Нужен сбор настоящей обратной связи. |
| Работа с владельцами | Частично | У пяти публичных мест заполнена связь владельца. Активность партнёров и договорённости не проверены. |
| Регистрация, почта, Google-вход | Частично | 91 локальная проверка security-группы прошла; настоящая доставка писем и внешний OAuth не проверены. |
| Модерация и публикация | Частично | Изучены версии, транзакции и повторная проверка прав; полный браузерный цикл и PostgreSQL-гонки не запускались. |
| HTTPS и приватные файлы | Готово в проверенной границе | DEBUG выключен, secure cookies и HTTPS redirect включены. Приватные mounts сохранены, прямых nginx aliases на них нет, локальные ACL-тесты проходят. |
| Ограничение попыток входа | Требует доработки/подтверждения | Не найдено отдельных ограничений login/reset в приложении и активном nginx. Внешний WAF неизвестен; атакующие проверки не проводились. |
| Удаление аккаунтов | Частично | Политика включена; автоматический process_account_deletions не найден в проверенных cron/systemd/контейнерах. Внешний запуск неизвестен. Сейчас заявок и просрочек ноль. |
| Правила и конфиденциальность | Частично | Страницы есть; RU/EN формулировка cookies «только функциональные» расходится с описанием GA. Юридическая проверка и права на контент не проводились. |
| Техническое SEO | Готово в выборке | Robots и sitemap 200; 445 уникальных URL. У 15 проверенных страниц корректные title/H1/canonical/hreflang и разбираемый JSON-LD; это не полный обход sitemap. |
| SEO-тексты | Частично | В примере description обрезан посреди слова до «6–14 ле». Исправить обрезку и языковые fallback. |
| Индексация и поисковый спрос | Не проверено | Текущий Search Console, позиции, запросы и поисковый трафик не проверялись. Sitemap не доказывает индексацию. |
| Аналитика | Частично | GA4 настроен, Yandex выключен. Получение событий и воронка поиск → карточка → контакт не подтверждены. |
| Скорость и нагрузка | Не проверено | Отрисовка наблюдалась; Core Web Vitals, нагрузочный тест и ёмкость сервера не измерялись. |
| Доступность | Не проверено полностью | Нет полной проверки клавиатуры, скринридера и контраста. |
| Сервер и схема БД | Готово в проверенной границе | Web/DB/Redis работают, DB/Redis healthy, перезапусков 0, свободно 47,9 GiB; ожидающих миграций нет. |
| Резервные копии | Частично | Два backup-задания, свежий файл от 02.11 02:15 UTC. Восстановление не тестировалось, внешняя копия не подтверждена. |
| Мониторинг | Не подтверждено | В проверенных заданиях не найден мониторинг доступности; внешние сервисы и уведомления неизвестны. |
| Воспроизводимый выпуск | Частично | Текущий патч production не закоммичен; локальное дерево содержит отдельные изменения карты. Нужен согласованный выпуск из зафиксированного состояния. |
| Продвижение и монетизация | Не проверено | Нет проверенных текущих данных о привлечении, конверсии, удержании и выручке. Нельзя считать коммерческую готовность доказанной только работающим каталогом. |

## Порядок работ

1. Убрать пустые направления из главного меню до наполнения; исправить позиционирование и обещания о ценах/расписании.
2. Организовать проверку карточек: цена, расписание, возраст, источник и дата проверки; начать с наиболее востребованных мест. Добавлять полезное наполнение в малые категории, не дробить их дальше.
3. Проверить внешние ограничения входа/reset и назначить ответственный процесс удаления аккаунтов; при отсутствии реализовать и протестировать отдельно.
4. Провести восстановление из резервной копии в изоляции, подтвердить внешнее хранение и уведомления о сбоях; оформить воспроизводимый Git-релиз.
5. Пройти настоящую регистрацию/восстановление/Google-вход и цикл владельца; проверить аналитику контактов, Search Console и скорость перед увеличением рекламы.

Все изменения приложения и production остаются рекомендациями. Этот аудит не даёт разрешения на их внедрение.

---

Ниже сохранён исторический отчёт. Его старые дефекты и ограничения не следует автоматически переносить на состояние 2026-11-02.

# KidsMap — LOCAL acceptance,2026-10-19

Git publication follow-up2026-10-19: user explicitly authorized committing/pushing all completed work to the current codex/module09-transfer-2026-10-16-r1 branch. The implementation acceptance below is historical at base75c6c18; production remains excluded. Versioned plan: docs/plans/project-fixes-2026-10-19.md; complete sanitized report: docs/reports/project-fixes-2026-10-19.md. Raw QA/runtime evidence stays local ignored. No main merge or deploy is authorized.

## Approved14 remediation —2026-10-19

Current decision: **all14items implemented and accepted LOCAL; production NOT_CONTACTED/NOT_APPLIED**. User explicitly approved the plan and local implementation of all14audit points. Modules01–13 remain closed. No commit/push, reset/clean/force push, deployment, production migration/restart/config/data/cleanup occurred. Source files and new migrations remain dirty for review.

Repository C:\kidsmap; origin https://github.com/romajka/kidsmap.git; branch codex/module09-transfer-2026-10-16-r1; unchanged HEAD75c6c18beb35f019a76e96543723448d8ed1cb7d. Two original stashes and implementation-entry dirty reports preserved.0142retained; additive0143_pending_email_change and0144_workflownotification_event_context_db_default tested on disposable PostgreSQL only.

Fresh evidence: full03 **2759/2759 PASS,1050.847s,exit0**, all2679baseline IDs retained,80new;139NodePASS;32standalone PythonPASS/1Windows-junctionSKIP;330responsive browser states and44interaction assertions. Browser visual review then found an empty email-error marker: one conditional markup fix plus one regression. Final UI04 **154/154 PASS,exit0** and **90repeat/additional browser states** cover that last change. The full2759result belongs to full03; it is not represented as another complete run after the markup-only delta. All other application source is identical. Check/drift passed on both snapshots. Exact source manifests/commands, retries and full per-point acceptance are local ignored evidence in docs/qa/project-fixes-2026-10-19/REPORT.md and acceptance.json. Original71audit evidence files were hash-verified unchanged.

| № | Проблема | Итог | Что изменилось | Доказательство |
|---|---|---|---|---|
| 1 | Подтверждение нового email | LOCAL PASS | Рабочий адрес меняется только после кода на новый. До этого новые приглашения и письма не дают прав. Хеш кода,10минут,5попыток,60секунд; проверены гонки, отмена, сбои отправки и удаление аккаунта. | test_project_fixes_email.py;154final focused;25browser actions |
| 2 | Права SEO-админки | LOCAL PASS | Изменения требуют POST,CSRF и нужных разрешений. Просмотр не даёт права запускать исправления или удалять историю. | 26SEO regressions;native dialog keyboard AZ/RU/EN |
| 3 | Приватные файлы при обновлении | LOCAL PASS | Добавлены два постоянных private volumes и явные корни. Оба хранилища запрещают прямой URL. Preflight останавливает выпуск при незащищённых файлах, включая остановленный контейнер. Перенос реальных файлов ещё требует отдельного выпуска. | Two real Docker containers;storage-review.md;3guard tests |
| 4 | Открытие SEO-отчёта | LOCAL PASS | Исправлено форматирование для Django6; динамический текст экранируется. | SEO report200;15responsive report states;escaped script assertion |
| 5 | Цены при публикации занятий | LOCAL PASS | Публикация и снятие занятия обновляют цены и доступность каталога с учётом вложенных тарифов. Сохранены старые скалярные цены, бесплатные и договорные варианты, валюты. | backend full331+6targeted;fresh full regression |
| 6 | Повреждённое расписание | LOCAL PASS | Некорректные JSON/дни/интервалы дают ошибку поля, сохраняя прежние часы; валидное «всё закрыто» остаётся доступным. | Owner HTTP,admin form,shared writer regression |
| 7 | Историческая площадка мероприятия | LOCAL PASS | Карточка мероприятия организации показывает утверждённое место, даже если площадку переименовали или скрыли. | Approved snapshot regression;real organization screenshot |
| 8 | Будущая работа специалиста | LOCAL PASS | Будущая работа помечена датой начала на AZ/RU/EN и не выдаётся за текущую. Согласия и версии связи перепроверяются. | Future/stale ownership regression;real organization screenshot |
| 9 | Запросы страницы организации | LOCAL PASS | Вместо30/74запросов для1/5филиалов —23/23; с занятием и тарифом в каждом филиале —26/26. Данные читаются пакетно без постоянных доверенных кэшей. | Final full BACKEND_QUERY_BUDGET and BACKEND_ACTIVITY_QUERY_BUDGET |
| 10 | Сохранение SEO-истории | LOCAL PASS | Частичная или неудачная проверка сохраняет прежние замечания. Закрываются только фактически проверенные и исчезнувшие проблемы. | Scoped/failed audit regressions;SEO report |
| 11 | Честный результат автоисправления | LOCAL PASS | Статус fixed требует повторной проверки исходной проблемы.200сам по себе недостаточен;404/неизвестное правило/непроверяемая схема не получают ложный успех. Несвязанные рейтинги больше не меняются. | Invariant/schema negative regressions |
| 12 | Настоящий откат рейтинга | LOCAL PASS | Поддерживаемые старые изменения восстанавливают сохранённые числа атомарно. При последующих изменениях данных откат отказывается перезаписывать их. Необратимые действия так и помечаются. | Exact restoration/repeated rollback/interference tests |
| 13 | Совместимость миграции уведомлений | LOCAL PASS | 0142не переписана.0144оставляет SQL default {}, поэтому старый INSERT после миграций работает. Проверен заполненный переход0141→0142→0144и обратимость0144; выпуск блокируется без подтверждённой остановки писателей. | SQL old worker INSERT;MigrationExecutor rehearsal;3release boundary tests |
| 14 | Запросы sitemap | LOCAL PASS | Для5/25занятий и15/75локализованных URL:12/52→2/2запроса. Проверены языки, снимки, скрытые программы, устаревшая связь и повторное использование генератора. | Final full SITEMAP_QUERY_BUDGET;canonical batch contract |

Release boundary: docs/PRIVATE_STORAGE_RELEASE.md is the concrete future preservation/migration/verification/recovery plan. Protect and verify existing private bytes before replacement; prepare both named volumes with0700roots; stop all writers for the entire0142–0144batch. New SQLdefault preserves old INSERTs after0144, but rollback to old app code reintroduces the email/SEO defects, so keep affected mutations blocked. Production topology, mounts, actual schema, backup restore and external SMTP/Google/search indexing remain unverified. Docker Compose CLI is absent locally: actual source-matched named volumes/containers/storage and a narrow Compose-ps adapter were exercised, not compose up. Physical devices/Safari and production performance were not tested.

Measured query budgets: Organization1/5branches30/74→23/23; with one priced Activity perbranch26/26. Activity sitemap5/25activities12/52→2/2. These measurements do not promise production latency. Legacy current-email accounts without any proof rows retain unchanged-address compatibility, with no invented verification; existing mismatched proof rows fail closed.

One pre-existing cosmetic observation outside the14scope: owner_places.html:84Organization-links controls use tight/native styling and plain links. No measured functional/overflow regression; source unchanged. Proposed separately, not silently implemented. Own labelled test containers/volumes/network/localhost relay and own browser session stopped; source/profiles/evidence retained. active_run closed by lead.

## Historical audit before implementation


Mode: **AUDIT ONLY**. User requested a broad project review, tests, bugs and optimization/SEO recommendations. No application fixes, commit, push, deployment or production access. Modules01–13 and prior accepted fixes remain CLOSED LOCAL in their earlier verified boundaries; this audit does not restart them. New findings require a separate agreed implementation scope.

Decision: **address authorization defects and private-file persistence before recommending a release**. No current production compromise, outage or data loss is established. Source-level defects are accompanied by isolated reproductions; production applicability remains UNKNOWN until a separate read-only preflight.

Lead: `/root`, canonical kidsmap-orchestrator; specialist definitions from `.agents/registry.json`. Backend and SEO specialists supplied source audits, then reviewed root-owned runtime evidence. Security specialist supplied source report/probes but did not complete final runtime sign-off; `/root` independently validated six prepared synthetic probes and source boundaries. No claim of independent security runtime execution.

## 1. State and snapshot

- Repository `C:\kidsmap`, origin `https://github.com/romajka/kidsmap.git`, branch `codex/module09-transfer-2026-10-16-r1`.
- LOCAL HEAD `75c6c18beb35f019a76e96543723448d8ed1cb7d`. Entry tracked/untracked tree clean; two existing stashes left untouched. Entry manifest3106tracked files preserved locally before report/journal edits.
- Disposable runtime: exact `git archive HEAD`, read-only source mount; Python3.12.15, Django6.0.9, PostgreSQL17.11, Node24.14.0, jsdom29.1.1, isolated Playwright Chromium. Deps image `sha256:0f663c65afc2230d52db10c87ec91996666838377e5d9c8bd90fc41e7610b8b1`.
- DB instances have networking disabled, dedicated qa_stage04/test_qa_stage04 and owned Unix sockets. Existing `scripts/run_isolated_quality.py` clears inherited environment, verifies actual database/role/socket and uses disposable media, LocMem cache/mail and disabled external integrations.
- Codebase Memory `C-kidsmap`: ready but generation2026-10-16T18:56:53Z predates this source. Architecture/symbol/impact tools used first; cited paths reported changed/unavailable coverage. Relevant source/routes/ORM were read directly; historical graph copies were not treated as active code or completeness evidence.
- PRODUCTION: NOT_CONTACTED. Actual image/SHA/schema/data/private mounts, mail, Google and search-console state UNKNOWN. Previous dated release authorization in the old decision pointer is history; current task supplies no production-write authorization.

## 2. Strengths

- Versioned publication candidates, rechecked authorization, ordered parent locks, PostgreSQL constraints and compare-and-swap operations have substantial existing regression coverage.
- Catalog/map readers already include batching and paged data. Organizations, events, specialists, teams and immutable occurrence facts have implemented domain contracts.
- Current JSON-LD serializer escapes script delimiters; Event schema/sitemap exist. Owner readiness delegates to the canonical evaluator. Old findings claiming otherwise were retired for this snapshot.
- Private specialist downloads are access-controlled and outside public media. The confirmed storage issue below concerns persistence across container replacement.
- Fresh public/login, account/editor and selected admin responsive matrices contain no unexpected local HTTP errors, page errors or horizontal document overflow in the tested fixtures. This is bounded browser evidence, not full accessibility/device/provider acceptance.

## 3. Confirmed problems

IDs are deduplicated. All environments below are LOCAL exact HEAD; affected production records/exposure are UNKNOWN. Detailed evidence is local and ignored under `docs/qa/project-audit-2026-10-19/`.

| ID / priority | Trigger and observed effect | Source / owner |
|---|---|---|
| SECURITY-01 / P1 | An active user changes profile to an unused, unverified invited email, discovers the invitation in inbox and accepts it. Both place and organization grant paths reproduced without control of the fictional mailbox. Existing-user account takeover is not claimed. | `src/catalog/forms.py:791`, `controllers/auth_controller.py:111`, `controllers/workflow_notifications.py:23`, `services/business_team.py:219`; Django/security |
| SECURITY-02 / P1 | Ordinary nonvolunteer staff with zero model permissions uses GET custom SEO admin URLs. Synthetic history was deleted; auditor/fixer write-mode dispatch reproduced with service mocks. GET also lacks POST/CSRF protection. | `src/catalog/domain_admin/seo.py:39`, handlers61/77/95; admin/security/SEO |
| SECURITY-03 / P1 conditional release risk | Compose persists media/static only. `/kidsmap-private-media` and `/app/private_media_drafts` are writable-container paths. Two clean containers using this mount pattern retained the public synthetic file but lost both private markers. Current production file existence and full app recovery remain unverified. | `src/config/settings.py:497`, `src/catalog/private_storage.py:17`, `services/server_drafts.py:124`, `docker-compose.yml`; release/security/DB |
| SECURITY-04 / P2 | Opening a persisted SEOAuditRun report produces real authenticated Chromium HTTP500. `format_html` receives no interpolation arguments and Django6 raises TypeError. | `src/catalog/domain_admin/seo.py:159`; admin/SEO |
| BE-01 / P2 | Activity approval leaves Place scalar price NULL while public nested tariff137AZN exists; the public catalog excludes the place. After unpublish there are0public plans but legacy fallback still displays137AZN. | `src/catalog/services/publication.py`, `services/pricing_plans.py`, `services/content_quality.py`; Django/DB |
| BE-02 / P2 | `[null]` or `[{}]` schedule JSON raises TypeError/KeyError in all three owner/admin form constructors. Invalid JSON in the shared helper can validate as seven closed days and overwrite a real schedule; the latter proof isolates the helper, not a complete owner/admin HTTP save. | `src/catalog/forms.py:135`; Django/owner/admin |
| BE-03 / P2 | Organization Event card displays today's Place name instead of approved `venue_snapshot.label`, while Event detail retains the historical venue. | `src/catalog/controllers/public_details.py:141`; Django/public UI |
| BE-04 / P2 | Confirmed employment starting30days later appears as an ordinary specialist on Organization page without future state/date; the same specialist profile correctly classifies it as future. | `src/catalog/controllers/public_details.py:98`, `services/specialist_presentation.py:35`; Django/public UI |
| BE-05 / P2 optimization | Warm Organization detail measured30SQL queries for1branch and74for5: +11queries per extra branch. Reader materializes all branches and performs per-branch enrichment. No production latency or index prescription is inferred. | `src/catalog/controllers/public_details.py:26`, `services/public_presentation.py`; Django/DB |
| SEO-PROJECT-01 / P2 | Partial sitemap/schema/links audits and scanner failure erase unrelated open SEOIssue rows. Synthetic ORM proofs show all four retention scenarios lose the old issue. | `src/catalog/services/seo_audit_engine.py:69`; SEO/Django |
| SEO-PROJECT-02 / P2 | `missing_canonical` remains absent, but safe-fix records `fixed` after HTTP200 and after HTTP404. The original metadata invariant is not rechecked. | `src/catalog/services/seo_fix_engine.py:112`; SEO/Django |
| SEO-PROJECT-03 / P2 | Rating fixture9/4.5 becomes0/0 after recalculation; rollback remains0/0 while recording `is_rolled_back=True`. Old values are not restored. | `src/catalog/services/seo_fix_engine.py:155`; SEO/Django/DB |
| RELEASE-01 / P2 rollout risk | After0142, `event_context` is NOT NULL without a persistent SQL default. An INSERT matching old code and omitting the field fails. Existing deploy script migrates while the old web stays online; code-only rollback is not established safe. | `src/catalog/migrations/0142_workflownotification_event_context.py`, `scripts/deploy-server.sh:64`; release/DB |

Confidence HIGH for these isolated observations. SECURITY-03 impact is conditional on corresponding files existing at container replacement; no assertion of production data loss. RELEASE-01 is a tested mixed-version compatibility constraint, not a failed migration. Every proposed remediation must preserve existing permissions, historical facts and legacy compatibility.

## 4. Tech debt

- Verified current email has multiple representations/consumers; mutable User.email is used as authorization identity in invitation paths.
- Custom admin endpoints need a consistent explicit action-permission, method and CSRF contract. Default admin wrapper access does not establish model-action authorization.
- Projection updates through signals coexist with QuerySet.update publication transitions. Tariff/public-visibility readers and writers must share a declared refresh contract.
- SEO engine tests assert statuses more strongly than restored values or original metadata invariants; diagnostic false-green remains possible.
- Private storage paths need one complete persistent/backup inventory; source defaults alone are insufficient for release and recovery.
- Historical knowledge pages predate major schema/runtime changes; use them for navigation, then verify current source.

## 5. Risks and limits

No production crawl, SQL, credentials, logs, image inspection, data changes, migration, restart, backup or cleanup. No user records/private bytes copied from production. No live SMTP/OAuth/Google Maps/Search Console, physical devices, Safari/Firefox, full screen-reader acceptance, dependency advisory audit or full production restore drill.

Browser fixtures:26fictional Places,1Organization,5affiliated branches and synthetic accounts. External unpkg.com/maps.google.com/fonts.googleapis.com blocked; real provider geometry and remote-font fidelity are not certified. Public metadata passed the sampled locale/route matrix; that does not establish search-engine indexing/rank or production canonical host correctness.

Authentication throttling, OTP concurrency, direct tariff-write races and broader team resolver query costs are source-review risks requiring scoped measurements, not confirmed exploits. All source-only optional currency scenarios are explicitly NOT RUN. Historical10000-place performance and carousel observations were not remeasured or silently closed.

## 6. Dead / legacy candidates

No deletion recommended or performed. Scalar/JSON/text compatibility paths, identity wrappers and historical events remain in use or usage UNKNOWN. Graph absence, empty synthetic tables and tests alone do not establish safe deletion of code or DB structures.

## 7. Fresh checks

Full Django gate: **2679tests PASS,0failures/0errors/0skips,806.098s, exit0**. Fresh migrate (including catalog0142), system check and `makemigrations --check --dry-run` completed. All2679discovered methods appear in the log; this is a current run on this PC, not the source-PC historical result.

Other completed checks:

- Node25workflow unit/DOM files:139PASS,0FAIL,0SKIP, exit0, with actual authenticated Django photo-form fixture.
- Standalone Linux Python:27tests,26PASS/1Windows-junctionSKIP, exit0. `pip check`: no broken requirements.
- Extra characterization:14tests OK/2.805s, exit0:6security +7backend +1migration. PASS here means the defect/constraint reproduced; it is not a product acceptance result.
- SEO ORM: four retention cases,200/404false-fix cases, rating rollback; synthetic transactions rolled back, network mocked. Exact-source safe-serialization probe also passed.
- Real Chromium:240responsive states =105public/login +60account/editor +75admin, AZ/RU/EN ×390/768/1024/1280/1440. All sampled routes200, no unexpected local HTTP errors/page errors/document overflow; public JSON-LD parse, main landmark, images and basic button names checked.19keyboard/navigation/search checks passed. Additional persisted SEO report intentionally reproduced HTTP500 and remains OPEN.
- Container replacement marker proof and0142SQL-default compatibility proof reproduced the release risks. This is not a full upload/recovery or production migration rehearsal.

Exact scripts/commands, logs, JSON and failed-attempt ledger are local under `docs/qa/project-audit-2026-10-19/commands.md`, `attempts.md`, `entry.json`, `security-runtime-validation.md`, `backend.md`, `seo.md`. Screenshots: `output/playwright/project-audit-2026-10-19/`. Intentionally absent historical docs/qa/verify_transfer.py were not restored. No test assertions or application source were changed for green.

## 8. Recommendations and handoff

1. Agree a first scope for SECURITY-01/02: verified email identity and explicit SEO admin action authorization/method/CSRF; negative tests for ordinary/staff/volunteer/reviewer/superuser and current/pending addresses.
2. Before any release, agree persistent private-root configuration and byte-preserving transition/recovery acceptance for SECURITY-03. Coordinate0142with old/new writers and rollback; do not run the broad deploy script as a diagnostic.
3. Address BE-01/02with one domain contract for tariff projection/visibility and shared fail-closed schedule validation. Preserve legitimate missing-input/draft/legacy paths.
4. Repair SEO report rendering, retention, actual metadata rechecks and truthful rollback semantics. Engine green status must not be used as current SEO acceptance until fixed.
5. Optimize Organization branch reader first: measured+11queries per branch. Separately Activity sitemap measured12queries/5activities/15URLs versus52queries/25activities/75URLs (warm local0.0345s→0.1084s). This is a P3 batch-reader candidate, not a demonstrated production latency incident or promised speedup.
6. Align Event venue and employment timing across public projections; then repeat affected locale/browser checks. Optional Event schema image enrichment and broader SEO audit coverage follow correctness/security work.

Named next owners: Django/security for identity and custom admin boundaries; release/DB/security for persistent storage and0142rollout; Django/DB for pricing/schedules/query batching; SEO/admin for diagnostic engine and report; integration/browser for acceptance. Implementation awaits user's decision on concrete scopes.

## 9. Priorities and decision

- P0: none established.
- P1:2confirmed authorization defects (SECURITY-01/02) and1conditional private-storage release/data-loss risk (SECURITY-03).
- P2:10confirmed isolated bugs/rollout constraints (SECURITY-04, BE-01…05, SEO-PROJECT-01…03, RELEASE-01).
- P3/candidates: measured Activity sitemap query scaling, diagnostic coverage/schema enrichment, contract consolidation. Unmeasured risks are not promoted to confirmed findings.

Recommendation: remediate the P1 boundaries/storage risk first; source and current test success do not authorize production release. Preserve module closure and existing work; stop at recommendations. The previous decision pointer is preserved in local `docs/qa/project-audit-2026-10-19/master-before.md`.

## Specialist onboarding E2E — 2026-11-04

New bounded AUDIT ONLY; previous entries and dirty application work preserved. LOCAL HEAD `b7659e79` plus dirty WORKTREE, production NOT RUN. Lead `/root` (kidsmap-orchestrator), support `/root/specialist_backend_audit` (django-reviewer).

Decision/evidence: [specialist-e2e-audit-2026-11-04.md](../reports/specialist-e2e-audit-2026-11-04.md), [backend audit](../reports/specialist-backend-audit-2026-11-04.md). Synthetic browser journey covers homepage, registration/local email code, login, draft, photo, self/other submission, admin publication, queue removal, separate identity approval, document upload/review/private access and public display. PostgreSQL targeted suite 108/108 PASS, repeated after source capture; rendered RU/AZ/EN × five widths for owner and admin, with additional final owner pass. No application fixes/commit/push/deploy.

**P1 SP-01:** staff with view_specialist but no change_specialist can publish through both admin lists (isolated HTTP/DB proof). P2: return-for-revision does not restore first applicant editing; publication and identity decisions are poorly connected and review omits applicant identity; readiness says 100% without required offline location; auth drops next; invalid phone accepted; admin document table and mobile layout broken; document upload feedback and public-visibility badge misleading. Main journey submits/publishes successfully and published item leaves pending queue, but that is not complete UX/security acceptance. Fix authorization and revision lifecycle first; implementation awaits user's scope decision.

## 2026-11-04 — Specialist onboarding: APPROVED IMPLEMENT / LOCAL

После прямого разрешения пользователя исправлены SP-01–SP-13 из сквозного аудита: server-side права действий обеих админок, возврат и повторная отправка той же анкеты, явная отдельная проверка личности с данными заявителя, readiness/телефон/next, документный uploader, responsive admin и реальная публичная видимость. Self по умолчанию без переключателя, компактная подсказка; legacy other drafts сохранены. Дополнительные реальные дефекты выбора места, восстановления subject и очистки направлений/языков устранены.

Проверка:253 Django/PostgreSQL PASS;26 focused PASS после финального изменения контроллера;13 Node PASS; owner15 +admin21 responsive states AZ/RU/EN и3menu states, фактический регистрационный и moderation/document lifecycle. После параллельной правки owner CSS/template выполнена повторная матрица15. Исправления LOCAL WORKTREE поверх b7659e79a25d2ae8d23cd505ec46755683223c09; production/commit/push/deploy не выполнялись, чужие dirty изменения сохранены. Полный отчёт и границы: [specialist-onboarding-fixes-2026-11-04.md](../reports/specialist-onboarding-fixes-2026-11-04.md). Не распространять PASS на все модули или на будущие изменения общего checkout.


## 2026-11-04 — Отдельная страница анкеты специалиста (LOCAL)

По прямой просьбе пользователя форма create/resume/edit выведена из account shell. Возвращена sticky-навигация с готовностью слева на desktop, mobile disclosure с переносом фокуса.22 Django +15 Node PASS;16 responsive/language states +3 owner-edit states,0 overflow после исправления action-row на1024px. Draft save/reload и validation подтверждены в Chromium. [Отчёт](../reports/specialist-editor-layout-2026-11-04.md). Production не изменялся.


## 2026-11-04 — Публичная карточка специалиста: AUDIT ONLY

Вывод: нужны исправления перед выпуском. Найден P1 HTML/XSS sink в карте (accepted form → rendered EN callback → bounded provider stub), P2 locale coordinates/RU-AZ map failure, неверные rating stars, WhatsApp formatting, price/age edge rendering. Browser подтвердил mobile порядок условий после отзывов, guest-review auth dead end и keyboard-inaccessible rating.42 existing tests +6 isolated probes; каталог→карточка и review submit→admin approve→public пройдены. Новые findings не исправлены. [Отчёт и локальная демо-ссылка](../reports/specialist-public-e2e-2026-11-04.md). Сервер демо оставлен включённым для пользователя. Production не изменялся.


## 2026-11-04 — Specialist mobile public: APPROVED IMPLEMENT / LOCAL

По прямому запросу пользователя исправлены публичные PUB-B01–B07 и мобильные UX-находки: безопасная/локализованная карта, цены/возраст/рейтинг/контакты, компактная карточка с закреплёнными CTA, guest login до отзыва, native keyboard rating. Дополнительно реальный browser401→новый вход→retry выявил CSRF rotation403: исправлен актуальный token без потери текста. В каталоге исправлены dialog/focus/inert/Escape и keyboard dropdown options.

[Отчёт и ограничения](../reports/specialist-mobile-public-2026-11-04.md). Полный найденный specialist корпус **185 PostgreSQL PASS**, отдельная shared integration **71 PASS**, **31 Node PASS**. Первые11 failures/errors полного SQLite-прогона были PostgreSQL guards/concurrency lock; assertions не ослаблялись, полный повтор на disposablePG успешен. Browser:21RU/AZ/EN responsive profiles,9catalog,5long-text widths, настоящие login/network/retry/review moderation + документы200/404. Принятая редакция появляется публично и больше не ожидает решения. XSS/numeric-map browser proof использует ограниченный provider stub.

LOCAL dirty WORKTREE поверхb7659e79;13файлов зафиксированы хешами в scratch/source-final.json. Несвязанный dirty work сохранён. Продакшен, физические телефоны/Safari/Firefox и настоящий внешний Google provider NOT RUN. PUB-M01 скрытое Place.name без ссылки сохраняет прежний продуктовый контракт. Preview8894 оставлен для оценки; синтетические данные не публиковались вне локального стенда.


## 2026-11-04 — Specialist soft motion follow-up / LOCAL

User requested gentle animation details. Scoped CSS-only motion + stylesheet cache version, no business changes. [Report](../reports/specialist-soft-motion-2026-11-04.md): normal320/390/768/1440, reduced320/390/1440 browserPASS; no overflow/pageerror, native keyboard disclosure and fixed CTA preserved;11existingJS regressionsPASS. The two deliberate source updates supersede their earlier mobile acceptance hashes; current hashes in `.tmp/specialist-motion-20261104/source-final.json`. Production NOT RUN.

## 2026-11-04 — Публичный сайт: мобильный AUDIT ONLY

[Сводный отчёт](../reports/public-mobile-audit-2026-11-04.md). LOCAL dirty WORKTREE поверх `b7659e79`; production NOT RUN. Root + browser-qa + frontend-reviewer: **249 валидных сочетаний страницы/языка/ширины**, без горизонтального переполнения; отдельные функциональные сценарии и просмотр screenshots. Исходный specialist preview8894 сохранён; общая проверка на отдельной копии8896 с синтетическими местами/событиями/организациями. Это не249 сквозных сценариев и не полная сертификация сайта.

**P1:** FAQ ложно подтверждает отправку, запросов вообще нет. **P2:** неправильные summary stars и отсутствующий автор в typed reviews; keyboard dropdown в организациях и каталоге; «Сегодня закрыто» вместо статуса текущего момента; гостевой тупик отзывов; низкое расположение цены/контакта занятия; FAQ игнорирует reduced motion. P3: плотность входа/FAQ, мобильный календарь, разное оформление действий, одинаковые подписи гидов, поиск/числительные организаций. Всего1P1/7P2/5P3; UX-оценки явно отделены от функциональных ошибок.

Подготовлен конкретный план исправлений и приёмки, application changes в этом аудите не выполнялись. В соответствии с canonical audit contract остановка на рекомендациях до решения пользователя. Реальные телефоны, Safari/Firefox, внешние OAuth/Maps/email и production не проверены; пустоты от незавершённых reveal и неверные тестовые locale-slug исключены как ложные срабатывания.

## 2026-11-04 — Публичный mobile: APPROVED IMPLEMENT / LOCAL

По прямому разрешению пользователя исправлены все 13 пунктов предыдущего аудита. [Итоговый отчёт](../reports/public-mobile-fixes-2026-11-04.md): FAQ без ложного получения обращения; корректные звёзды/автор/гостевой вход; статус расписания; keyboard dropdown и reduced motion; компактные auth/FAQ, календарь, контакты занятия, поиск организаций и оформление событий. Дополнительно исправлена подтверждённая browser-негативным сценарием утечка языка ошибок LoginForm между запросами.

166 PostgreSQL regression PASS; затем 10 focused PASS и окончательные 54 auth/focused PASS (пересекающиеся наборы, не суммировать). 21 JS PASS. 283 responsive states без overflow/broken complete images/pageerror/local HTTP errors, отдельные функциональные и негативные проверки; последние изменения дополнительно проверены на затронутых страницах. Один исполнитель, независимый повторный аудит не заявляется.

LOCAL dirty WORKTREE поверх b7659e79; 25 файлов зафиксированы source-final.json. Прежний и параллельный dirty work сохранён. Preview8894 и8896 работают; disposable PostgreSQL после тестов остановлен. Production/deploy/реальные устройства/Safari/Firefox/внешние отправки NOT RUN. Все согласованные находки закрыты в проверенной области, без обещания отсутствия любых ошибок.
