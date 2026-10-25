# Сохранённые черновики в кабинете

> Дополнение после нового снимка пользователя: первоначальная проверка не охватила `/account/profile/`, куда вёл пункт «Личный кабинет». Исправление фактического входа и проверка этой страницы описаны в [отдельном отчёте](2026-10-25-profile-entry-drafts-fix.md).

Дата: 2026-10-25. Один агент, согласованное локальное исправление по снимкам пользователя. `C:/kidsmap`, dirty WORKTREE, HEAD `3c1e383bd81d3cd0a26657ef3b79e768e2fc5858`. Production, deploy, push, пользовательские сохранения и чужие данные не изменялись. Web на `http://127.0.0.1:8898/` оставлен работающим.

## Воспроизведение и причина

Под `place_admin` через обычную форму сайта создан собственный неполный working draft, введены название и сайт, нажато «Сохранить черновик». Сохранение успешно; новая Place-запись не требуется.

- «Обзор» строился только по Place и не включал ServerDraft. Сохранённого названия в HTML не было.
- «Мои места» уже включали ServerDraft, но после всех опубликованных карточек. Тестовый черновик находился на `y=14437.89`, опубликованный список начинался на `y=495`. Вверху кнопка продолжения указывала на старую Place-запись.
- Верхний счётчик «Черновики и модерация» учитывал только Place и не включал новые рабочие копии.

Результаты до правки: [before/results.json](../../output/playwright/draft-visibility-20261025/before/results.json).

## Исправление

- В «Моих местах» блок «Сохранено для продолжения» перенесён перед опубликованными местами. Сохранены список, пагинация, даты, прогресс, ссылки продолжения и удаление собственных черновиков.
- В «Обзоре» показаны четыре последних сохранённых черновика, полный счётчик и ссылка «Все черновики».
- Ссылки используют UUID конкретной сохранённой рабочей копии, а не старую карточку места.
- Верхний счётчик черновиков учитывает рабочие копии. Общее число Place-записей не увеличивается автоматически.
- Выборка ограничена текущим actor, типом place, новой карточкой без target_id и отсутствием materialized_place. Чужие и уже преобразованные черновики не попадают в новый обзор. Существующие рабочие копии редактирования места остаются прикреплёнными к своим карточкам в «Моих местах».
- Общая сборка названия и URL вынесена в `services/place_working_drafts.py`, её использует и существующий список. Приоритет языка и сохранённые UUID сохранены.

Автоматических преобразований или переноса пользовательских данных нет. Ранее сохранённые рабочие черновики появляются через исправленную выборку и расположение блока.

## Проверки и срез

Codebase Memory `C-kidsmap`: поиск dashboard/ServerDraft, затем проверка реальных views/controllers/templates. Индекс 2026-10-16 устарел; динамические ORM/шаблонные связи проверены по исходникам.

После исправления manifest локального сервера содержит 1140 файлов. Относительно предыдущего UI-среза изменены controller owner_places, views, два шаблона кабинета, test_place_workflow_readiness и добавлен place_working_drafts.py. [Manifest до](../../output/playwright/draft-visibility-20261025/before/sources.json), [manifest после](../../output/playwright/draft-visibility-20261025/after/sources.json). Предыдущие широкие QA-прогоны не объявляются повторёнными на этом срезе.

| Проверка | Результат |
|---|---|
| Новые регрессии до исправления | RED: 4 теста, 4 failures и отсутствующий context key; owner/admin не видят сохранённые записи в обзоре, порядок списка неверен |
| Django целевой набор после исправления | 45 PASS, 27.867 s |
| Django финальный срез после уточнения языка | 17 PASS, 5.869 s; включены четыре новые регрессии и существующие проверки working drafts |
| Browser: admin через сайт | AZ/RU/EN × 390/768/1024/1280/1440 × обзор/мои места: 30 наблюдений PASS |
| Продолжение и повторное открытие | Сохранённые название и сайт восстановлены по ссылке из обзора и после reload |
| Privacy/совместимость | Тесты owner/admin, чужие/consumed исключены, пустое название сохраняет видимый черновик, newest four и total count, пагинация и старые ссылки продолжают работать |
| DB invariants | GET обзора не создаёт Place; схемы/миграций не добавлено |
| Django check / makemigrations --check --dry-run | No issues / No changes detected |
| Diff whitespace | PASS: git -c core.whitespace=cr-at-eol diff --check |

