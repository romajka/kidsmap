# SOCIAL-QA-01 — Сохранённая оценка не восстанавливается в редакторе

- Severity: **P2 OPEN**. Execution identity /root; 2026-10-10-r1; LOCAL isolated QA09, HEAD 8d188b316f800fbedf0b1e376905dfd4924cb1b6, source unchanged. Production applicability UNKNOWN. Classification PRE-EXISTING BASELINE; reproducibility fresh, confidence HIGH.
- Роль: автор. URL/endpoint: `/ru/reviews/{place|specialist|activity|event}/target/<id>/`.
- Шаги: Создать отзыв с оценкой4 через UI, отправить и перезагрузить страницу; повторить после одобрения.
- Ожидание: В редакторе выбрана сохранённая оценка текущей либо pending редакции.
- Факт: Текст восстановлен, select показывает «—», value пустой. В БД rating4/5 сохранён; новая отправка требует заново выбрать оценку.
- Доказательство: flows:reload-rating-*; proof:saved-rating-restored18 FAIL; [matrix](../matrix.json), raw result artifacts соответствующих scripts, [свежий PNG](../screenshots/proof-feedback-ru-390.png), [manifest](../screenshots-manifest.json).
- Первопричина (source verified): `src/catalog/templates/catalog/typed_reviews.html:24`. Ни одна option не получает selected; template не читает candidate/current rating.
- Impact / обоснование: Ограниченный подтверждённый сбой пользовательского сценария/доступности; компрометация, постоянная потеря данных и production авария не установлены.
- Область исправления: Восстановить selected из действительной candidate/current редакции и не менять рейтинг молча. Проверить pending/approved/rejected, reload и повторную отправку всех4типов.
- Owner/dependencies: frontend-reviewer + django-reviewer; единый выбор candidate/current, без изменения moderation/cooldown.
- Repair: [самостоятельный копируемый промпт](../repair-prompts/SOCIAL-QA-01.txt). Приложение в этом запуске не исправлялось.
