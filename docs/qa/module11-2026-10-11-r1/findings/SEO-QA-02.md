# SEO-QA-02 · P2 · Social title специалиста остаётся KidsMap

Status OPEN. Environment LOCAL isolated module11; fresh native/HTTP evidence 2026-10-11. Role: guest.

URL/endpoint: `/ru/specialists/fictional-qa11-specialist-ui-renamed/ (AZ/EN аналоги)`

Шаги: Переименовать специалиста через админку, подтвердить dialog, reload; открыть карточку и локальный preview.

Ожидание: og:title/twitter:title содержат идентичность опубликованного специалиста.

Факт: title/H1 — Uydurma QA11 specialist verified rename2; og:title и twitter:title — KidsMap.

Причина: specialist_detail.html override title/meta_description, но не og_title/twitter_title; base.html defaults.15 relevant source files совпадают с HEAD.

Приоритет и влияние: Пользователь preview не может определить специалиста по заголовку; ограниченное влияние, production эффект неизвестен.

Область исправления: Specialist detail social title blocks, общий формат title и approved публичный текст.

Владелец/зависимости: seo-reviewer/frontend-reviewer; согласовать с SEO-QA-01.

Классификация: pre-existing LOCAL HEAD source in scoped15file comparison; fresh WORKTREE behavior. Приложение в целом dirty, pristine-HEAD runtime и production NOT RUN. Confidence HIGH для локального факта; внешние последствия UNKNOWN.

Evidence:

- [specialist-clean.result.txt](../specialist-clean.result.txt)
- [post-change.result.txt](../post-change.result.txt)
- [screenshots/preview-specialist-ru-360.png](../screenshots/preview-specialist-ru-360.png)

[Самостоятельный копируемый prompt](SEO-QA-02-repair.txt)
