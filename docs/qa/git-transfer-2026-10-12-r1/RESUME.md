# Продолжение KidsMap после Git-переноса

Дата: 2026-10-12. Репозиторий: `https://github.com/romajka/kidsmap`, ветка **task33-progress**. Production не обновлялся. Итог передачи и проверки remote ref — в [REPORT](REPORT.md).

На другом ПК получи ветку обычными fetch/switch/pull. Перед переключением проверь свой WORKTREE; не сбрасывай и не перезаписывай чужие локальные изменения. Если Git сообщает конфликт, сохрани изменения и разберись с ним до продолжения. Изменения в main не вносить.

```text
Продолжаем KidsMap из полученной ветки task33-progress на этом ПК.

Определи фактический checkout, HEAD, branch, dirty WORKTREE и active_run. Найди docs/qa/git-transfer-2026-10-12-r1/REPORT.md и docs/qa/continuation-and-repair-prompts-2026-10-11.md. Прочитай статус передачи, общие инструкции guide, таблицу всех13 модулей, правила PLAN / IMPLEMENT-APPROVAL / ACCEPT, перенос через Git и сопутствующий repair-index.json. Отдельные технические задания подробно разбирай после выбора scope; не загружай все73 задания заранее.

Прочитай AGENTS.md и канонические .agents: README, registry, действующее определение kidsmap-orchestrator, architecture, source-of-truth и audit-contract. Сверь текущий статус со свежими docs/qa/module01-recheck-2026-10-11-r1/REPORT.md и docs/qa/place-qa08-fix-2026-10-11-r1/REPORT.md. module13 MASTER_AUDIT — исторический ledger, не новая полная приёмка текущего checkout.

Проверь, что PLACE-QA-01–08 fixes, scripts/build_isolated_locales.py, связанные regression tests и QA documents реально получены. PLACE-QA-08 = CROSS-QA-03, одна причина; не исправляй их повторно по старому r2. Full module01 ещё NOT RUN. Оставшаяся историческая очередь:76 ID/73 группы для свежего recheck; guide содержит73 PLAN,13 ACCEPT,2 служебных блока. Это не76 свежо подтверждённых багов.

Старые Windows paths/localhost/PID/DB/container/browser sessions и .tmp/.venv/shared MO не переносимы. Для последующих проверок нужен собственный изолированный DJANGO_TESTING=1 стенд и свежий locale build с проверенным manifest до django.setup. Текущий этап — только ознакомление, без запуска стенда, новых fixes, commit/push/deploy или production.

Дай конкретную сводку: где найден guide, фактический snapshot, что выполнено/что осталось, как пользоваться PLAN→одобрение плана→IMPLEMENT→ACCEPT, каких материалов не хватает и какой следующий prompt рекомендуешь. Остановись после сводки: выбранное задание пользователь отправит отдельно. Сохрани чужие изменения, active_run и стенды.
```

Рекомендуемый первый следующий scope: **ACCEPT-01**, недостающая полная приёмка постоянных мест. Реализация остальных findings — после свежего recheck, конкретного сохранённого плана и одобрения его scope. На сервер выгружать только по отдельному поручению после завершения нужных исправлений/проверок.
