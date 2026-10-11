# SEO-QA-03 · P2 · Фото мероприятия отсутствует в social image metadata

Status OPEN. Environment LOCAL isolated module11; fresh native/HTTP evidence 2026-10-11. Role: guest/admin.

URL/endpoint: `/ru/event/1-uydurma-qa11-tedbir/ (AZ/EN аналоги)`

Шаги: Через admin Event1 загрузить собственный fixture.png, заполнить телефон/организатора; Save→reload; открыть публичную карточку и её head.

Ожидание: При наличии опубликованного главного фото OG/Twitter используют его абсолютный public URL.

Факт: Карточка показывает /media/events/fixture.png, изображение loaded=true; OG/Twitter image остаётся /static/img/logo.svg.18 native cells подтверждены.

Причина: event_detail.html не override og_image/twitter_image; base.html:31/36 берёт site logo. Place уже override оба фото-блока: ранняя гипотеза про Place Twitterlogo исключена.

Приоритет и влияние: Preview показывает логотип вместо афиши; P2 по потере содержательного изображения, без утверждения поведения внешних ботов.

Область исправления: Event template/head context, валидное public photo и fallback при отсутствии фото.

Владелец/зависимости: seo-reviewer/frontend-reviewer; SEO-QA-01 смежный template.

Классификация: pre-existing LOCAL HEAD source in scoped15file comparison; fresh WORKTREE behavior. Приложение в целом dirty, pristine-HEAD runtime и production NOT RUN. Confidence HIGH для локального факта; внешние последствия UNKNOWN.

Evidence:

- [post-change.result.txt](../post-change.result.txt)
- [screenshots/post-change-event-ru-360.png](../screenshots/post-change-event-ru-360.png)
- [screenshots/preview-event-ru-360.png](../screenshots/preview-event-ru-360.png)

[Самостоятельный копируемый prompt](SEO-QA-03-repair.txt)
