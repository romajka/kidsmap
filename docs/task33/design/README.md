# Макеты KidsMap №33

Этап 02 создал [Owner HTML-прототипы](owner/index.html), [каталог экранов/снимков](owner/README.md) и browser evidence. Revision owner-02-r1 и admin-public-03-r1 **приняты пользователем 2026-09-29**; точное решение в [acceptance.md](acceptance.md). Specialist screens созданы этапом25, **specialist-25-r1 / ACCEPTED2026-10-03**; рабочие экраны интегрированы и проверены в этапе25.

Макеты используют существующие KidsMap tokens, логотип, Chiron и локальные Material Symbols; приложение не меняется. Синтетические данные, имитация сохранения/проверки/фото/приглашений пояснены на отдельной стартовой странице. Нет backend и внешних запросов.

Основные снимки: 390 и 1280. Проверены также 320/360/768/1024/1440, AZ/RU/EN, long text, keyboard/focus, errors/loading/empty/rejected/conflict/saving. Реальные результаты в [verification.json](owner/verification.json), ограничения и exact commands в [reports/02.md](../reports/02.md).

После решения пользователя в [acceptance.md](acceptance.md) записываются дата, явный ответ, revision и scope. Общий approved план не является approval ещё не принятых экранов.

## Admin/public — этап 03

Revision admin-public-03-r1, accepted2026-09-29. [Admin вход](admin/index.html), [public вход](public/index.html), [admin screen/screenshot index](admin/README.md), [public screen/screenshot index](public/README.md). Только статические демонстрационные fixtures: приложение/production не менялись.

Проверки: [browser aggregate](shared03/verification.json), [03 report](../reports/03.md), [independent review](../reports/03-review.md), [plan](shared03/plan.md).

## Specialist — этап 25

[Галерея specialist-25-r1](specialist/index.html?lang=ru), [семь сценариев и состояния](specialist/README.md), [отчёт25](../reports/25.md). CREATED / ACCEPTED2026-10-03: независимая design-часть принята пользователем; реализация25 DONE locally. Используются принятые tokens и локальные assets; приложение, БД и production не менялись исходным design checkpoint; последующая локальная интеграция описана в отчёте25.
