# SOCIAL-QA-07 — Название занятия заменено техническим Activity object

- Severity: **P3 OPEN**. Execution identity /root; 2026-10-10-r1; LOCAL isolated QA09, HEAD 8d188b316f800fbedf0b1e376905dfd4924cb1b6, source unchanged. Production applicability UNKNOWN. Classification PRE-EXISTING BASELINE; reproducibility fresh, confidence HIGH.
- Роль: гость/автор. URL/endpoint: `/ru/reviews/activity/target/1/ и языковые варианты`.
- Шаги: Открыть настоящую карточку занятия Uydurma QA09 fəaliyyət, затем его страницу отзывов.
- Ожидание: Заголовок явно называет занятие с языковым fallback.
- Факт: На review page заголовок «Отзывы: Activity object (1)» во всех18cells, хотя name_az сохранено и настоящая карточка отображает название.
- Доказательство: proof:activity-human-title18 FAIL; cards-sort:public-card-review-activity; [matrix](../matrix.json), raw result artifacts соответствующих scripts, [свежий PNG](../screenshots/proof-activity-title-ru-390.png), [manifest](../screenshots-manifest.json).
- Первопричина (source verified): `src/catalog/controllers/typed_reviews.py:90; src/catalog/models/catalog_structure.py:71`. target_name использует name_i18n либо str(target); Activity не имеет нужного name_i18n/__str__, унаследованные name_* не выбраны.
- Impact / обоснование: Непонятное название снижает ориентирование без потери прав/данных.
- Область исправления: Использовать действительное публичное имя Activity и существующий языковой fallback; сверить место/специалиста/мероприятие и отсутствие technical object IDs в пользовательском заголовке.
- Owner/dependencies: django-reviewer + frontend-reviewer; canonical public presentation/fallback, не добавлять независимую локализацию.
- Repair: [самостоятельный копируемый промпт](../repair-prompts/SOCIAL-QA-07.txt). Приложение в этом запуске не исправлялось.
