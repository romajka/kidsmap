# JSON-инструкции админки перед выпуском

2026-10-25. Один агент, согласованные локальные проверки и исправления. `C:/kidsmap`, dirty WORKTREE, HEAD `3c1e383bd81d3cd0a26657ef3b79e768e2fc5858`. Production, deploy и push не затрагивались. Сервер `http://127.0.0.1:8898/` оставлен работающим.

**Итог:** поддерживаемые поля инструкции проверены через настоящий импорт и сохранение. Найденные расхождения исправлены. JSON заполняет форму; явное сохранение, фотографии, проверка неизвестных фактов и модерация остаются отдельными действиями.

## Исправлено

1. В инструкции «Обновить по экспорту» было написано, что пустой текст пропускается. Реализация очищает такое поле. Текст исправлен: omitted/null сохраняют значение, явная пустая строка очищает текст; неизвестные сведения нельзя обозначать пустыми строками в обновлении.
2. Плашки `custom_price_badge_az/ru/en` попадали в JSON и сохранённый candidate, но в форме редактирования возвращались пустыми. Причина: поля объявлены в форме, но отсутствовали в edit fieldsets, поэтому не получали initial. Добавлены в add/edit fieldsets. Теперь повторное открытие и следующее сохранение не стирают их.
3. `lesson_format`, `lessons_per_week`, `lessons_per_month` были заявлены в JSON, но отсутствовали в админской форме. Теперь входят в add/edit fieldsets и отображаются в «Особенностях места». Общие параметры места и параметры отдельного тарифа остаются независимыми.
4. Неизвестные ключи внутри тарифов отбрасывались при нормализации с HTTP200 и без предупреждения. Теперь импорт отклоняется до изменения формы, с путём ошибочного поля. Проверены прямые и вложенные групповые тарифы; ошибки доступны на RU/AZ/EN. Поддерживаемые старые алиасы и служебные поля экспорта не запрещены.
5. К примерам добавлены цена «от», курс с рассрочкой, обязательная допуслуга и регистрационный взнос. Всего 16 примеров. Уточнены дополнительные поля тарифа и предел 12 строк в одной карточке.
6. Уточнено, что `editor_review` — временный отчёт редактору, а не сохраняемые поля Place. Исходный JSON/REPORT.txt нужно сохранить отдельно. Обновлена версия JS в admin/volunteer templates для сброса старого asset cache.

Изменены domain_admin/place.py, services/pricing_plans.py, section_pricing.html, два подключения importer JS, сам importer, JS-регрессии и JSON contract; добавлен test_admin_json_instruction_fields.py. Модели и миграции в этой задаче не изменялись.

## Какие пункты заполняются

Из настоящего диалога «Собрать JSON» извлечена структура с **51 верхнеуровневым ключом**. Она проверялась импортом собственных синтетических данных в новой карточке, native save и повторным открытием.

| Область | Фактический результат |
|---|---|
| 45 обычных полей | Значения перенесены и сохранены: названия/описания AZ/RU/EN, категории, возраст, контакты, ссылки, адрес/координаты, примечания, общие параметры занятий, плашки цены и прочие тексты |
| pricing_plans | Отдельная проверка всех нормализованных полей, 16 примеров, сложного набора и полного export/import |
| schedule_days | Полная неделя: пять дней 10:00–18:00, суббота 24/7, воскресенье закрыто; сохранение, экспорт и повторный импорт подтверждены |
| is_temporary | Тип постоянной карточки задан выбранным workflow, не переключается этим JSON-флагом |
| temporary_start/temporary_end | В постоянной карточке проверялись как unknown/null; временные карточки этим прогоном не проверялись |
| editor_review | Отображается как вспомогательная проверка; не становится полями карточки |
| Фотографии | JSON не загружает изображения. Два файла загружены настоящим picker отдельно; на опубликованной карточке доступны HTTP200 |
| Направления/группы | Через nested_pricing v2 для уже созданной карточки: тексты, язык, возраст, расписание, преподаватель, условия и тарифы сохранены; export/import сохраняет структуру и IDs |
| Публикация/проверенность/владелец | Управляются соответствующими действиями и правами, не назначаются автоматически новым JSON |

Телефоны сравнивались по цифрам: форматирование `+994 50 …` после открытия не является потерей номера. `public_links` сравнивались как JSON-объекты, независимо от пробелов и порядка ключей.

## Тарифы

