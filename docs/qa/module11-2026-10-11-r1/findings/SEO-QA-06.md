# SEO-QA-06 · P2 · Редактор «Контент и SEO» возвращает 500

Status OPEN. Environment LOCAL isolated module11; fresh native/HTTP evidence 2026-10-11. Role: admin.

URL/endpoint: `/admin/catalog/catalogcontentsettings/1/change/`

Шаги: Войти synthetic superuser; открыть singleton editor в трёх языках; повторить DEBUGFalse в 6 ширинах.

Ожидание: Редактор открывается и позволяет native save/reload SEO landing config.

Факт: HTTP500; DEBUGTrue диагностика __str__ returned non-string (type __proxy__); DEBUGFalse native error18cells. Landing rename/repeated rename зависимо NOT RUN.

Причина: models/site.py:10 gettext_lazy; CatalogContentSettings.__str__ :784–785 возвращает proxy; Django6.0.2 options.py:1911 вызывает str(obj). HEAD+WORKTREE source одинаковы.

Приоритет и влияние: Один административный редактор полностью недоступен, public landing pages продолжают открываться. P2, без текущей production проверки.

Область исправления: CatalogContentSettings.__str__ Python string contract и bounded native/admin regression.

Владелец/зависимости: django-reviewer/frontend-admin; дальше native landing edit/rename audit.

Классификация: pre-existing LOCAL HEAD source in scoped15file comparison; fresh WORKTREE behavior. Приложение в целом dirty, pristine-HEAD runtime и production NOT RUN. Confidence HIGH для локального факта; внешние последствия UNKNOWN.

Evidence:

- [admin-errors.result.txt](../admin-errors.result.txt)
- [source-extra.md](../source-extra.md)
- [screenshots/admin-SEO-config-error-ru-360.png](../screenshots/admin-SEO-config-error-ru-360.png)

[Самостоятельный копируемый prompt](SEO-QA-06-repair.txt)
