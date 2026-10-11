# SOCIAL-QA-03 — 409 убирает редактор и встроенное восстановление ввода

- Severity: **P2 OPEN**. Execution identity /root; 2026-10-10-r1; LOCAL isolated QA09, HEAD 8d188b316f800fbedf0b1e376905dfd4924cb1b6, source unchanged. Production applicability UNKNOWN. Classification PRE-EXISTING BASELINE; reproducibility fresh, confidence HIGH.
- Роль: автор. URL/endpoint: `/ru/reviews/specialist/target/1/`.
- Шаги: Открыть отзыв в2вкладках, отправить редакцию A, затем устаревшую B.
- Ожидание: 409 объясняет конфликт внутри интерфейса; несохранённый ввод B доступен для сравнения/повтора после обновления версии.
- Факт: Сервер защищает данные, но отдаёт отдельную страницу «Отзыв изменился. Обновите страницу.» без редактора, навигации и B.18cells. Back в отдельной проверке возвращал ввод — постоянная потеря данных не заявляется.
- Доказательство: edits:two-tabs-server-conflict/recovery/back; proof:matrix-two-tabs-40918 PASS,matrix-conflict-recovery18 FAIL; [matrix](../matrix.json), raw result artifacts соответствующих scripts, [свежий PNG](../screenshots/proof-conflict-ru-390.png), [manifest](../screenshots-manifest.json).
- Первопричина (source verified): `src/catalog/controllers/typed_reviews.py:65`. ReviewConflict обработан сырой HttpResponse409, а не формой/сохранением submitted payload.
- Impact / обоснование: Ограниченный подтверждённый сбой пользовательского сценария/доступности; компрометация, постоянная потеря данных и production авария не установлены.
- Область исправления: Добавить локализованную обработку409 с сохранением B и явным восстановлением/обновлением. Не превращать конфликт в успешное сохранение и не делать слепой повтор POST.
- Owner/dependencies: django-reviewer + frontend-reviewer; CAS, текущие права, candidate/live и cooldown обязательны.
- Repair: [самостоятельный копируемый промпт](../repair-prompts/SOCIAL-QA-03.txt). Приложение в этом запуске не исправлялось.