- **16/16 примеров** текущей инструкции реально импортированы, сохранены и повторно открыты. Сравнивались все нормализованные поля, а не только сумма или уведомление.
- **13 типов продукта**, **14 единиц количества**, **4 периода регулярной оплаты** взяты из действующего backend contract и прошли JSON → native save → reopen. Положительный batch из 12 тарифов сохраняется; 13 строк отклоняются.
- Все **4 режима цены места** прошли JSON-переключение/сохранение с сохранением скрытых тарифов.
- Сложный набор: диапазон 100–150 USD, каждые 2 недели, 7 посещений, срок использования 3 месяца, календарные даты предложения, семейная аудитория, возраст/число участников, дни недели, AZ/RU/EN условия и названия, источник; курс 900 AZN с 3 платежами; обязательные материалы 15 AZN; неактивный тариф. Все переданные параметры сохранены без пересчёта валют, количества, периода или деления общей цены курса.
- Проверены вложенная группа и тариф 90 AZN / 7 занятий / каждые 2 недели. После одобрения полный export v2 → import → save → reopen сохранил IDs и значения прямых/вложенных тарифов, расписания и обычных полей.
- Своя карточка реально одобрена. Анонимные public detail/catalog проверены; публичные суммы/условия прямых и группового тарифов проверены на RU/AZ/EN при 390 и 1440. Неактивный тариф не показывается.
- Девять отрицательных случаев: неизвестное поле, рассрочка без числа платежей, recurring без периода, перевёрнутый диапазон, нулевое количество, неподдерживаемый product_type, объект вместо списка, 13 строк, неверный телефон. HTTP400, название и исходные тарифы остаются неизменными.

## Доказательства и версии

До исправления: 4 Django-теста дали 8 failures (поля/initial и неизвестные ключи); отдельная языковая регрессия дала 2 failures для AZ/EN. JS-регрессии подтвердили противоречие инструкции и отсутствие нужных примеров.

После исправления:

- Django **43 PASS**, 11.509 s: новые регрессии, JSON editor/export/scope, legacy export, сохранность редактора, volunteer instruction и relational pricing.
- Node/DOM **37 PASS, 0 FAIL, 0 SKIP**, 4.019 s. Использованы реальные jQuery/Select2. Первоначальный запуск без их путей имел один dependency skip; финальный набор — без пропусков.
- Admin layouts AZ/RU/EN × 390/1440: новые поля видны, нет horizontal overflow/pageerror.
- Django check: no issues; makemigrations check/dry-run: no changes detected; git diff whitespace: PASS.

Срез **A**: 1142 source hashes; [основные примеры](../../output/playwright/admin-json-release-20261025/final/results.json), [полная матрица полей](../../output/playwright/admin-json-release-20261025/final/root-field-matrix.json), [34 результата продолжения](../../output/playwright/admin-json-release-20261025/followup/results.json), [manifest A](../../output/playwright/admin-json-release-20261025/followup/sources.json). На этом срезе выполнены примеры, все типы/единицы, группы, layouts и публикация.

Срез **B**: та же структура 1142 файлов; после A изменены только локализация сообщения неизвестного tariff field в pricing_plans.py и её регрессия. Финальные 43 Django-теста и [6 завершающих browser результатов](../../output/playwright/admin-json-release-20261025/final-check/results.json) относятся к B: реальные ошибки RU/AZ/EN, импорт уже одобренного v2 export с проверкой IDs и полей, удаление собственного старого probe, сохранение сложной QA-карточки для просмотра. [Manifest B](../../output/playwright/admin-json-release-20261025/final-check/sources.json). В конце повторно сверены все 1142 хеша stand/disk, delta пустой.

В основном browser-файле после 16 успешных примеров есть FAIL дополнительного сравнения `verified_at:null`: pipeline намеренно не переносит пустую отметку staff-проверки. Это ошибка harness-сравнения, не потеря пользовательского тарифного поля. Для вложенных данных поправлено сравнение только этого пустого служебного значения; affected nested/export/approval сценарии затем прошли в followup и final-check. Первоначальные phone/JSON whitespace различия также проверены семантически; плашки и отсутствующие поля, в отличие от них, были подтверждёнными defects и исправлены.

Все наборы пересекаются с прежним полным QA. Не складывать их как уникальные тесты. Не каждый из 16 примеров публиковался отдельно: публично проверен сложный комбинированный набор и группа.

