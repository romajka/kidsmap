# SEO canonical: реализация 09.10.2026

Явная команда пользователя на внедрение рекомендованного решения. Ветка task33-progress; main не затронута. Основание: seo-indexation-audit-2026-10-09.md; план docs/superpowers/plans/2026-10-09-seo-canonical.md.

Изменения:
- Каталог301 удаляет однозначные page=1 и стандартныйsort=new, сохраняя фильтры/page>=2. Повторные/невалидные значения оставлены существующей политике paginator/noindex.
- Пагинация ссылается прямо на чистую первую страницу. Страницы2+ сохраняют index/self-canonical и локализованные alternates.
- Фильтрованные страницы сохраняют noindex,follow и получают canonical нормализованной текущей комбинации с устойчивым порядком ключей. Sitemap не включает фильтры.
- Place detail после проверки публичной видимости объединяет исправлениеslug и удалениеquery одним301. Скрытая карточка сquery сразу404.
- Существующие slug, публичные данные, auth/next, robots, пороги качества и SEO-посадочные не менялись. Новых миграций нет.

RED:27tests,12failures,0errors до изменения productioncode. Failures подтверждали неправильные redirect/canonical/first-page-link и hidden404; /tmp/kidsmap-seo-fix-20261009/red.
GREEN:27tests PASS за20.191s; /tmp/kidsmap-seo-fix-20261009/green.
REGRESSION:140tests PASS за86.909s; /tmp/kidsmap-seo-fix-20261009/regression. PublicPagesSmoke, PublicLanguageConsistency, LocalizedFilterOptions, PublicFilterCounts, SeoLandingVisibility, OrganizationDirectory, AuthValidationAndNextSecurity. В тестах smoke есть сообщения о пропуске responsive generation для искусственных невалидных изображений; tests0errors/0failures. На реальные загруженные изображения production вывод не переносится.

Команды: PATH="$PATH:/snap/bin" python3 docs/task33/qa04/run.py --output /tmp/kidsmap-seo-fix-20261009/{red,green,regression} с указанными labels; exactargv в run.json. Каждый запуск использовал отдельный PostgreSQL networknone/tmpfs/Unixsocket, DJANGO_TESTING=1, изолированныеcache/media/email; cleanupPASS. Синтаксис Python и gitdiff--check PASS.

Обновлены прежние ожидания только для согласованного нового контракта: page1→301; фильтры→свой canonical; первая paginationlink→чистый URL. Устойчивый порядок ключей проверяется отдельным тестом. Неподходящие assertions не удалялись.

Release protocol: immutable image из allowlisted Git archive; candidate check/migrate--check; только imagepin существующего override, безrelease-server.sh/миграций/syncdefaults/collectstatic. Предыдущий image/runtimeoverride сохраняются, rollbackбез восстановленияDB. Серверная проверка после выкладки сохраняется отдельно в /tmp/kidsmap-seo-fix-20261009/live и /opt/kidsmap-releases/20261009-seo-<sha>/REPORT.md; этот файл фиксирует локальную проверку перед релизом и сам не доказывает production deployment.

Границы: полный projectsuite, реальная Googleиндексация/URLInspection/requestindexing и GooglebotDNSverification NOTRUN. Существующие7 URL из GSC уже были200/index/selfcanonical/sitemap; менять их canonical оснований нет. Внедрение не гарантирует сроки/факт индексации Google.
