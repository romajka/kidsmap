# Черновики на фактической странице входа в кабинет

Дата: 2026-10-25. Один агент, согласованное локальное исправление. `C:/kidsmap`, dirty WORKTREE, HEAD `3c1e383bd81d3cd0a26657ef3b79e768e2fc5858`. Production/deploy/push не затрагивались, чужие сохранения не изменялись, локальный сервер 8898 оставлен работающим.

## Почему предыдущего исправления оказалось недостаточно

Предыдущая проверка охватывала `/account/` и `/account/places/`. На новом снимке пользователя показана `/account/profile/`: «Данные профиля» и полный список Place. Именно туда вели пункты «Личный кабинет» в desktop header и мобильном меню. Хотя в sidebar подсвечивался «Обзор», это другой view и шаблон, в которых ServerDraft не передавались и не отображались.

Это подтверждено исходниками header.html, AccountProfileView._build_context, account_profile.html и реальным нажатием пункта меню. Браузер до правки перешёл на `/ru/account/profile/`; собственный сохранённый черновик там отсутствовал.

Codebase Memory `C-kidsmap` использован для поиска AccountProfileView/AccountDashboardView; известный устаревший индекс 2026-10-16 не принят за текущий исходник. View/template/header связи проверены непосредственно в рабочем дереве.

## Исправление

- Пункт «Личный кабинет» на компьютере и телефоне ведёт на обзор `/account/`.
- Старые ссылки `/account/profile/` также показывают «Сохранено для продолжения», первым блоком над данными профиля. Пользовательские сохранения не требуют переноса.
- Блок вынесен в общий account_working_drafts.html; его используют обзор и профиль. Выборка остаётся actor-private, с исключением чужих и уже преобразованных рабочих копий.
- Настройки и формы изменения профиля продолжают работать; блок добавлен в readonly профиль, а не в настройки.

## Проверка

| Проверка | Результат |
|---|---|
| До исправления: 2 новые Django-регрессии | RED, 3 failures: owner/admin не видят черновики на profile |
| После исправления: workflow readiness + профиль | 30 PASS, 8.237 s |
| Прямой profile URL | AZ/RU/EN × 390/768/1024/1280/1440: 15 сочетаний PASS, без horizontal overflow |
| Реальный desktop пункт «Личный кабинет» | До → profile; после → account overview с сохранённым черновиком |
| Реальный mobile пункт «Личный кабинет» | Account overview с сохранённым черновиком, PASS |
| Продолжение с profile | Сохранённые название и сайт восстановлены, повторный reload сохраняет значения |
| Privacy | Django-регрессии исключают foreign/consumed; owner/admin проверены |
| Profile settings | Набор TestAccountProfileUpdates прошёл вместе с readiness-тестами |
| Django check / migration check | No issues / No changes detected |
| Diff whitespace | PASS с core.whitespace=cr-at-eol |

Браузер: [before/results.json](../../output/playwright/profile-drafts-20261025/before/results.json), [after/results.json](../../output/playwright/profile-drafts-20261025/after/results.json), [mobile entry и cleanup](../../output/playwright/profile-drafts-20261025/finish.json). После проверки удалён только собственный именованный тестовый черновик; на profile повторно подтверждена видимость остальных сохранений.

Снимки: [desktop profile](../../output/playwright/profile-drafts-20261025/after/ru-1440-profile.png), [mobile profile](../../output/playwright/profile-drafts-20261025/after/ru-390-profile.png), [mobile menu arrival](../../output/playwright/profile-drafts-20261025/mobile-menu-arrival.png). Артефакты остаются в ignored output, не копируются в versioned screenshots.

Срез после исправления: 1141 source hashes. Относительно предыдущего verified draft-visibility среза изменены header.html, account_dashboard.html, account_profile.html, views.py, test_place_workflow_readiness.py и добавлен account_working_drafts.html. [Manifest](../../output/playwright/profile-drafts-20261025/after/sources.json). Предыдущие широкие E2E не выдаются за повторённые на этом срезе.

## Команды

```powershell
# Isolated PostgreSQL/socket, DJANGO_TESTING=1, cleared env, отдельные cache/media/email.
wsl -d Ubuntu-24.04 -- bash /mnt/c/kidsmap/.tmp/owner-ui-feedback-20261025/profile-tests-start.sh
wsl -d Ubuntu-24.04 -- bash /mnt/c/kidsmap/.tmp/place-implementation-20261023/rerun.sh owner-ui-feedback-red profile-drafts-green catalog.testcases.test_place_workflow_readiness catalog.testcases.auth_flow.TestAccountProfileUpdates

$env:KIDSMAP_PLAYWRIGHT_MODULE='C:/Users/Ramin/AppData/Local/npm-cache/_npx/9833c18b2d85bc59/node_modules/playwright'
$env:KIDSMAP_BROWSER_EXECUTABLE='C:/Users/Ramin/AppData/Local/ms-playwright/chromium-1243/chrome-win64/chrome.exe'
node .tmp/owner-ui-feedback-20261025/profile-entry.cjs before
node .tmp/owner-ui-feedback-20261025/profile-entry.cjs after
node .tmp/owner-ui-feedback-20261025/profile-finish.cjs
wsl -d Ubuntu-24.04 -- bash /mnt/c/kidsmap/.tmp/owner-ui-feedback-20261025/check.sh
git -c core.whitespace=cr-at-eol diff --check
```

Логи: `.tmp/place-implementation-20261023/profile-drafts-{red,green}.log`. Доступы в отчёт не переносились. Изолированный тестовый PostgreSQL остановлен; сервер и БД стенда продолжают работать. Физические устройства, Firefox/WebKit, production и полный набор остальных product E2E не проверялись.

Для пользователя: [страница со снимка](http://127.0.0.1:8898/ru/account/profile/#account-working-drafts), [обзор кабинета](http://127.0.0.1:8898/ru/account/).