Снимки: [новые поля на телефоне](../../output/playwright/admin-json-release-20261025/followup/admin-ru-390.png), [тарифы публично](../../output/playwright/admin-json-release-20261025/followup/public-ru-1440.png), [тарифы публично на телефоне](../../output/playwright/admin-json-release-20261025/followup/public-ru-390.png). Captured prompts: [search](../../output/playwright/admin-json-release-20261025/final/prompt-search.txt), [JSON](../../output/playwright/admin-json-release-20261025/final/prompt-json.txt), [update](../../output/playwright/admin-json-release-20261025/final/prompt-update.txt).

## Команды

```powershell
wsl -d Ubuntu-24.04 -- bash /mnt/c/kidsmap/.tmp/admin-json-release-20261025/start-tests.sh
wsl -d Ubuntu-24.04 -- bash /mnt/c/kidsmap/.tmp/place-implementation-20261023/rerun.sh owner-ui-feedback-red admin-json-instructions-final catalog.testcases.test_admin_json_instruction_fields catalog.testcases.test_place_json_editor_roundtrip catalog.testcases.test_place_legacy_json_export catalog.testcases.test_place_json_scope catalog.testcases.test_place_editor_preservation catalog.testcases.test_volunteer_json_prompt catalog.testcases.pricing_plans_relational

$env:NODE_PATH='C:/kidsmap/.tmp/phone-dom/node_modules'
$env:KIDSMAP_JSDOM='C:/kidsmap/.tmp/phone-dom/node_modules/jsdom'
$env:KIDSMAP_JQUERY='C:/kidsmap/staticfiles/admin/js/vendor/jquery/jquery.js'
$env:KIDSMAP_SELECT2='C:/kidsmap/staticfiles/admin/js/vendor/select2/select2.full.js'
node --test scripts/tests/place_json_prompts.test.cjs scripts/tests/place_json_patch.test.cjs scripts/tests/place_pricing_editor.test.cjs scripts/tests/place_pricing_compatibility.test.cjs

$env:KIDSMAP_PLAYWRIGHT_MODULE='C:/Users/Ramin/AppData/Local/npm-cache/_npx/9833c18b2d85bc59/node_modules/playwright'
$env:KIDSMAP_BROWSER_EXECUTABLE='C:/Users/Ramin/AppData/Local/ms-playwright/chromium-1243/chrome-win64/chrome.exe'
node .tmp/admin-json-release-20261025/audit.cjs final
node .tmp/admin-json-release-20261025/followup.cjs
node .tmp/admin-json-release-20261025/final-check.cjs
wsl -d Ubuntu-24.04 -- bash /mnt/c/kidsmap/.tmp/owner-ui-feedback-20261025/check.sh
git -c core.whitespace=cr-at-eol diff --check
node .tmp/place-full-cycle-20261025/final_snapshot.cjs admin-json-localized admin-json-verified
```

Django: DJANGO_TESTING=1, cleared environment, собственный PostgreSQL socket без network DB, изолированные cache/media/private-media/email. Логи `.tmp/place-implementation-20261023/admin-json-instructions-{red,green,green2,final}.log`, `.tmp/admin-json-release-20261025/{prompts-red,node-final,browser-final,browser-followup,browser-final-check}.log`. Доступы и fixtures с паролями остаются в ignored scratch. Собственный test PostgreSQL остановлен; web и БД стенда работают.

Codebase Memory применён как навигация; индекс 2026-10-16 устарел. Динамические Django/form/JS связи, новые helpers и validators сверены с актуальными исходниками. Не выполнялась внешняя генерация ответов ChatGPT или проверка достоверности реальных исследуемых мест: проверены текст инструкций, их примеры и применение приложением.

## Для ручной проверки

- [Добавить место и открыть JSON-инструкции](http://127.0.0.1:8898/admin/catalog/place/add/?type=permanent).
- [Сложная локальная QA-карточка в админке](http://127.0.0.1:8898/admin/catalog/place/353/change/).
- [Та же карточка публично](http://127.0.0.1:8898/ru/place/353-place-e2e-admin-ru-1792939416196/).

Первый собственный probe 352 удалён; 353 оставлен специально для просмотра. Чужие сохранения и неоднозначные legacy-данные не преобразовывались. Это закрывает локальную JSON-проверку; отдельные production release gates из [оценки готовности](2026-10-25-public-release-readiness.md) остаются непроверенными. Полный продуктовый набор, Firefox/WebKit, физические устройства и Google Maps не запускались заново.