45 и 17 — пересекающиеся наборы, их нельзя складывать. Браузерные 30 наблюдений и один сценарий продолжения отражены в [after/results.json](../../output/playwright/draft-visibility-20261025/after/results.json). Нет pageerror или неожиданных локальных HTTP ≥400; 422 проверки неполных полей допустим. Горизонтальный overflow проверен во всех снимках.

Доказательства: [обзор на компьютере](../../output/playwright/draft-visibility-20261025/after/ru-1440-overview.png), [мои места на компьютере](../../output/playwright/draft-visibility-20261025/after/ru-1440-places.png), [обзор на телефоне](../../output/playwright/draft-visibility-20261025/after/ru-390-overview.png), [мои места на телефоне](../../output/playwright/draft-visibility-20261025/after/ru-390-places.png). Это локальные ignored browser-артефакты, они не копируются в versioned screenshots. Собственный именованный тестовый черновик удалён после проверки; остальные сохранения оставлены: [cleanup.json](../../output/playwright/draft-visibility-20261025/cleanup.json).

## Команды

```powershell
# Все Django-запуски: DJANGO_TESTING=1, cleared env, isolated PostgreSQL socket,
# отдельные cache/media/private-media/email; никаких production credentials.
wsl -d Ubuntu-24.04 -- bash /mnt/c/kidsmap/.tmp/owner-ui-feedback-20261025/draft-tests-start.sh
wsl -d Ubuntu-24.04 -- bash /mnt/c/kidsmap/.tmp/place-implementation-20261023/rerun.sh owner-ui-feedback-red draft-visibility-green catalog.testcases.test_place_workflow_readiness catalog.testcases.test_place_editor_preservation catalog.testcases.test_place_editor_preview catalog.testcases.test_place_staff_workflow
wsl -d Ubuntu-24.04 -- bash /mnt/c/kidsmap/.tmp/place-implementation-20261023/rerun.sh owner-ui-feedback-red draft-visibility-final catalog.testcases.test_place_workflow_readiness

$env:KIDSMAP_PLAYWRIGHT_MODULE='C:/Users/Ramin/AppData/Local/npm-cache/_npx/9833c18b2d85bc59/node_modules/playwright'
$env:KIDSMAP_BROWSER_EXECUTABLE='C:/Users/Ramin/AppData/Local/ms-playwright/chromium-1243/chrome-win64/chrome.exe'
node .tmp/owner-ui-feedback-20261025/draft_visibility.cjs before
node .tmp/owner-ui-feedback-20261025/draft_visibility.cjs after
node .tmp/owner-ui-feedback-20261025/draft-cleanup.cjs
wsl -d Ubuntu-24.04 -- bash /mnt/c/kidsmap/.tmp/owner-ui-feedback-20261025/check.sh
git -c core.whitespace=cr-at-eol diff --check
```

Логи: `.tmp/place-implementation-20261023/draft-visibility-{red,green,final}.log`. Fixture с доступами остаётся в ignored scratch; в отчёт не переносится. Собственный изолированный тестовый PostgreSQL остановлен; web и БД локального стенда работают.

Не запускались заново полные moderation/pricing/JSON/legacy E2E, Firefox/WebKit, физические устройства или production-проверки. Обычные Place-черновики по-прежнему отображаются в своём разделе; новый обзор предназначен для ещё не преобразованных рабочих копий новых мест.

Ручная проверка: [Обзор](http://127.0.0.1:8898/ru/account/), [Сохранено для продолжения](http://127.0.0.1:8898/ru/account/places/#owner-working-drafts-panel).
