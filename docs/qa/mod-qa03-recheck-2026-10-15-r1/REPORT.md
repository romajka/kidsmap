# MOD-QA-03 — свежий recheck / PLAN COMPLETE, CONFIRMED OPEN

2026-10-15. Application changes: **0**. Closed IDs: **[]**. Требуется approval [конкретного плана](IMPLEMENTATION_PLAN.md). Исторические отчёты сохранены; MOD01/02 остаются scoped LOCAL PASS, ACCEPT-08 не выполнен.

## Snapshot и источник

Checkout `/home/ramin/kidsmap`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch `task33-progress`, dirty WORKTREE, active_run NONE. [entry.json](entry.json) содержит snapshot30517существующих файлов,68контейнеров,7известных QA HTTP процессов. Конечная сверка: [verification.json](verification.json), [preservation.json](preservation.json). Исторический continuity четырёх HTTP до module07 остаётся NOT VERIFIED; текущая сверка не восполняет прошлый пробел.

Собственный профиль `.tmp/mod-qa03-recheck-2026-10-15-r1`, HTTP43765, PID655705, PostgreSQL51543, DB/user `mod03_recheck_r1`, own container/volume `mod-qa03-recheck-2026-10-15-r1-pg`. Это параметры текущего запуска, не инструкция переиспользовать их позднее. Fresh synthetic1admin+3Place+3Event+3Specialist. 175migrations, Python3.12.3/Django6.0.2. Own DB/cache/media/private-media/email; DJANGO_TESTING=1, очищенное окружение, checkout `.env` не загружался. Socket guard разрешает собственный PG; native browser разрешает только собственный origin, внешние fonts заблокированы. Это не host-wide firewall. Runtime/source endpoint доступен только локальному QA-профилю и не добавлен в приложение.

Текущие RU/AZ/EN PO собраны `scripts/build_isolated_locales.py` в собственный каталог: build0, verify0; manifest и единственный LOCALE_PATHS до django.setup, реально открытые3MO подтверждены. Shared MO сохранены. [runtime-info.json](runtime-info.json), [runtime-source-final.json](runtime-source-final.json), [locale-manifest.json](locale-manifest.json), [dependency-manifest.json](dependency-manifest.json):953source hashes, фактические module/template origins, startup source совпадает с текущим checkout. Evidence создан с текущего dirty WORKTREE, не с чистого HEAD.

## Что подтверждено

Старый toolbar overflow больше не воспроизводится. Остаются фиксированная раскладка Place (дата0px/строки470.34375px приRU1024 expanded), отсутствие локальной прокрутки широких таблиц всех трёх очередей выше768px и отрицательная левая граница mobile sort вAZ/EN. Причины и точные source-селекторы перечислены в плане. Никакая другая MOD-задача этим отчётом не закрывается.

Baseline:108основных сочетаний,288native состояний/PNG; [accepted-baseline.json](accepted-baseline.json): **1121observations =1037PASS/84FAIL**, 0NOTRUN в принятой геометрической выборке. FAIL:27читаемость даты/высота строк,48локальная прокрутка,9mobile sort. Root overflow и toolbar fit прошли. Эти PASS не означают проверку всей функциональности админки.

Сохранён исходный [r2](native-baseline-r2.js.result.json):1036PASS/85FAIL. В одной базовой EN/Place1440collapsed точке измерение попало в незавершённую анимацию sidebar (206.8px вместо72). Только её6base assertions повторены с ожиданием конечной72px; итог5PASS/1sourceFAIL. Исходные результаты не заменены и assertions не изменены. [sidebar-transition-harness.json](sidebar-transition-harness.json), [stable subset](native-stable-subset.js.result.json). 18mobile expanded overlay состояний не используются для взаимодействия с перекрытым фоном; сортировка/колонки проверены после закрытия native overlay.

