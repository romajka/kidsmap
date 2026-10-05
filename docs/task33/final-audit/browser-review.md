# Итоговый браузерный аудит KidsMap №33

Роль: canonical browser-qa (`.agents/agents/browser-qa/agent.md`), исполнитель `/root/stage26_public`,2026-10-04. AUDIT ONLY dirty WORKTREE, production не использовался. Прежнее авторство backend этапа27 раскрыто: это самостоятельное выполнение браузерных сценариев, но не независимый source-review того backend. Применены Playwright/KidsMap UI/frontend-design/accessibility skills. **Аудит завершён, строгий браузерный gate FAIL:816 уникальных DOM-clean контекстов,1724/1724 data/DOM проверок,1 неожиданная ошибка перехода страницы.** Исторические PASS не перенесены. [Результаты](browser-results.json), [findings](browser-findings.json), [галерея](screenshots/index.json).

## 1. Состояние области

Новая основная матрица798 контекстов плюс18 дополнительных Program/Activity/Organization на одном финальном приложении V3 `r2-local-sha256-65d8995ff21fb5e5b9fb88d81d18f2f36c4380841f14131cd11dc258bf8c61b2`,2750 APP файлов. Языки AZ/RU/EN; ширины320/360/390/768/1024/1280/1440 (дополнительные390/1280). Каждый прогон имеет отдельную disposable PostgreSQL/cache/media/email среду, DJANGO_TESTING1, Unixsocket guard, no production credentials, external transports blocked/stubbed. All4 фактически выполненных APP manifests идентичны и совпадают с current WORKTREE (включая проверку новых файлов). Никакой R1 bounded equivalence не использован. MO скомпилированы из того же PO и явно исключены из source hash. Selected HTTP CSS/JS/adminCSS SHA совпали с frozen source. Curated27 actual synthetic PNG скопированы побайтно с SHA/provenance; длинные previews уменьшаются image viewer и не дают оснований утверждать прочтение каждой строки.

| Свежий финальный запуск | Контексты DOM-clean | Data/DOM проверки | Строгий gate |
|---|---:|---:|---|
| R1 `finalaudit-20261004-r1-clean` |357/357|367/367|PASS, wrapper exit0|
| Specialist `finalaudit-20261004-specialist` |168/168|380/380|PASS, wrapper exit0|
| Event `finalaudit-20261004-event` |273/273|931/931|PASS, wrapper exit0|
| Program/Activity/Org `finalaudit-20261004-targeted3` |18/18|46/46|FAIL, wrapper exit1:1pageerror|

Неожиданные failed requests/static errors0 во всех финальных семействах. Guards/cleanup PASS в каждом. Дополнительный bounded motion diagnostic —1 контекст/2 проверок данных PASS,2 pageerrors; это причинное воспроизведение, **не добавляется** к816/1724. [Подробности](browser-motion-results.json).

Первый свежий R1 браузер фактически завершил357/357 контекстов и367/367 проверок, но оболочка завершилась exit1 после матрицы: исполнитель изменил workspace-копию запускающего скрипта во время чтения bash. Сохранён `browser-attempts.json` с initial frozen wrapper SHA/actual immutable matrix SHA; полный смешанный текст оболочки UNKNOWN. Trap нормально очистил среду; manual collector — дополнительная сверка raw evidence, а не PASS invocation. Финальный R1 повторяется из immutable mirror; ошибочная попытка исключена из финальных чисел.

## 2. Сильные стороны

Фактически подтверждены конкретные пользовательские границы: видимость опубликованного текста отдельно от кандидата; права всей сети отдельно от выбранных филиалов; личные документы отдельно от публичных сертификатов; формат/состояние события отдельно от опубликованности; локальная группа/цена/расписание отдельно от общей программы. Реальные native POST, CSRF/stale и записанное состояние прошли. Карта не рисует точки для неизвестных координат. Полный месяц календаря и выбранный день совпадают с фильтрами/списком; архив хранит исходную географию; онлайн не получает выдуманную площадку. Baku/actual UTC и секунды/микросекунды owner/admin сохраняются корректно. Program owner candidate не меняет одобренный публичный текст до review; менеджер с place.edit получает404 на Program GET и POST с собственным валидным CSRF.

## 3. Реальные проблемы

Подтверждены5 P3, подробно в `browser-findings.json`: FA01 literal `None` вместо неизвестного стажа (21 public Specialist context); FA02 AZ success toast на RU dashboard после реального сохранения; FA03 clipping корректного текста «Найдено9 кружков» (текст172.625px, overflow:hidden parent134px на320/169px на390), **ошибка склонения не подтверждена**; FA04 вложенные2 visible main landmarks в6 Program contexts; FA05 uncaught native ViewTransition ошибка при Program POST400/302, данные корректны. Для FA05 source boundary — global navigation:auto в motion.css:143 и отсутствие scoped override в Program; точная внутренняя promise причина не объявляется доказанной. Бounded diagnostic воспроизвёл оба actual trigger с сохранённым правильным approved/candidate состоянием. Новых подтверждённых P0/P1/P2 в этой области нет.

