# Объединение веток KidsMap — 2026-10-21

Единая рабочая ветка: `main`, основной каталог `/home/ramin/kidsmap`.
Разрешение пользователя: учесть изменения Antigravity и оставить одну ветку локально и на GitHub. Деплой не входит в эту операцию.

Основа: GitHub `main` на `ff6a6b705f62425498f532d3ed8c2cfaae2624e1` (20 октября). Сверены основной dirty checkout и `/home/ramin/kidsmap-transfer-2026-10-19` на `a7b0476e`.

Сохранены пять свежих файлов Antigravity: фильтрация цены, параметры каталога, повторная инициализация select после AJAX и связанные тесты. Добавлены 28 локальных планов. Более новые исправления из main сохранены: email identity, уведомления, SEO, public batch loader, галерея, закреплённые зависимости и версии статических ресурсов.

Истории старых веток включены родителями итогового коммита. Старые варианты файлов, index/worktree patches, SHA256 manifests и исходные Git refs доступны в приватном локальном архиве `/home/ramin/kidsmap-branch-archive-2026-10-21`. Исторические QA-артефакты не удаляются и исключены из локального Git status; настройки .env, рабочие базы, media и чужие процессы не менялись. Вторая копия исходников сохраняется с detached HEAD.

## Проверка

- PostgreSQL 17.10 и Django 6.0.9; `DJANGO_TESTING=1`; собственная временная база, LocMem cache/email, media/locales; оба Docker-контейнера с `--network none`, без опубликованных портов.
- Из `/km`: `python scripts/run_isolated_quality.py --profile-root /tmp/kidsmap-task33-qa04-branches-20261021-r2 --socket-dir /km/.tmp/kidsmap-task33-qa04-socket-branches-20261021/socket catalog.testcases.test_task33_search catalog.testcases.public`.
- Проверки Django и migration drift: PASS. Первый запуск 261 теста: 260 PASS, 1 ENVIRONMENT ERROR — в тестовую копию не был включён deploy/nginx. После добавления исходного deploy из того же дерева повторён только `catalog.testcases.public.TestPublicPagesSmoke.test_production_nginx_keeps_admin_host_out_of_www_redirect_block`: PASS. Приложение для этого не менялось.
- Python AST и `git -c core.whitespace=cr-at-eol diff --check`: PASS.
- Полный корпус приложения и rendered-browser QA: NOT RUN. Новая функциональность не принимается в production этой Git-операцией.

Публикация использует `[skip ci]`, предотвращая существующий push-main workflow. Удаление веток выполняется атомарно вместе с fast-forward main и проверкой ожидаемых SHA; force-rewrite истории не используется. Итоговые refs и workflow runs проверяются после публикации. Production не подключалась.
