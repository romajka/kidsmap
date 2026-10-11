# MOD-QA-07 — Сводка ошибки специалиста разбивает HTML на отдельные символы

OPEN · P2 · 2026-10-10 · LOCAL WORKTREE/HEAD 8d188b316f800fbedf0b1e376905dfd4924cb1b6 · run module08-2026-10-10-r1. Browser evidence produced by /root; no independent specialist execution. Confidence HIGH для факта. Production UNKNOWN. Класс: существующий baseline текущего локального source, не regression от этого аудита.

Роль: admin; передать владельцу модуля03. URL/endpoint: `/ru/admin/catalog/specialist/1/change/`. Проверенные cells: RU/AZ/EN × 390/1440.

Шаги: В admin снять все специализации, выбрать rejected, указать причину, нажать Save и принять нативное подтверждение. Сервер отклоняет форму. Посмотреть верхнюю error summary.

Ожидание: Одна понятная ошибка «Обязательное поле» с переходом к специализациям, честное состояние несохранённого ввода.

Факт: Одна .errorlist превращается в 84 error-summary links: «Специализации: <», затем «u», «l», символы class/errorlist markup и далее. Красный блок занимает большую часть экрана. Allowlisted persisted state остаётся прежним, что является правильной валидацией.

Причина / границы гипотезы: В specialist/change_form.html цикл for error in field.errors перебирает AdminField.errors() как HTML string; нужен список ошибок underlying bound field. Подтверждены rendered links и source; это ошибка отображения, а не отсутствие required validation.

Source: src/catalog/templates/admin/catalog/specialist/change_form.html:12–14; Django admin.helpers.AdminField.errors. Доказательства: [specialist-finish.result.txt](../specialist-finish.result.txt), [specialist-save-proof.result.txt](../specialist-save-proof.result.txt), [specialist-error-banner-ru-1440.png](../screenshots/specialist-error-banner-ru-1440.png), [specialist-error-banner-en-390.png](../screenshots/specialist-error-banner-en-390.png). Полная [матрица](../matrix.json), [snapshot](../snapshot.json).

Приоритет P2: Сводка не сообщает пригодное для исправления сообщение и создаёт десятки лишних keyboard targets. Критическая потеря данных/компрометация этим evidence не установлена.

Область: Specialist server error summary и переход к underlying field/checkbox group; application validation не ослаблять. Зависимости / ownership: frontend-admin + Django владелец указанной поверхности; Модуль03; Django AdminField vs BoundField; inline error summaries проверить на тот же тип.

Приложение не исправлено. Следующий шаг: согласованный отдельный repair scope, [копируемый промпт](../repair-prompts/MOD-QA-07.txt).
