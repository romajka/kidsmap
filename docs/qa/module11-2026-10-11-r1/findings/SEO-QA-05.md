# SEO-QA-05 · P2 · Редактирование slug специалиста превращает старый URL в 404

Status OPEN. Environment LOCAL isolated module11; fresh native/HTTP evidence 2026-10-11. Role: guest/admin.

URL/endpoint: `/ru/specialists/fictional-qa11-specialist/ → /ru/specialists/fictional-qa11-specialist-ui-renamed/`

Шаги: В admin Specialist1 изменить exposed slug; подтвердить штатный dialog; save→reload; открыть новый и предыдущий URL во всех 3 языках.

Ожидание: Существующая публичная ссылка сохраняется либо получает permanent redirect к текущей идентичности без loop и приватного раскрытия.

Факт: Новый URL200 и canonical новый; старый 404, Location отсутствует во всех 3 языках. Обычные 2 name rename до slug edit сохраняли старый URL.

Причина: admin.py exposed slug; Specialist slug-only lookup views.py:2881 точный и alias resolver отсутствует. Модель генерирует slug только при пустом значении. Source соответствует HEAD.

Приоритет и влияние: Уже опубликованные/расшаренные ссылки ломаются после доступного UI изменения; P2, production масштабы неизвестны.

Область исправления: Политика стабильного specialist URL: immutable slug либо alias/history с 301 и public visibility guard; минимальные изменения, migrations только если необходимы согласованному дизайну.

Владелец/зависимости: seo-reviewer/django-reviewer/database-reviewer; URL policy, uniqueness, hidden states.

Классификация: pre-existing LOCAL HEAD source in scoped15file comparison; fresh WORKTREE behavior. Приложение в целом dirty, pristine-HEAD runtime и production NOT RUN. Confidence HIGH для локального факта; внешние последствия UNKNOWN.

Evidence:

- [specialist-clean.result.txt](../specialist-clean.result.txt)
- [screenshots/specialist-slug-reload.png](../screenshots/specialist-slug-reload.png)
- [screenshots/specialist-old-slug-ru.png](../screenshots/specialist-old-slug-ru.png)

[Самостоятельный копируемый prompt](SEO-QA-05-repair.txt)
