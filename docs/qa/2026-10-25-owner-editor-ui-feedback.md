# Форма места: мишка, отступы и выбор расписания

Дата: 2026-10-25. Один агент, согласованные локальные исправления по двум снимкам пользователя. `C:/kidsmap`, dirty WORKTREE, HEAD `3c1e383bd81d3cd0a26657ef3b79e768e2fc5858`. Существующие изменения сохранены; production, deploy, push и чужие данные не затрагивались. Локальный QA-сервер `http://127.0.0.1:8898/` оставлен работающим.

## Что изменено

- Из формы владельца убран боковой помощник Маппи вместе с подписью и загрузкой его JS. Изображения и код помощника оставлены для возможного возвращения; логотип сайта сохранён.
- Увеличены промежутки между подписями, полями и подсказками. В расписании исправлено наложение подписи на select: измеренный промежуток был −1 px, стал 7 px. Между пояснением и подписью теперь 20 px вместо 6 px.
- В новой форме владельца тип расписания пустой: «Выберите тип расписания» / «Cədvəl növünü seçin» / «Choose a schedule type». До выбора скрыты дни, примечания и описание режима.
- Ошибка `structured_schedule` раньше попадала в первый видимый control скрытого поля — select типа. Теперь при выбранном типе ошибка направляется в отдельное доступное сообщение расписания. Пустой тип при явной проверке по-прежнему указывает на select. После исправления часов сообщение снимается.
- Сохранённые значения и явно переданный initial не сбрасываются. Совместимость старых POST без нового поля сохранена; модель и миграции не менялись.

## Срезы и Codebase Memory

Граф `C-kidsmap` использован для поиска классов форм; индекс 2026-10-16 устарел, 120 файлов с частичным разбором, 0 skipped. Фактические формы, шаблоны и динамический JS сверены с текущими исходниками.

Снимки браузера: [до](../../output/playwright/owner-ui-feedback-20261025/before/sources.json), [после](../../output/playwright/owner-ui-feedback-20261025/after/sources.json). После рестарта проверено совпадение всех 1139 хешей stand/disk. Относительно Final4 предыдущего полного аудита изменены восемь файлов в manifest: forms.py; общий шаблон расписания; owner_place_continuous.html; permanent_place_form.html; test_place_workflow_readiness.py; owner_place_continuous.css; kidsmap_editor_ux.js; kidsmap_schedule_editor.js. Дополнены JS-регрессии editor_live_validation.test.cjs, которые не входят в manifest сервера.

Предыдущие широкие браузерные прогоны относятся к своим прежним срезам. На этом срезе проведены перечисленные ниже целевые проверки, а не повтор всего полного аудита.

## Проверки

| Проверка | Результат |
|---|---|
| Исходная проблема в Chromium | Воспроизведена: regular выбран автоматически, aria-invalid=true, мишка присутствует, подпись накладывается на select |
| Новые Django-регрессии до исправления | RED: 2 теста, 3 failures для RU/AZ/EN из-за default regular |
| JS-регрессия до исправления | RED: ошибка часов красила выбранный тип |
| Django после исправления | 41 PASS, 27.728 s |
| Node/DOM после исправления | 104 PASS, 0 FAIL, 0 SKIP; 10.228 s; включает целевые 20 тестов live validation/schedule |
| Owner AZ/RU/EN × 390/768/1024/1280/1440 | 15 сочетаний PASS: placeholder, отсутствие помощника, панели до выбора, нейтральный выбранный тип, отступы, отсутствие горизонтального overflow |
| Дополнительные браузерные проверки | 7 результатов PASS: явная проверка указывает на часы; исправление часов снимает ошибку; сохранение и повторное открытие working draft сохраняют режим и часы; именованный собственный черновик удалён; admin/volunteer × 390/1440 без ложной красной рамки |
| Console/network | В матрице нет pageerror и неожиданных HTTP ≥400; 422 проверки неполной формы — ожидаемый результат |
| Django check / migration check | No issues / No changes detected |
| git diff --check | PASS с core.whitespace=cr-at-eol |

104 Node-теста включают 20 целевых: эти числа не складываются. Семь дополнительных браузерных результатов не обозначают семь независимых полных E2E.

