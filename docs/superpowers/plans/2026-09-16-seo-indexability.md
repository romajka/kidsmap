# SEO indexability implementation plan

**Goal:** Устранить подтверждённые технические помехи индексации опубликованных карточек KidsMap.
**Authorization:** Пользователь 16.09.2026 поручил выполнить улучшения, указав доступ к Git и серверу. Это продолжение одобренного исправления admin-host. Только точечные тесты.
**Architecture:** Сохранить SSR и существующую политику публикации. Исправить host routing, отделить чистую пагинацию каталога от фильтров и добавить FAQ в локализованный sitemap. Никаких изменений данных карточек без подтверждённых фактов, миграций или платного продвижения.
**Stack:** Django, nginx, Docker; AZ/RU/EN.
**Spec:** `docs/agent-audits/SEO_SEARCH_AUDIT_2026-09-16.md`, текущие указания пользователя.

## 1. Diagnose
- [x] Проверить текущий diff и источники canonical/robots/sitemap/pagination.
- [x] Сверить production revision и работающий image, подготовить откат на прежний image.
- [x] Перепроверить 3 старых исключения sitemap через URL Inspection; не менять исправившиеся URL. Все три уже в индексе.

## 2. Implement with targeted tests
Files: `src/catalog/context_processors.py`, `src/catalog/controllers/place_controller.py`, `src/catalog/sitemaps.py`, `src/catalog/testcases/public.py`; существующий diff `src/catalog/middleware.py`.
- [x] Добавить тесты: 13 пригодных карточек, `/catalog/?page=2` во всех языках → HTTP 200, index/follow, canonical и hreflang с `?page=2`, ссылки назад. `?page=1` → canonical без параметра. Неверные/вне диапазона номера не должны создавать индексируемые дубли.
- [x] Добавить тест на присутствие `/faq/`, `/ru/faq/`, `/en/faq/` в sitemap; сохранить тест фильтра `category=EDU` с noindex.
- [x] Увидеть ожидаемые падения; передать фактический номер страницы из controller в request SEO context; использовать его только для чистой пагинации `place_list`. Добавить `faq_page` в StaticViewSitemap.
- [x] Проверить admin-host redirect: auth/login, auth/register, place, root и локализованные публичные маршруты. `/admin/` остаётся на admin-host. Дополнительно отдельный robots на admin-host разрешает обход именно редиректов (не административных страниц).
- [x] Запустить только затронутые тесты в изолированной БД с `DJANGO_TESTING=1`, затем `git diff --check`: 16 tests OK.

## 3. Release and verify
- [x] Сформировать небольшой release commit `f8005bb0`; production base совпала. Предыдущий image сохранён. Сборка до переключения web, без release-server (он меняет БД и статические файлы вне scope).
- [x] Выпустить только код SEO без миграций и изменения контента; health/public/admin smoke успешны. Откат подготовлен и не потребовался.
- [x] Проверить опубликованные canonical/robots/301 и sitemap. IndexNow принял 240 публичных canonical URL, HTTP 200.
- [x] Уточнить отчёт: `docs/agent-audits/SEO_IMPLEMENTATION_2026-09-16.md`, команды тестов, результаты live/GSC, список контентных задач и границы результата.
