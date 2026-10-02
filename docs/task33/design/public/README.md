# KidsMap public макеты — admin-public-03-r1

Status: **awaiting_user_review**. Только static synthetic fixtures этапа 03. Общий план не является принятием дизайна.

## Просмотр

`python3 docs/task33/design/shared03/preview.py` открывает allowlisted preview только на 127.0.0.1:8763. Затем `/docs/task33/design/public/index.html`. Завершить Ctrl+C. Сервер не раздаёт env, приложение, media или БД. HTML также можно открыть локально; проверки выполнены через HTTP.

AZ/RU/EN в шапке. Параметры `long=1`, `missing=1` показывают длинный текст и AZ fallback. Переводы учебные, не редакторская готовность реальных карточек. Все фотографии отсутствуют намеренно; category placeholder использует действующие tokens/Material Symbols. Данные не сохраняются после reload.

## Экраны

- [activity](activity.html?lang=ru)
- [catalog](catalog.html?lang=ru)
- [event](event.html?lang=ru)
- [events](events.html?lang=ru)
- [index](index.html?lang=ru)
- [organization](organization.html?lang=ru)
- [place](place.html?lang=ru)

Каталог: 3 конкретных места, 1 confirmed shared venue с 2 независимыми бизнесами; 1 парк без coordinates остаётся в list. Это схема карты, не подключённый map provider. Organization discovery по имени, без Org directory или фиктивной точки.

[Calendar](events.html?lang=ru&view=calendar); desktop month / mobile days + selected-day list. q/category/age/format/occurrence/month/date/view сохраняются при переключении и языке. Calendar не зависит от list pagination; маленькая fixture выдача не изображает реальную pagination/API. [Online](event.html?event=online&lang=ru), [canceled](event.html?event=canceled&lang=ru), [past](event.html?event=past&lang=ru).

[Narimanov branch](place.html?sample=narimanov&lang=ru) → [local activity](activity.html?sample=narimanov&lang=ru); [independent studio](place.html?sample=studio&lang=ru). Одинаковые значения цен двух филиалов — synthetic local fixtures, не общая цена Program.

Нет реальных photo/contact/geo данных. Контакты *.example.test демонстрационные; кнопка сайта перехватывается в preview. Местные условия и источник общих контактов видны; часы открытия отдельно от занятия. Отзывы/ratings раздельны, у Organization нет числового рейтинга.

## Browser screenshots

40 настоящих PNG Chromium, widths 390/1280. Отдельная матрица проверяет 320/360/390/768/1024/1280/1440 на AZ/RU/EN.

- [activity-ru-1280](screenshots/activity-ru-1280.png)
- [activity-ru-390](screenshots/activity-ru-390.png)
- [catalog-map-en-1280](screenshots/catalog-map-en-1280.png)
- [catalog-map-en-390](screenshots/catalog-map-en-390.png)
- [catalog-map-filtered-en-1280](screenshots/catalog-map-filtered-en-1280.png)
- [catalog-map-filtered-en-390](screenshots/catalog-map-filtered-en-390.png)
- [catalog-ru-1280](screenshots/catalog-ru-1280.png)
- [catalog-ru-390](screenshots/catalog-ru-390.png)
- [event-canceled-ru-1280](screenshots/event-canceled-ru-1280.png)
- [event-canceled-ru-390](screenshots/event-canceled-ru-390.png)
- [event-fallback-en-1280](screenshots/event-fallback-en-1280.png)
- [event-fallback-en-390](screenshots/event-fallback-en-390.png)
- [event-online-ru-1280](screenshots/event-online-ru-1280.png)
- [event-online-ru-390](screenshots/event-online-ru-390.png)
- [event-past-ru-1280](screenshots/event-past-ru-1280.png)
- [event-past-ru-390](screenshots/event-past-ru-390.png)
- [event-ru-1280](screenshots/event-ru-1280.png)
- [event-ru-390](screenshots/event-ru-390.png)
- [events-calendar-online-az-1280](screenshots/events-calendar-online-az-1280.png)
- [events-calendar-online-az-390](screenshots/events-calendar-online-az-390.png)
- [events-calendar-ru-1280](screenshots/events-calendar-ru-1280.png)
- [events-calendar-ru-390](screenshots/events-calendar-ru-390.png)
- [events-ru-1280](screenshots/events-ru-1280.png)
- [events-ru-390](screenshots/events-ru-390.png)
- [index-ru-1280](screenshots/index-ru-1280.png)
- [index-ru-390](screenshots/index-ru-390.png)
- [organization-ru-1280](screenshots/organization-ru-1280.png)
- [organization-ru-390](screenshots/organization-ru-390.png)
- [place-long-missing-az-1280](screenshots/place-long-missing-az-1280.png)
- [place-long-missing-az-390](screenshots/place-long-missing-az-390.png)
- [place-long-missing-en-1280](screenshots/place-long-missing-en-1280.png)
- [place-long-missing-en-390](screenshots/place-long-missing-en-390.png)
- [place-missing-ru-1280](screenshots/place-missing-ru-1280.png)
- [place-missing-ru-390](screenshots/place-missing-ru-390.png)
- [place-narimanov-ru-1280](screenshots/place-narimanov-ru-1280.png)
- [place-narimanov-ru-390](screenshots/place-narimanov-ru-390.png)
- [place-ru-1280](screenshots/place-ru-1280.png)
- [place-ru-390](screenshots/place-ru-390.png)
- [place-studio-en-1280](screenshots/place-studio-en-1280.png)
- [place-studio-en-390](screenshots/place-studio-en-390.png)

Evidence: [основная матрица](../shared03/verification.json), [дополнительная матрица](../shared03/extra-verification.json), [regressions](../shared03/regression-results.json), [отчёт 03](../../reports/03.md), [independent review](../../reports/03-review.md).
