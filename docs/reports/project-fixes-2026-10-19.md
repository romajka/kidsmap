# KidsMap: выполнение14пунктов,2026-10-19

Все14пунктов реализованы и приняты **LOCAL**. Production не контактировался и не изменялся. Модули01–13 не открывались заново. Commit/push не выполнялись.

## Состояние

`C:\kidsmap`, origin `https://github.com/romajka/kidsmap.git`, ветка `codex/module09-transfer-2026-10-16-r1`, HEAD `75c6c18beb35f019a76e96543723448d8ed1cb7d`. WORKTREE dirty: изменения реализации и отчётов оставлены для просмотра. Два исходных stash сохранены. До реализации сохранены3106хешей, исходные dirty-отчёты и binary diff в entry.json/entry.patch/entry-files.0142на месте; новые0143_pending_email_change и0144_workflownotification_event_context_db_default применялись только в одноразовых QA-БД.

План: `docs/plans/project-fixes-2026-10-19.md`. Разрешение пользователя на все14пунктов дано до начала реализации. Канонические роли прочитаны; lead /root, три специалиста с разделёнными файлами; дополнительная проверка storage выполнена специалистом, не писавшим storage implementation. Общие тесты и browser acceptance выполнены lead.

## По пунктам простым языком

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

## Свежие проверки и точные границы

- Полный `final-full-03`: **2759/2759 PASS**,1050.847сек,exit0;2679ID прежнего полного аудита сохранены,80новых. `check` и `makemigrations --check --dry-run` прошли. Запуск через существующий `scripts/run_isolated_quality.py`, DJANGO_TESTING=1, свежий PostgreSQL17.11 с Unix socket и выключенной сетью, отдельные cache/media/mail.
- После полного snapshot визуальная проверка выявила пустой красный индикатор email. Browser RED доказал valid=true/emptyError=true/errorClass=true/`!`. Исправлен **только условный error marker** в account_profile.html, добавлена одна регрессия. Финальный `ui-final-04`: **154/154 PASS**,exit0,check/driftPASS. Повторно выполнены60состояний кабинета/редактора и30состояний обычной/ошибочной формы. Полный2759прогон относится к full03; последний markup patch принят целевыми154и90browser, а не назван повторным полным прогоном. Единственные отличия full03→ui04: этот шаблон, его тест и уточнение текста recovery guide. Остальной source полностью совпадает; manifests сохранены.
- Node24.14.0/jsdom29.1.1: **139/139 PASS**,25unit/DOMfiles,0skips, с реальным HTML Django photo form. Node inputs и относящиеся к photo form исходники после этого прогона не менялись. Три отдельные browser-fixture scripts не выдаются за Node unit coverage.
- Standalone Python: **32PASS/1SKIP**,33tests; единственный skip — Windows junction на Linux. `python-final.log` содержит полный список, включая остановленный контейнер и writer boundary.
- Chromium: **330responsive states** AZ/RU/EN×390/768/1024/1280/1440:105public/login,60account/editor,105admin/report,60email pending/expired/exhausted/empty; затем90повторных состояний для последней markup-правки. **44functional assertions**:19navigation/menu/search и25email/SEO; Enter/Tab/Escape/focus/CSRF присутствуют.0unexpected JS/local HTTP/static errors,0document overflow в измеренных состояниях. Ожидаемые400на плохой/истёкший код и блокировки внешних fonts/maps выделены отдельно, а не скрыты под «console clean».
- Реальные local Docker volumes/два successive containers сохранили оба synthetic payload. Файлы0600, дочерние каталоги0700. Корни volumes по умолчанию0755: runbook требует явную подготовку0700; после неё0700сохранились. Compose CLI в WSL отсутствует: source YAML разобран, фактические точки монтирования выполнены через Docker; это **не docker compose up**. Stopped-container guard дополнительно проверен на реальном остановленном Docker container с узким adapter для Compose ps.
- Миграционный тест сохранил старое уведомление0141→0142→latest, проверил history context, reverse/reapply0144и SQLINSERT без event_context. Схему production, его версии, реальные backups/ACL/volumes мы не проверяли.

