# Макеты KidsMap №33

Этап 02 создал [Owner HTML-прототипы](owner/index.html), [каталог экранов/снимков](owner/README.md) и browser evidence. Revision owner-02-r1; **awaiting_user_review**, не приняты пользователем. Admin/public набор этапа 03 создан; Specialist screens ещё не создавались.

Макеты используют существующие KidsMap tokens, логотип, Chiron и локальные Material Symbols; приложение не меняется. Синтетические данные, имитация сохранения/проверки/фото/приглашений пояснены на отдельной стартовой странице. Нет backend и внешних запросов.

Основные снимки: 390 и 1280. Проверены также 320/360/768/1024/1440, AZ/RU/EN, long text, keyboard/focus, errors/loading/empty/rejected/conflict/saving. Реальные результаты в [verification.json](owner/verification.json), ограничения и exact commands в [reports/02.md](../reports/02.md).

После решения пользователя в [acceptance.md](acceptance.md) записываются дата, явный ответ, revision и scope. Общий approved план не является approval ещё не принятых экранов.

## Admin/public — этап 03

Revision admin-public-03-r1, awaiting_user_review. [Admin вход](admin/index.html), [public вход](public/index.html), [admin screen/screenshot index](admin/README.md), [public screen/screenshot index](public/README.md). Только статические демонстрационные fixtures: приложение/production не менялись.

Проверки: [browser aggregate](shared03/verification.json), [03 report](../reports/03.md), [independent review](../reports/03-review.md), [plan](shared03/plan.md).
