# SOCIAL-QA-05 — Страница отзывов о сайте переполняется на768px

- Severity: **P2 OPEN**. Execution identity /root; 2026-10-10-r1; LOCAL isolated QA09, HEAD 8d188b316f800fbedf0b1e376905dfd4924cb1b6, source unchanged. Production applicability UNKNOWN. Classification PRE-EXISTING BASELINE; reproducibility fresh, confidence HIGH.
- Роль: вошедший пользователь. URL/endpoint: `/ru/reviews/, /reviews/, /en/reviews/`.
- Шаги: Открыть страницу с доступной формой автора при768px; посмотреть hero, sorting и реакции.
- Ожидание: Контент/кнопки помещаются в viewport без горизонтального scroll и обрезки.
- Факт: Document822px при viewport768; сортировка справа805px, реакции791px. Computed review-form-grid tracks220/260/200px, width708/right784.59; форма содержит только2label. Guest без формы помещается.12matrix cells FAIL + отдельная geometry proof.
- Доказательство: matrix:site-overflow12 FAIL; proof:site768-form-fits; [matrix](../matrix.json), raw result artifacts соответствующих scripts, [свежий PNG](../screenshots/matrix-author-site-ru-768.png), [manifest](../screenshots-manifest.json).
- Первопричина (source verified): `static/css/site.css:6160; src/catalog/templates/pages/site_reviews.html:155`. Три минимальные grid tracks220/260/200 с gap28 дают intrinsic min-width708 вложенной форме и растягивают внешние блоки; responsive collapse наступает ниже проверенной ширины.
- Impact / обоснование: Ограниченный подтверждённый сбой пользовательского сценария/доступности; компрометация, постоянная потеря данных и production авария не установлены.
- Область исправления: Устранить лишнюю/жёсткую колонку и min-content overflow в реальной2полной форме. Не маскировать обрезку overflow-x:hidden; сверить остальные формы и18cells, особенно768.
- Owner/dependencies: frontend-reviewer; scoped .review-form-grid для site form, сохранение остальных consumers.
- Repair: [самостоятельный копируемый промпт](../repair-prompts/SOCIAL-QA-05.txt). Приложение в этом запуске не исправлялось.
