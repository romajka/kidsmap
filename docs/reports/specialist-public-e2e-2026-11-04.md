# Публичная карточка специалиста — end-to-end, 4 ноября 2026

**Вердикт: нужны исправления перед выпуском.** Публичная карточка читается на компьютере, но мобильный порядок блоков затрудняет выбор. Найдены отдельные функциональные ошибки и P1 в выводе карты. Это новые находки аудита публичной страницы; основные проблемные строки уже присутствуют в LOCAL HEAD b7659e79, а не появились при переносе формы из account shell.

Режим: AUDIT ONLY по просьбе пользователя оценить удобство, дать готовую ссылку и проверить позитивные/негативные сценарии. Lead — kidsmap-orchestrator (browser/UX), один независимый django-reviewer по канонической роли. Application source не изменялся. Production не открывался, commit/push/deploy не выполнялись. Dirty WORKTREE сохранён. Финальная сверка с предыдущей editor snapshot обнаружила параллельные изменения в owner_specialist_create.html и specialist_workspace.css; остальные3файла совпали. Эти изменения не сделаны данным аудитом и не откатывались. Предыдущая приёмка редактора не переносится автоматически на новый срез; данный отчёт принимает только проверенные публичные сценарии.

## Ссылка для оценки

[Демонстрационная карточка](http://127.0.0.1:8894/ru/specialists/demo-specialist/).

Локальная копия synthetic QA-базы: `.tmp/specialist-public-20261104/preview.sqlite3`. Анкета, контакты, квалификация и отзыв помечены как демо и не описывают реального специалиста. Использован штатный вариант без фотографии, который также выявил неработающую иконку-заглушку. Preview server оставлен включённым по запросу ссылки; на другом компьютере localhost недоступен. Карточка с безопасным тестовым XSS payload после проверки переведена в draft/inactive.

## Подтверждённые проблемы

| ID | Приоритет | Что происходит | Доказательство / исправление |
|---|---|---|---|
| PUB-B01 | **P1** | Адрес принимается формой как текст, но после публикации вставляется в InfoWindow как HTML. Это путь stored XSS. | `specialist_detail.html:569,593`. Actual proposal submit validation принимает payload; реальный rendered EN callback передал его в локальный Google stub, безвредный handler исполнился при открытии marker info. Google live НЕ проверен. Нужны DOM/text nodes, не конкатенация HTML. |
| PUB-B02 | P2 | Карта RU/AZ не запускается с дробными координатами. | `specialist_detail.html:567`: `40,4`/`49,86` в JavaScript, браузер `Unexpected number`, callback undefined. EN с точкой работает. Нужна locale-independent сериализация. |
| PUB-B03 | P2 | Число и звёзды рейтинга противоречат друг другу. | После реального browser submit + admin approve: header `★★★☆☆ 4,0`, сам отзыв `★★★★☆`. Source:64. |
| PUB-B04 | P2 | Форматированный WhatsApp содержит скобки в wa.me destination. | Desktop и mobile: `https://wa.me/994(00)0000000`; штатная форма допускает такой формат. Source473/512. Нужна нормализация до цифр. Переход к внешнему WhatsApp/звонок не выполнялись. |
| PUB-B05 | P2 | Заполненная только верхняя цена пропадает. | price_from=None/price_to75 → `—`; source351–357. Верхняя цена существует в модели/фильтре. |
| PUB-B06 | P2 | Возраст0–0 становится «любой возраст». | Проверка truthiness вместо None; source83. |
| PUB-B07 | P3 | EN возраст с «лет», AZ `Onlayn və oçno` и нижняя цена `od`, равная цена `40–40`. | Runtime EN/RU/AZ и isolated SSR; source85–89,343–354. |
| PUB-U01 | P2 UX | На телефоне цена/формат/место идут после описания, образования, документов, отзывов и дисклеймера. | RU390×844: цена примерно на3000px, отзывы на2200px. Около3.5 экранов до условий. Перенести краткие условия/языки/место ближе к имени. CTA звонка/WhatsApp закреплены и видны. |
| PUB-U02 | P2 UX | Гость пишет отзыв, но лишь при отправке узнаёт о необходимости входа; кнопки входа рядом нет. | Реальный POST401 содержит redirect_url, JS показывает только текст, feedback links0. После ручного входа возврат к #reviews работает, введённый до входа текст не восстановлен. Нужен ясный вход до ввода либо сохранение текста и переход. |
| PUB-U03 | P2 accessibility | Оценку нельзя выбрать клавиатурой. | Пять span, tabindex=-1, role отсутствует, обработчики только mouse/click. Нужна доступная группа выбора оценки. |
| PUB-U04 | P3 UI | Штатная заглушка без фото — пустой цветной квадрат; значки заголовков/контактов отсутствуют. | Actual computed `::before` для fa-user-tie = none, скриншоты. Material Symbols в общем header работают. |
| PUB-U05 | P2 UX | Языки консультации не показаны в подробной карточке. | Демо имеет AZ/RU/EN; в каталоге языки есть, detail-template/DOM их не выводят. |
| PUB-U06 | P3 UI | Лишний воздух в описании, технически выглядящие обычные синие ссылки «Это мой профиль»/«Все отзывы», тяжёлый дисклеймер для обычного педагога. | Визуальная оценка, не утверждение о backend-ошибке. `white-space:pre-line` на обёртке также сохраняет переводы строк template-разметки. |

PUB-M01, требует продуктового решения: название закрытой связанной карточки Place остаётся описанием места практики без ссылки. В коде это явный fallback, поэтому не объявлено доказанной утечкой. Уточнить, означает ли скрытие Place также скрытие его названия в существующей практике.

## Позитивные и негативные сценарии

- Browser каталог → поиск demo → ссылка → детальная карточка: PASS. Несуществующий поисковый запрос даёт0 соответствующих карточек; повторный поиск восстанавливает результат.
- RU/AZ/EN ×390/768/1024/1280/1440 +RU320:16 состояний. На обычной демо-карточке без координат нет горизонтального переполнения, page errors и неожиданных local HTTP>=400. Это не отменяет отдельные map errors на coordinate fixture.
- Сохранённые цена40–60, длительность45, возраст4–10, биография/образование, активное место и opt-in certificate выводятся. Нет утверждения, что все крайние значения отображаются верно — см. findings.
- Одобренный публичный synthetic certificate скачивается200; чужой private document404. Полная существующая privacy suite также PASS.
- Гость reviewPOST401; авторизованный без оценки400 без потери текста; отрицательные/нечисловые/слишком большие rating, пустой/слишком длинный текст отвергаются. GET405, безCSRF403. Последние случаи — isolated Django tests, не browser UI.
- Browser network-abort при отзыве: ошибка видна, текст сохранён, кнопка снова доступна. Повторная отправка200, форма скрыта, сообщение о модерации, публичных отзывов0.
- Реальная админка: selected review → «Одобрить» → «Выполнить»; статус approved. Повторная загрузка публичной карточки показывает тот же отзыв, рейтинг4,0 и count1. При этом отображение звёзд ошибочно — PUB-B03.
- Isolated tests: draft/pending/rejected/inactive profiles404, published active200. Pending review не виден; правка approved review сохраняет прежнюю публичную версию до решения; отклонение правки не стирает старый отзыв; принятие обновляет тот же review head и агрегаты. Повторный POST не создаёт второй публичный review head.
- Публичная карта: RU/AZ JS syntax failure воспроизведён в Chromium; EN callback + HTML sink проверены отдельно bounded stub. Доступ к настоящему Google API не использовался.

## Команды и результаты

Django runner очищает окружение, DJANGO_TESTING=1, SQLite test DB in-memory, LocMem cache, собственные media/filemail; внешние интеграции выключены.

```bash
.venv/bin/python .tmp/specialist-e2e-20261104/run.py test catalog.testcases.specialists catalog.testcases.test_specialist_price_filter catalog.testcases.test_task33_specialist_privacy --settings=qa_settings --noinput -v 1
# 42 PASS,31.339s,exit0
.venv/bin/python .tmp/specialist-e2e-20261104/run.py test .tmp/specialist-public-20261104 --pattern=test_backend_probe.py --settings=qa_settings --noinput -v 1
# 6 PASS,1.130s,exit0 — probes подтверждают и дефекты, это не48 тестов отсутствия багов
```

SQLite W047 — ожидаемое ограничение nulls-distinct, не PostgreSQL proof. Один промежуточный scratch SSR probe использовал неканонический AZ prefix и получил301; исправлен на `/`. Одна browser automation команда имела CSS-selector без кавычек вокруг5; исправлена. Не считаются дефектами приложения. Lazy images с naturalWidth0 до прокрутки не объявлены сломанными картинками.

Evidence: `.tmp/specialist-public-20261104/` — backend-audit.md, backend-probes.log, matrix.log, first-look.log, guest-review.log, review-invalid.log, review-network-retry.log, review-approved.log, catalog-search.log, catalog-docs.log, map-locales.log, map-sink-proof.log, source-snapshot.json. Screenshots: `output/playwright/specialist-public-*.png`.

Контракт [Google InfoWindow.content](https://developers.google.com/maps/documentation/javascript/reference/info-window): строка может содержать HTML, DOM Element/Text также поддерживаются; проверен через Context7 по официальной документации. Graph template coverage partial64/343–344, фактический source просмотрен.

NOT RUN: production, реальные звонки/сообщения/WhatsApp/SMTP/OAuth, live Google Maps, физические устройства/Safari/Firefox, concurrent PostgreSQL races, полный corpus всех модулей. Форму создания/модерацию профиля целиком повторно не прогоняли: они приняты в предыдущих отчётах; этот этап проверяет публичную карточку и путь отзывов.

Следующий bounded implementation: сначала безопасный map sink + locale-independent coordinates, затем contacts/rating/price/age и публичная mobile-композиция/языки/отзывы. Новые findings в этом аудите не исправлены.
