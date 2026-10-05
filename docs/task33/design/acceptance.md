# Принятие макетов

Owner status: **accepted**. Revision: **owner-02-r1**, 2026-09-29. Макеты созданы и проверяются отдельно от принятия пользователем. Принят пользователем 2026-09-29, отдельный ответ: «Принимаю оба набора».

| Набор | Создан | Принят пользователем | Evidence |
|---|---|---|---|
| Owner: Place/Organization/Program/groups/team, этап 02 | да, owner-02-r1 | да — accepted | [HTML-вход](owner/index.html), [каталог экранов и снимков](owner/README.md), [browser evidence](owner/verification.json), [отчёт 02](../reports/02.md) |
| Admin/public/catalog/calendar, этап 03 | да, admin-public-03-r1 | да — accepted | [Admin](admin/index.html), [Public](public/index.html), [экраны admin](admin/README.md), [экраны public](public/README.md), [отчёт 03](../reports/03.md) |
| Дополнительные Specialist screens, этап 25 | да, specialist-25-r1 | да — ACCEPTED 2026-10-03 | [Галерея](specialist/index.html?lang=ru), [сценарии](specialist/README.md), [отчёт 25](../reports/25.md); прямой ответ «принимаю продолдавй» |

## Набор экранов для решения

1. [Четыре секции самостоятельного места](owner/place.html?state=empty&lang=ru), [парк без организации](owner/place.html?sample=park&lang=ru), [филиал с общими контактами](owner/place.html?sample=network&lang=ru).
2. [Создание организации без адреса/филиала](owner/organization.html?lang=ru).
3. [Пустой кабинет](owner/cabinet.html?sample=empty&lang=ru), [организация без филиалов](owner/cabinet.html?sample=org-empty&lang=ru), [сеть и статусы филиалов](owner/cabinet.html?sample=network&lang=ru).
4. [Общая программа и влияние на филиалы](owner/program.html?lang=ru).
5. [Местные группы, расписание и цены](owner/groups.html?lang=ru).
6. [Приглашение, индивидуальные действия и границы доступа](owner/team.html?lang=ru).
7. [Сохранение с ошибкой](owner/place.html?state=save-failed&lang=ru), [конфликт](owner/place.html?state=conflict&lang=ru), [опубликовано + изменения на проверке](owner/place.html?sample=network&state=published-pending&lang=ru). Остальные состояния доступны со стартовой страницы.

Снимки на 390/1280 и ссылки каждого экрана — в [owner/README.md](owner/README.md). AZ/RU/EN переключаются в шапке. Все данные и действия демонстрационные.

## Запись решения пользователя

2026-09-29: пользователь ответил «Принимаю оба набора» на вопрос о принятии owner-02-r1 и admin-public-03-r1 для этапа05. Приняты оба полных набора, не только отдельные экраны. Specialist screens не входят в это принятие.

Admin/public status: **accepted**. Revision: **admin-public-03-r1**, 2026-09-29. Принят пользователем 2026-09-29 ответом «Принимаю оба набора»; результаты browser/review записаны в отчёте03. Перед 05–28 обязательны принятие Owner + admin/public и baseline 04; перед 25 также Specialist screens. Production launch не запрашивался.

## Набор 03 для решения пользователя

1. [Organization admin](admin/organization.html?lang=ru), [Place без Organization](admin/place.html?lang=ru), [направления/группы](admin/groups.html?lang=ru).
2. [Волонтёрское предложение](admin/review.html?lang=ru), [конфликт базы](admin/review.html?state=conflict&lang=ru), [новый объект](admin/review.html?state=new&lang=ru), [общая программа и два активных филиала](admin/review.html?state=program&lang=ru).
3. [Передача владельца](admin/transfer.html?lang=ru) с последствиями для команды и приглашений.
4. [Каталог конкретных мест](public/catalog.html?lang=ru), переключатель схемы карты и независимые карточки общей площадки; Organization discovery по названию.
5. [Organization detail без общего рейтинга](public/organization.html?lang=ru), [Place detail](public/place.html?lang=ru), [Activity с местными условиями](public/activity.html?lang=ru).
6. [Список афиши](public/events.html?lang=ru), [календарь](public/events.html?view=calendar&lang=ru), [онлайн](public/event.html?event=online&lang=ru), [отмена](public/event.html?event=canceled&lang=ru), [архив](public/event.html?event=past&lang=ru).
7. [Нет фото/координат/RU перевода](public/place.html?sample=park&missing=1&lang=ru), [длинный EN перевод](public/place.html?long=1&lang=en).

Отдельное явное решение получено 2026-09-29: owner-02-r1 и admin-public-03-r1 приняты. Baseline04 DONE; checkpoint для05 выполнен. Это историческое решение не включает Specialist screens и production.

## Specialist — принято пользователем

2026-10-03: после предъявления specialist-25-r1 пользователь ответил «принимаю продолдавй». Полный набор принят; разрешено продолжить application integration и проверки в том же этапе25. Повторного принятия не требуется. Историческая запись design checkpoint ниже сохранена; NOT_ACCEPTED/REVIEW_PENDING в ней описывает состояние до этого ответа.

2026-10-03: создан и независимо проверен **specialist-25-r1 / CREATED / REVIEW_PENDING**. Пользователь ещё не принимал этот набор. Галерея и семь рабочих сценариев: [публичный профиль](specialist/profile.html?lang=ru), [личный кабинет](specialist/person.html?lang=ru), [сотрудничество организации](specialist/organization.html?lang=ru), [подтверждение личности](specialist/claim.html?lang=ru), [приватные документы](specialist/documents.html?lang=ru), [проверка KidsMap](specialist/review.html?lang=ru), [сверка переноса](specialist/reconciliation.html?lang=ru). Варианты ошибок, ограничений доступа, подтверждений и истории доступны в [каталоге](specialist/README.md).

Только синтетические данные и демонстрационные действия. Реальная интеграция приложения, backend ACL и перенос fixtures остаются до продолжения этапа25 после принятия. Прямое условие [промпта25](../prompts/25.md): «Реализацию Specialist экранов начинай после их принятия». Принятие owner/admin-public повторно не требуется; этап26 не запущен.
