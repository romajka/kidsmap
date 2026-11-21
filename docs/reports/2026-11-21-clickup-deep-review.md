# KidsMap. Повторная приёмка колонки «Проверка»

21 ноября 2026 года в личной сессии ClickUp сверены 14 карточек. Тестировалась локальная рабочая копия на базе `5bb9af5f`. PostgreSQL, браузерные БД, медиа, почта и аккаунты изолированы. Публичные страницы использованы для сверки карточек. Операции сохранения и модерации выполнялись на тестовых данных.

## Что требует действия

1. **№51 — дефект времени в редакторе.** В тарифе с источником подтверждение сохранено в 08:30 UTC. В Chromium с часовым поясом Баку поле показывает 08:30, хотя должно показывать 12:30. Воспроизводится на AZ, RU и EN. Редактор отрезает суффикс часового пояса в двух местах. Исправить преобразование для отображения и проверить сохранение того же момента после повторного открытия. В том же прогоне предупреждение корректно сохранилось при одном подтверждённом и одном неподтверждённом тарифе. [Две ветки отрисовки поля](../../static/js/kidsmap_pricing_editor.js#L392)
2. **№73 — приёмка действующей версии.** Локально проверены парк без телефона, отдельный контакт администрации и исключение старого номера. В публичной версии у парка «Гянджлик» найдено действие звонка и WhatsApp. Его номер в этом проходе не раскрывался. Предыдущая сверка зафиксировала устаревший номер в трёх карточках. Все три нужно повторно проверить на версии с исправлением. [Парк «Гянджлик»](https://kidsmap.az/ru/place/205-park-gyandzhlik/) · [Исходная сверка контактов](2026-11-21-task-73-park-contacts.md)
3. **№75 — приёмка на четырёх исходных записях.** У реальных карточек №29, 30, 31 и 33 совпадает адрес Eldar Tağızadə küçəsi 30B. На тестовых данных проверена справочная связь для четырёх аналогичных записей без владельца и защита от передачи прав. Фактическое сохранение привязок этих четырёх записей в рабочем каталоге требует отдельной приёмки. [№29](https://kidsmap.az/ru/place/29-ami-inkisaf-merkezi-prodlenka-i-pomosh-s-domashnimi-zadaniya/) · [№30](https://kidsmap.az/ru/place/30-ami-inkisaf-merkezi-risovanie/) · [№31](https://kidsmap.az/ru/place/31-ami-inkisaf-merkezi-detskaya-gimnastika/) · [№33](https://kidsmap.az/ru/place/33-ami-inkisaf-merkezi-detskie-tancy/)

## По каждой карточке

| Карточка | Проверенные сценарии | Итог |
|---|---|---|
| [№26 · Подтверждение отзыва](https://app.clickup.com/t/1100350000001549/z8rcte3q4d) | Отправка отзыва и сообщение о модерации на AZ/RU/EN. Гость не видит отправленный на модерацию текст. | Прошло. |
| [№33 · Одно место, много направлений](https://app.clickup.com/t/1100350000001549/z8rcte3q4r) | Поиск по направлениям, возрастам и тарифам, публичная карточка и карта. Место не дублируется в выдаче. | Прошло. Проверка структуры на тестовых данных. |
| [№34 · Официальные ответы](https://app.clickup.com/t/1100350000001549/z8rcte3q4t) | На ширине 390 px владелец отправил ответ, обычный пользователь увидел его с отметкой представителя, формы ответа у обычного пользователя нет. Модератор скрыл и восстановил ответ, исходный отзыв остался видим. PostgreSQL также проверил повторную отправку, конкурентность и модерацию. | Прошло для согласованного формата. Возможны несколько отдельных официальных ответов. |
| [№48 · Сроки модерации](https://app.clickup.com/t/1100350000001549/z8rcte5avp) | Очереди мест и отзывов, смена сроков, фильтры, история, предупреждения, сроки в часовом поясе Баку и переход по счётчикам. | Прошло. 90 браузерных сочетаний и 3 граничных сценария. |
| [№49 · Апелляции](https://app.clickup.com/t/1100350000001549/z8rcte5awd) | Подача, проверка прав и версий, повторный запрос, независимый пересмотр и уведомление. Пересмотр не публикует исходный материал автоматически. | Прошло. |
| [№49 · Короткая карточка](https://app.clickup.com/t/1100350000001549/z8rcte5axc) | В ClickUp помечена как дубль основной апелляции. | Принимается вместе с основной. |
| [№51 · Примечания к ценам](https://app.clickup.com/t/1100350000001549/z8rcte5c5y) | Редактирование и очистка текста, предупреждение при неполном подтверждении, права и сброс подтверждения при изменении тарифа. Дополнительная проверка времени в форме. | **Исправить отображение времени подтверждения.** |
| [№52 · Вёрстка редактора](https://app.clickup.com/t/1100350000001549/z8rcte5c5z) | Существующее место, открытые секции и расширенные поля тарифа. AZ/RU/EN и 8 ширин от 390 до 1920 px, включая границу 1536 px. Контроль таблицы расписания, общей прокрутки и высоты правой панели. | Прошло во всех 24 сочетаниях в пределах этой проверки. |
| [№54 · Синхронизация редакторов](https://app.clickup.com/t/1100350000001549/z8rcte7n3r) | Волонтёр и администратор открыли один черновик. Оба увидели возраст 1–6 и готовность 12/12. Пройдены серверные проверки версий. | Прошло. |
| [№73 · Парки и контакты](https://app.clickup.com/t/1100350000001549/z8rctexru6) | 24 публичных сценария и 6 проверок форм, включая пустой телефон, телефон администрации и скрытие старого номера. | Прошло локально. Осталась сверка трёх опубликованных карточек после выкладки исправления. |
| [№74 · Фильтры админки](https://app.clickup.com/t/1100350000001549/z8rctexryk) | Категория, район, организация и статус одновременно. Сохранение параметров при сортировке и переходе по страницам. Также проверен поиск по названию связанной организации. | Прошло. |
| [№75 · Привязка организаций](https://app.clickup.com/t/1100350000001549/z8rctexrzr) | Два типа привязки, согласия и права, сохранение публикации, история и конкурентные операции. | Прошло на тестовых данных. Фактические привязки AMI в рабочей системе ещё нужно принять. |
| [Доработки админ-панели](https://app.clickup.com/t/1100350000001549/z8rcte9eux) | Причина «4/5», состояние после сохранения, ссылка проверяющего на ожидающую заявку, корзина отдельного черновика и права доступа. | Прошло в проверенном объёме. Обязательность английского перевода остаётся продуктовым решением. |
| [Похожие и ближайшие места](https://app.clickup.com/t/1100350000001549/z8rcte8h4u) | Координаты и их отсутствие, устаревшая точка, отличия категории, переходы по ссылкам и скрытые места. | Прошло. 45 браузерных сочетаний. |

## Воспроизведение

Проверки Django проводились на отдельных контейнерах PostgreSQL 17 через `keep_pg.py`. Результат — **608 из 608**, три набора по 115, 253 и 240 тестов. Напечатанная в третьем наборе строка `QA synthetic interruption inside transition` относится к тесту восстановления. Набор завершился кодом 0.

```powershell
$qa = Join-Path $env:LOCALAPPDATA 'Temp/kidsmap-clickup-20261121-audit'
$py = '.venv/Scripts/python.exe'
& $py -X utf8 "$qa/keep_pg.py" catalog.testcases.test_moderation_sla catalog.testcases.test_moderation_sla_sources catalog.testcases.test_place_moderation_queue_coherence catalog.testcases.test_admin_review_workflow_fix catalog.testcases.test_appeal_pages catalog.testcases.test_appeal_sources catalog.testcases.test_appeal_workflow catalog.testcases.test_official_review_reply catalog.testcases.test_review_confirmation catalog.testcases.test_review_inbox_notifications catalog.testcases.test_mod_qa03_queue_sorting
& $py -X utf8 "$qa/keep_pg.py" catalog.testcases.test_task33_search catalog.testcases.test_task33_completion_taxonomy catalog.testcases.test_task33_public_details catalog.testcases.test_task33_pricing catalog.testcases.test_task33_map catalog.testcases.test_public_map_paging catalog.testcases.test_nearby_places catalog.testcases.test_park_administration_editors catalog.testcases.test_park_editor_markup catalog.testcases.test_phone_public_contract catalog.testcases.test_place_contact_policy catalog.testcases.test_legacy_pricing_notes catalog.testcases.test_current_pricing_contract catalog.testcases.test_admin_legacy_price_preservation catalog.testcases.test_place_public_tariff_terms catalog.testcases.pricing_plans catalog.testcases.pricing_plans_relational catalog.testcases.test_offer_qa09_partial_review_pricing
& $py -X utf8 "$qa/keep_pg.py" catalog.testcases.test_organization_connections catalog.testcases.test_organization_connections_concurrency catalog.testcases.test_admin_draft_search catalog.testcases.test_staff_profile catalog.testcases.test_volunteer_admin catalog.testcases.test_volunteer_dashboard catalog.testcases.test_draft_readiness_display catalog.testcases.test_place_editor_preview catalog.testcases.test_task33_volunteer_hub catalog.testcases.test_task33_publication catalog.testcases.test_publication_request_completion
& $py -X utf8 "$qa/acceptance48_near.py" sla
& $py -X utf8 "$qa/acceptance48_near.py" sla-edge
& $py -X utf8 "$qa/acceptance48_near.py" nearby
& $py -X utf8 "$qa/review_verify.py"
& $py -X utf8 "$qa/park_browser.py"
& $py -X utf8 "$qa/deep_review_official.py"
& $py -X utf8 "$qa/deep_review_price_runner.py"
$adminQa = Join-Path $env:LOCALAPPDATA 'Temp/kidsmap-clickup-ramin-five'
& $py -X utf8 "$adminQa/ramin_browser.py" all
```

Браузерные прогоны работали на loopback с временной SQLite. Проверка тарифа и редактора завершилась кодом 1 из-за трёх подтверждённых расхождений времени. Матрица вёрстки в этом же прогоне завершилась без расхождений. Факт выкладки каждого локального изменения на действующем сайте этим отчётом не подтверждён.

Полный прогон админки завершился кодом 0. Прошли 23 относящихся к колонке браузерных сценария. Две дополнительные сверки БД подтвердили сохранение всех четырёх тестовых справочных привязок с прежним владельцем и статусом публикации и помещение в корзину только выбранного черновика.
