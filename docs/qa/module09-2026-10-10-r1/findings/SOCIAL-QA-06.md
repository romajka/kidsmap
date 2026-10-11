# SOCIAL-QA-06 — Выбор звёзд не имеет программного состояния

- Severity: **P2 OPEN**. Execution identity /root; 2026-10-10-r1; LOCAL isolated QA09, HEAD 8d188b316f800fbedf0b1e376905dfd4924cb1b6, source unchanged. Production applicability UNKNOWN. Classification PRE-EXISTING BASELINE; reproducibility fresh, confidence HIGH.
- Роль: автор отзыва о сайте. URL/endpoint: `/ru/reviews/ и языковые варианты`.
- Шаги: Tab к звезде, выбрать3 с Space/Enter, проверить rendered attributes и hidden rating.
- Ожидание: Доступное название оценки и программное состояние выбранного значения позволяют понять текущую оценку.
- Факт: Keyboard меняет hidden rating=3, active CSS красит звёзды, но aria-pressed/aria-checked/role radio отсутствуют; label — только цифра.72matrix проверки selected state FAIL. Реальный screen reader NOT RUN.
- Доказательство: matrix:site-rating-Space/Enter PASS; site-rating-selected-accessible72 FAIL; [matrix](../matrix.json), raw result artifacts соответствующих scripts, [свежий PNG](../screenshots/rating-author-ru-390.png), [manifest](../screenshots-manifest.json).
- Первопричина (source verified): `src/catalog/templates/pages/site_reviews.html:158,196`. paint() меняет только CSS.active; кнопки с numeric aria-label не сообщают выбор через семантику или live status.
- Impact / обоснование: Ограниченный подтверждённый сбой пользовательского сценария/доступности; компрометация, постоянная потеря данных и production авария не установлены.
- Область исправления: Обеспечить доступную группу оценки и объявляемое выбранное значение; согласовать keyboard, фокус, тексты AZ/RU/EN. Проверить mouse/Tab/ShiftTab/Space/Enter и native POST/reload.
- Owner/dependencies: frontend-reviewer + accessibility; server payload/range и default rating сохранить.
- Repair: [самостоятельный копируемый промпт](../repair-prompts/SOCIAL-QA-06.txt). Приложение в этом запуске не исправлялось.