Точные команды, sourceSHA256, exits и все попытки: `*-source.json`, `*-result.json`, `*.log`, acceptance.json. Основные команды: `python docs/qa/project-fixes-2026-10-19/run_quality.py --name final-full-03 --keep`; `run_quality.py --name ui-final-04` с семью labels из ui-final-04-source.json; `run_browser.py` с именами сохранённых browser scripts. Собственный wrapper только создаёт immutable snapshot/свежую среду и вызывает проектный launcher; production credentials не наследуются.

## Повторные попытки и ограничения

Сохранены ожидаемые RED, промежуточный sitemapRED, неверный stale-affiliation fixture(нулевая версия нарушала DB check; заменена реальным изменением ownership version), environment-only readonly.tmp/Windows encoding ошибки, два отменённых full01/full02(exit137) до финального full03. Browser retries отделены: неверные поля syntheticSEOIssue, cp1251fixture copy, concurrent navigation, незаполненные обязательные поля и ожидание немедленной повторной смены вопреки60сек cooldown. Их нельзя считать product PASS или удалять из истории. Непустой красный email marker был реальной найденной UI-регрессией и исправлен с отдельной RED/GREEN проверкой.

Live SMTP delivery, Google/OAuth providers, карты/CDN, Search Console, индексация поисковиками, Safari/физические устройства и production нагрузка/данные/конфигурация **NOT RUN**. Локальные query budgets не являются обещанием production latency. Старые неоднозначные email без каких-либо proof rows не переведены автоматически в verified: сохранена совместимость неизменённого legacy адреса; имеющиеся несовпадающие proof rows fail closed. Это не ретроспективная проверка владения всеми историческими адресами.

## Отдельный будущий выпуск

Исполнимый порядок и recovery boundary: `docs/PRIVATE_STORAGE_RELEASE.md`. Перед выпуском отдельно проверить actual server SHA/schema/mounts, остановить всех писателей/traffic, сохранить и проверить оба private tree вне старого container, подготовить/восстановить private volumes, выполнить полную0142–0144batch с писателями выключенными, проверить SQLdefault и включить только проверенную новую версию. Затем выполнить release smoke, authenticated/foreign/anonymous private download, email/invitation/SEO checks и включить private volumes в backup/restore schedule. Flag KIDSMAP_WRITERS_STOPPED=1 только подтверждает уже выполненную оператором остановку; сам ничего не останавливает. Обычный online rollout этого перехода небезопасен. Старый код даже при совместимой схеме возвращает security defects, поэтому affected mutations при recovery должны оставаться заблокированы. **На этом task остановлен перед любым production применением.**

## Дополнительное наблюдение вне14пунктов

Неблокирующая визуальная доработка: в кабинете владельца блок «Связи с организациями» содержит тесные native select/button и простые синие ссылки; остальной кабинет стилизован. Это существующая разметка `src/catalog/templates/pages/owner_places.html:84`, файл не менялся, функциональных/overflow ошибок в проверенных ширинах нет. Скриншот `output/playwright/project-fixes-2026-10-19/final/owner-ru-1440.png`. Визуальное оформление предложено отдельным следующим scope; эти14исправлений его не включают.

Подробные отчёты: email-report.md,backend-report.md,seo-report.md,storage-review.md. Исходный audit evidence manifest проверен: все71файлов неизменны. Runtime/test data/screenshots/logs остаются local ignored, не переносятся как обязательная часть Git.


Git publication2026-10-19: user explicitly authorized commit/push after LOCAL acceptance. The unchanged application snapshot is being published on codex/module09-transfer-2026-10-16-r1, based on75c6c18beb35f019a76e96543723448d8ed1cb7d. Runtime evidence, screenshots, databases and credentials remain local/ignored. This publication does not apply changes to production. Historical acceptance statements above describe the implementation boundary before this Git-only follow-up.
