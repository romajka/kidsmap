# SOCIAL-QA-02 — Автор не видит сохранённую причину отказа

- Severity: **P2 OPEN**. Execution identity /root; 2026-10-10-r1; LOCAL isolated QA09, HEAD 8d188b316f800fbedf0b1e376905dfd4924cb1b6, source unchanged. Production applicability UNKNOWN. Classification PRE-EXISTING BASELINE; reproducibility fresh, confidence HIGH.
- Роль: автор. URL/endpoint: `/ru/reviews/event/target/1/ и /reviews/specialist/target/2/`.
- Шаги: Автор отправляет; модератор отклоняет с QA09 reason. Для live отзыва отправить новую редакцию и отклонить. Автор делает reload.
- Ожидание: Автор видит отказ, причину и отклонённый текст, может исправить; approved live остаётся прежним.
- Факт: Причины сохранены в revisions; после отказа candidate pointer очищен. Редактор показывает прежний live либо только rejected head text, без причины/понятного статуса.18cells воспроизведены для отклонённого edit.
- Доказательство: decisions:rejection-reason-event; edits:rejected-edit-feedback-visible; proof:rejection-reason-visible18 FAIL; [matrix](../matrix.json), raw result artifacts соответствующих scripts, [свежий PNG](../screenshots/rejected-edit-feedback.png), [manifest](../screenshots-manifest.json).
- Первопричина (source verified): `src/catalog/services/review_versions.py:215; src/catalog/controllers/typed_reviews.py:86; src/catalog/templates/catalog/typed_reviews.html:22`. moderate_candidate очищает candidate_revision_id; own view/template не выбирают последнее отклонённое решение и не выводят reason.
- Impact / обоснование: Ограниченный подтверждённый сбой пользовательского сценария/доступности; компрометация, постоянная потеря данных и production авария не установлены.
- Область исправления: Показать автору последнее релевантное решение и reason без раскрытия приватных жалоб. Сохранить live/candidate invariant, обеспечить исправление и resubmit с reload.
- Owner/dependencies: django-reviewer + frontend-reviewer + security-reviewer; причина/жалоба остаются доступны только соответствующему автору/платформе.
- Repair: [самостоятельный копируемый промпт](../repair-prompts/SOCIAL-QA-02.txt). Приложение в этом запуске не исправлялось.
