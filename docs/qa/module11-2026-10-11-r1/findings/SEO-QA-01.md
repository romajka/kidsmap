# SEO-QA-01 · P2 · Карточки используют общее описание каталога в OG/Twitter

Status OPEN. Environment LOCAL isolated module11; fresh native/HTTP evidence 2026-10-11. Role: guest.

URL/endpoint: `Публичные Place/Organization/Activity/Specialist/Event, AZ/RU/EN`

Шаги: Открыть любую seeded опубликованную карточку; сравнить meta description и OG/Twitter description; выполнить reload и собственный локальный preview.

Ожидание: Social descriptions описывают именно текущую карточку и соответствуют её approved описанию.

Факт: meta description индивидуальный; og:description и twitter:description — общий текст каталога.90 native failures включают это на 5entity×18cells.

Причина: base.html:30/35 содержит отдельные блоки meta_description_og/twitter_description; detail templates переопределяют только meta_description. Причина подтверждена source-extra.md; файлы совпадают с HEAD.

Приоритет и влияние: Ограниченный дефект представления ссылки: теряется содержание карточки. Реальные внешние платформы/CTR не проверены.

Область исправления: Публичные detail templates/shared SEO context; только approved public descriptions, fallback/escaping и privacy.

Владелец/зависимости: seo-reviewer, frontend-reviewer; зависимости SEO-QA-02/03 имеют смежные template blocks.

Классификация: pre-existing LOCAL HEAD source in scoped15file comparison; fresh WORKTREE behavior. Приложение в целом dirty, pristine-HEAD runtime и production NOT RUN. Confidence HIGH для локального факта; внешние последствия UNKNOWN.

Evidence:

- [browser-matrix.result.txt](../browser-matrix.result.txt)
- [post-change.result.txt](../post-change.result.txt)
- [screenshots/preview-place-ru-360.png](../screenshots/preview-place-ru-360.png)

[Самостоятельный копируемый prompt](SEO-QA-01-repair.txt)
