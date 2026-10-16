# ORG-QA-03 — конкретный план исправления

Статус PLAN READY / IMPLEMENTATION NOT RUN. Checkout `/home/ramin/kidsmap`, branch `task33-progress`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, dirty WORKTREE, active_run NONE. Scope только ORG-QA-03. Основание: свежий `recheck.result.json`, source и временная браузерная проверка `layout-probe.result.json` и уточнённая `layout-probe-refined.result.json` (QA addStyleTag, не application patch).

## Причина и точные файлы

`static/admin/css/pages/kidsmap_changelist.css`, `.km-toolbar #changelist-search.km-search-form`: принудительный nowrap в базовом правиле; wrap только при viewport <=900, хотя sidebar на1024 оставляет форме630px. Изменить базовое правило на `flex-wrap: wrap !important`, обновить его комментарий. В существующее `.km-toolbar-right` добавить `flex-wrap: wrap` и `max-width: 100%`, чтобы группа sort/columns при sidebar на768 не превышала форму. Существующие размеры/порядок/buttons/theme и локальный scroll таблицы сохранить. Не вводить global overflow:hidden, не менять templates/JS/services, ownership/connections или Place правки первого модуля.

Разрешённые deliverables: этот CSS, новые QA scripts/results/REPORT/PNG в собственном `docs/qa/org-qa03-fix-2026-10-13-r1/` (либо следующий уникальный rN), current status ORG-QA-03 в guide. Другие application файлы не входят.

## Выполнение и проверки

1. Зафиксировать входные hashes, active_run и чужие changes/процессы. Новый собственный профиль с DJANGO_TESTING=1, уникальными loopback PostgreSQL/DB/cache/media/email/cookies; fresh locales и sole LOCALE_PATHS. Не использовать .env/production.
2. Сохранить RED: нынешний исходник и реальные PNG/geometry на1024 RU/AZ/EN; overflow +194/+122/+109px. Текущий probe отдельно от принятия patch.
3. Выполнить только указанные два CSS-правила.
4. Реальный browser RU/AZ/EN ×360/390/768/1024/1280/1440 ×sidebar open/closed: document не шире viewport, все search/filter/sort/columns controls доступны, локальный table scroll сохраняется. Проверить Enter search, клавиатурный выбор fictional карточек, переход к connection preview и cancel без mutation. Проверить shared consumers search panel (Place, Event, Specialist PlaceOwnershipRequest и PlaceReview (пять фактических includes)) в affected width/language scope, не делать полный проектный прогон.
5. Visible keyboard focus, dropdown/filter состояния, console/network, PNG manifest; source/runtime hashes и git diff --check. CSS-only fix не требует тестов, повторяющих implementation.
6. REPORT закрывает только ORG-QA-03 при фактическом acceptance, иначе OPEN. После ORG-QA-04 выполнить одну полную ACCEPT-02. Commit/push/deploy/production не разрешены.
