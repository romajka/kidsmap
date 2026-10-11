# SOCIAL-QA-09 — Пагинация и сортировка ленты отзывов сбрасываются301

- Severity: **P2 OPEN**. Execution identity /root; 2026-10-10-r1; LOCAL isolated QA09, HEAD 8d188b316f800fbedf0b1e376905dfd4924cb1b6, source unchanged. Production applicability UNKNOWN. Classification PRE-EXISTING BASELINE; reproducibility fresh, confidence HIGH.
- Роль: гость/автор. URL/endpoint: `/ru/place-reviews/?page=2 и ?sort=likes; AZ/EN variants`.
- Шаги: Иметь29 approved reviews; нажать страницу2 либо выбрать «likes» в реальном select и применить.
- Ожидание: Показана2страница с другими отзывами; выбранный sort сохраняется.
- Факт: GET?page=2 получает301 Location на URL без query; browser возвращается к active page1 во всех18cells. Sort likes также301→popular во всех3языках. Site reviews control?page=2=200 и native pagination PASS.
- Доказательство: pagination-probe request chain; pagination-matrix:place-index-page2 18 FAIL; cards-sort:place-review-sort-preserved3 FAIL; [matrix](../matrix.json), raw result artifacts соответствующих scripts, [свежий PNG](../screenshots/pagination-ru-390.png), [manifest](../screenshots-manifest.json).
- Первопричина (source verified): `src/catalog/services/public_urls.py:12,28,81; src/catalog/middleware.py:84; src/catalog/controllers/place_reviews_controller.py:34`. Allowlist содержит site_reviews:{sort,page}, но не place_reviews. PublicQueryParameterCanonicalMiddleware удаляет законные параметры до Paginator/sorting.
- Impact / обоснование: Ограниченный подтверждённый сбой пользовательского сценария/доступности; компрометация, постоянная потеря данных и production авария не установлены.
- Область исправления: Разрешить только реальные параметры sort/page для place_reviews в canonical query contract, сохранив удаление посторонних параметров. Native page1/2/3, сортировка, RU/AZ/EN, language switching/canonical/redirect и другие URL должны пройти свежую проверку.
- Owner/dependencies: django-reviewer + seo-reviewer + frontend-reviewer; module11 query/canonical/language regressions.
- Repair: [самостоятельный копируемый промпт](../repair-prompts/SOCIAL-QA-09.txt). Приложение в этом запуске не исправлялось.