Неудачные QA attempts сохранены: initialR1 mixed-shell-read (полный browser result, но wrapper failure, заменён clean repeat); targeted initial strict locator main matched2 (JSON не вернулся, counts0); targeted2 business checks18/46 PASS, но screenshot inspection выявила неполное подключение cached font в QA transport. Подключение только тестового /qa-font.ttf исправлено, добавлена meaningful font assertion и выполнен targeted3. Ошибки тестовых скриптов не выданы за application defect; failing native error в финальном правильном transport не скрыта.

## 4. Tech debt

Копируем проверенный CLI harness с явными актуальными fixture/path contracts. Approved display fixtures Program/Org/Activity создаются непосредственно в синтетической БД, что не выдаётся за полный UI-процесс публикации. Native owner Program edit/candidate isolation/scope выполняются отдельно. Автоматизация показывает first-control focus/Tab и конкретную навигацию, а не полный accessibility compliance.

## 5. Risks

Успешный выбранный браузерный сценарий не доказывает завершённость всех требований28 этапов и не закрывает debt полного backend suite. Root объединяет независимые domain/security/runtime результаты. Нативные пользовательские действия работают только с изолированными аккаунтами/данными. Реальный GoogleMaps/OAuth/CDN/SMTP в этот аудит не включён; local map fallback/API проверены отдельно от провайдера.

## 6. Dead/legacy candidates

Нет предложений удаления кода/моделей/БД на основании браузера. Текстовые legacy-артефакты будут перечислены как полировка, не dead-code evidence.

## 7. Tests gaps и сценарии

| Семейство | Сценарий для человека | Что реально проверяется | Граница |
|---|---|---|---|
| Родитель | Находит место и открывает карту | SSR каталог/деталь/map, карта open/close/API, canonical/hreflang/schema/privacy, overflow | Реальный внешний Maps SDK не проверен |
| Владелец | Редактирует самостоятельное место | Continuous sections, CSRF, рабочие controls, responsive/focus | Все варианты сложных прайсов не перебраны |
| Организация | Видит свои филиалы и участников | Selected/all-network ACL, будущий филиал, Tab до последнего таба | Native transfer/invite lifecycle отдельно у domain reviewer |
| Волонтёр/модератор | Работает с очередью и отзывами | Публикуемый head отдельно от pending, review controls, off-cohort503 без записей | Это не полная модерация каждого вида контента |
| Специалист | Подтверждает права, управляет сотрудничеством и документами | Claims/workspace/invitations/docs/ACL/private metadata и actual POST | Person richsnippet не требовался этапом25 |
| События | Выбирает месяц/день и фильтрует афишу | Полный месяц, day/list membership, native keyboard/mode/history/reload/range, zero states | Не все формы всех legacy событий |
| События | Сохраняет онлайн и опубликованное событие | Реальные owner/admin POST, точные секунды, Baku/actual UTC, CSRF/stale, organizer/venue/archives/reviews | Production/schema/data не затрагивались |
| Общая программа | Меняет общую часть для филиала | Native owner edit, impact confirmation, candidate-only/public isolation, stale409, independent program.manage | Initial approved content — display fixture, не full publication UI |
| Занятие/организация | Видит общие и местные сведения | Public detail translations/SEO, local supplement/group/schedule/price, hidden targets404 | Withdrawal/review propagation отдельно у domain reviewer |

Полный screenreader/контраст audit, physical devices, real integrations, exhaustive legacy content и production image/deploy — NOT_RUN. Скриншоты synthetic-only; длинные full-page PNG требуют zoom, выводы уточняются фактическим DOM.

## 8. Recommendations

Рекомендованы отдельные небольшие исправления пяти P3 после согласования реализации, включая проверку native Program400/302 при изменении motion. Все текущие APP изменения запрещены audit scope и не выполнялись. Общее «всё полностью готово» не подтверждается даже при успешных данных/DOM: strict browser FAIL и broader requirement-level/backend rollup root остаются самостоятельными ограничениями.

## 9. P0/P1/P2/P3

P0/P1/P2: новых подтверждённых в browser scope нет. P3:5 подтверждённых замечаний (FA01–05), без воспроизведённой потери данных/access bypass. Native error сохраняет строгий gate FAIL, severity не используется для превращения результата в PASS. Browser automation failures сохранены без сокрытия.

Executed commands: `wsl -u root -- bash /mnt/c/kidsmap/docs/task33/final-audit/qa/browser_sync.sh`; неизменяемый `/root/km28-browser/docs/task33/final-audit/qa/browser_run.sh` с указанными выше family/stamp; `motion finalaudit-20261004-motion` — отдельный diagnostic; workspace `browser_results_writer.py` и `browser_gallery.py` с4 final rawdirs (root/task33-evidence/browser28-*). Writers создают корректный FAIL artifact, их exit0 означает успешную запись отчёта, **не PASS браузера**. Final source comparison2750 exactMATCH, generated MO exception declared, own cleanup PASS. Named handoff: root kidsmap-orchestrator для итогового PARTIAL verdict/roadmap и HTML-report; domain reviewer получает точные row/check scopes. No APP/prod/Git/deploy changes.