Первый partial harness:13FAIL/4NOTRUN,120observations,27PNG; закрыт только его собственный browser context после timeout попытки закрыть overlay перекрытой header-кнопкой. Исправлен только native путь закрытия через backdrop; полный r2 выполнен один раз. [baseline-harness-correction.json](baseline-harness-correction.json). Отдельный первый selected CSS trial завершился CLI1 из-за уже выполненного login; ошибка сохранена, subsequent trial использует fresh own context. [selected-trial-login-failure.json](selected-trial-login-failure.json).

## Предложение, не исправление

Только `static/admin/css/pages/kidsmap_changelist.css`, добавить27строк. Точный [diff](proposed.diff)/[SHA manifest](proposal-manifest.json). Существующие байты dirty-файла сохранены в proposal как префикс, приложение не изменено.

Выбранная CSS-схема протестирована только SIMULATED injection в отдельном собственном браузере:30Place states,21native local wheel;18mobile keyboard sort,12Event/Specialist wheel. Дата≥140px, строки≤80.5px, root fit, меню в viewport, видимый focus, scroll страницы0. [simulated-design-summary.json](simulated-design-summary.json). Эти данные не считаются postpatch GREEN; исходный CSS по-прежнему воспроизводит баг. Неиспользованные варианты и trial результаты сохранены.

[PNG manifest](png-manifest.json):414PNG с hashes/dimensions —288baseline-r2,3stable subset,27partial,3inspection,93SIMULATED (включая сохранённую duplicate-copy и альтернативы). Ручной просмотр выбранных изображений: [visual-review.json](visual-review.json), не утверждается просмотр всех414PNG. Native navigation/login/set-language/sidebar/summary clicks и keyboard focus использованы; jsdom/source inspection/HTTP200 не выдаются за rendered evidence. Предлагаемая CSS внедрялась явно и только в SIMULATED trials.

## Команды и границы

Точные argv/exit/duration: [commands.jsonl](commands.jsonl). Setup/prepare exit0; locale build/verify0; runtime-info0. Native inspect0, partial baseline0 с4NOTRUN, stop-own-baseline0, baseline-r2 CLI0 с85rawFAIL, CSS trial0, first selected trial1, corrected selected trial0, stable subset0 с1sourceFAIL, shared trial0. CLI0 не означает semantic PASS. `finalize_plan.py`0 агрегирует retained evidence/пишет proposal; `verify_plan.py` сохраняет конечные checks. Дополнительные read/view/metadata команды не подменяют браузерные проверки.

Browser diagnostics в исходных result JSON: намеренно blocked внешние fonts отмечены отдельно; final gate проверяет local HTTP errors/pageerror принятых baseline запусков. Partial context-close abort не переносится в accepted source result. Синтетический domain hash до/после unchanged. Network/browser guards не доказывают production или глобальную сетевую изоляцию машины.

**NOT RUN:** application patch, postpatch GREEN, functional search/sort/reset/columns/reload расширенная проверка, row action/popover clipping и keyboard horizontal scroll после patch, reviewer/volunteer роли в этой responsive выборке, модуль08 целиком, MOD04–08, глобальный корпус, production. Полный модуль07/неизменившиеся полные наборы не повторялись. Не выполнялись commit/push/deploy/reset/clean/stash/production accesses; active_run не присваивался. Существующие стенды/контейнеры/артефакты сохранены, свой стенд оставлен для review.

QA metadata correction: первый gate19PASS/1FAIL сохранён в [verification-gate-r1.json](verification-gate-r1.json). Он ошибочно ожидал всего3открытых MO, игнорируя22штатных каталога установленных Django/allauth/jazzmin. Финальный gate требует точное множество3own+22package MO, единственный own LOCALE_PATHS и отсутствие любых других project MO. [Обоснование](locale-gate-harness-correction.json); приложение/PO и browser assertions не менялись.

Конечный metadata gate: **20PASS/0FAIL**. Все30516существующих файлов кроме явно дополненного guide побайтно сохранены; предыдущий guide точно восстанавливается удалением своей заметки/ссылки. 68контейнеров и7HTTP процессов сохранили identity/state/ports, active_run NONE. CSS приложения не изменён. Это PLAN verification, не GREEN исправления.