Браузерная матрица: [results.json](../../output/playwright/owner-ui-feedback-20261025/after/results.json). Дополнительные проверки: [results.json](../../output/playwright/owner-ui-feedback-20261025/acceptance/results.json).

Снимки: [исходная ошибка](../../output/playwright/owner-ui-feedback-20261025/before/ru-1440-weekly.png), [пустой выбор](../../output/playwright/owner-ui-feedback-20261025/after/ru-1440-initial.png), [недельный режим](../../output/playwright/owner-ui-feedback-20261025/after/ru-1440-weekly.png), [верх формы без помощника](../../output/playwright/owner-ui-feedback-20261025/acceptance/owner-about-desktop.png), [мобильная форма](../../output/playwright/owner-ui-feedback-20261025/acceptance/owner-about-mobile.png).

## Команды

```powershell
# RED, выделенный PostgreSQL без сети и с отдельным socket.
wsl -d Ubuntu-24.04 -- bash /mnt/c/kidsmap/.tmp/place-implementation-20261023/quality.sh owner-ui-feedback-red catalog.testcases.test_place_workflow_readiness.PlaceWorkflowReadinessTests.test_new_owner_schedule_starts_with_localized_empty_choice catalog.testcases.test_place_workflow_readiness.PlaceWorkflowReadinessTests.test_saved_and_explicit_owner_schedule_choices_are_preserved

# GREEN: DJANGO_TESTING=1, очищенное окружение, isolated DB/cache/media/email.
wsl -d Ubuntu-24.04 -- bash /mnt/c/kidsmap/.tmp/place-implementation-20261023/rerun.sh owner-ui-feedback-red owner-ui-feedback-green catalog.testcases.test_place_workflow_readiness catalog.testcases.test_place_editor_preservation catalog.testcases.test_place_editor_preview catalog.testcases.test_place_staff_workflow

$env:KIDSMAP_JSDOM='C:/kidsmap/.tmp/phone-dom/node_modules/jsdom'
node --test scripts/tests/editor_ux.test.cjs scripts/tests/editor_feedback.test.cjs scripts/tests/editor_live_validation.test.cjs scripts/tests/editor_preview_return.test.cjs scripts/tests/owner_workflow.test.cjs scripts/tests/owner_mappy.test.cjs scripts/tests/schedule_confirm.test.cjs

$env:KIDSMAP_PLAYWRIGHT_MODULE='C:/Users/Ramin/AppData/Local/npm-cache/_npx/9833c18b2d85bc59/node_modules/playwright'
$env:KIDSMAP_BROWSER_EXECUTABLE='C:/Users/Ramin/AppData/Local/ms-playwright/chromium-1243/chrome-win64/chrome.exe'
node .tmp/owner-ui-feedback-20261025/browser.cjs before
node .tmp/owner-ui-feedback-20261025/browser.cjs after
node .tmp/owner-ui-feedback-20261025/acceptance.cjs
wsl -d Ubuntu-24.04 -- bash /mnt/c/kidsmap/.tmp/owner-ui-feedback-20261025/check.sh
git -c core.whitespace=cr-at-eol diff --check
```

Логи остаются локально: `.tmp/place-implementation-20261023/owner-ui-feedback-{red,green}.log`, `.tmp/owner-ui-feedback-20261025/node-suite.log`. Fixture с доступами остаётся в ignored scratch, в отчёт не копируется. Собственный тестовый PostgreSQL остановлен; web и DB локального стенда работают.

Технические поправки harness: ожидаемый preview422 исключён из неожиданных network ошибок. Первая дополнительная проверка ошибочно ожидала обязательную валидацию от кнопки предпросмотра; приложение допускает предпросмотр неполной формы. Правильная кнопка «Проверить заполнение» проверена повторно успешно. Старт браузера во время рестарта web получил закрытое соединение; после готовности и сверки manifest прогон повторён.

## Границы

Пустой default изменён для новой формы владельца; сохранённые места и defaults staff-форм не переопределялись. Не проверялись production, физические устройства, Firefox/WebKit и Google Maps. Полные pricing/moderation/legacy/JSON E2E после этой небольшой правки не повторялись; актуальные целевые регрессии перечислены выше.

Для ручной проверки: [новая форма](http://127.0.0.1:8898/ru/account/places/create/?type=permanent&fresh=1), [кабинет](http://127.0.0.1:8898/ru/account/places/).
