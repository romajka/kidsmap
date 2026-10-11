# SEO-QA-07 · P3 · HEAD организаций и занятий возвращает 405 при GET200

Status OPEN. Environment LOCAL isolated module11; fresh native/HTTP evidence 2026-10-11. Role: guest.

URL/endpoint: `/organizations/7b78e253-9a64-4772-a308-7e59ae9a390b/ и /activities/1/, RU/AZ/EN`

Шаги: GET текущий public URL; HEAD тот же URL без params; повторить после rename/detach.

Ожидание: HEAD публичного GET ресурса поддерживается, сохраняет status/SEO headers и не возвращает тело.

Факт: GET200; HEAD405, Allow GET, во всех 3 языках для 2 типов. Свежий final повтор 6FAIL.

Причина: controllers/public_details.py:17/179 @require_GET допускает GET и отклоняет HEAD. HEAD check unchanged; privacy guard GET работает.

Приоритет и влияние: P3 interoperability для link checkers/клиентов. Это не доказательство, что Google не индексирует GET страницу.

Область исправления: Public Organization/Activity HTTP method decorators/headers; existing visibility/privacy guards.

Владелец/зависимости: django-reviewer/seo-reviewer; no DB migration needed.

Классификация: pre-existing LOCAL HEAD source in scoped15file comparison; fresh WORKTREE behavior. Приложение в целом dirty, pristine-HEAD runtime и production NOT RUN. Confidence HIGH для локального факта; внешние последствия UNKNOWN.

Evidence:

- [http-proof.json](../http-proof.json)
- [http-final.json](../http-final.json)
- [source-review.md](../source-review.md)

[Самостоятельный копируемый prompt](SEO-QA-07-repair.txt)
