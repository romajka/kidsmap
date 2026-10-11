# SEO-QA-04 · P2 · Публичное мероприятие не включается в sitemap

Status OPEN. Environment LOCAL isolated module11; fresh native/HTTP evidence 2026-10-11. Role: guest.

URL/endpoint: `/sitemap.xml; /event/1-uydurma-qa11-tedbir/`

Шаги: Включить события через admin; сохранить полноценное fictional Event через UI; GET AZ/RU/EN детали и sitemap; повторить после OFF→ON.

Ожидание: Публичное индексируемое Event получает sitemap entry по согласованному visibility/language contract.

Факт: Опубликованный Event GET200/index, JSON-LD Event присутствует; все 3 EventURL отсутствуют в свежих initial/final XML. Hidden/disabled entries не попадают.

Причина: src/config/urls.py:21 sitemap registry не содержит EventSitemap; current sitemaps.py Event класс не подключён.

Приоритет и влияние: Integration gap в обнаружении публичных событий. Это не доказательство отсутствия индексации и не privacy leak; ожидаемый inclusion contract должен сохранять disabled/private фильтры.

Область исправления: Event sitemap + регистрация; public predicate, approved даты/языки, flags.

Владелец/зависимости: seo-reviewer/django-reviewer; интеграционные тесты visibility.

Классификация: pre-existing LOCAL HEAD source in scoped15file comparison; fresh WORKTREE behavior. Приложение в целом dirty, pristine-HEAD runtime и production NOT RUN. Confidence HIGH для локального факта; внешние последствия UNKNOWN.

Evidence:

- [http-final.json](../http-final.json)
- [sitemap-final.xml](../sitemap-final.xml)
- [visibility.result.txt](../visibility.result.txt)

[Самостоятельный копируемый prompt](SEO-QA-04-repair.txt)
