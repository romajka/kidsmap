# MOD-QA-06 — AZ/EN подтверждение снятия с публикации написано по-русски

OPEN · P2 · 2026-10-10 · LOCAL WORKTREE/HEAD 8d188b316f800fbedf0b1e376905dfd4924cb1b6 · run module08-2026-10-10-r1. Browser evidence produced by /root; no independent specialist execution. Confidence HIGH для факта. Production UNKNOWN. Класс: существующий baseline текущего локального source, не regression от этого аудита.

Роль: admin. URL/endpoint: `/admin/catalog/place/ и /en/admin/catalog/place/ → row unpublish`. Проверенные cells: AZ/EN × все 6 ширин; RU контроль.

Шаги: Перейти в AZ или EN очередь и открыть подтверждение снятия опубликованного места.

Ожидание: Заголовок, объяснение и кнопки на выбранном языке; пользовательское название места может сохранять свой язык.

Факт: «Снять с публикации?», русское объяснение, «Да, снять», «Отмена» в AZ и EN. На EN окружающая основная административная UI переведена. Подтверждено 12 captured texts и 4 повторных browser cells.

Причина / границы гипотезы: Строки захардкожены в kidsmap_place_changelist.js:647–654 и не получают i18n/data labels. Source не зависит от версии .mo. Собственный первоначальный matcher содержал mojibake; статус исправлен по сохранённому rendered text и независимо повторён final-proof.

Source: static/admin/js/kidsmap_place_changelist.js:647–654,575–579; shared notifications defaults. Доказательства: [supplement.result.txt](../supplement.result.txt), [final-proof.result.txt](../final-proof.result.txt), [matrix.json](../matrix.json), [unpublish-modal-en-390.png](../screenshots/unpublish-modal-en-390.png), [unpublish-modal-az-1440.png](../screenshots/unpublish-modal-az-1440.png). Полная [матрица](../matrix.json), [snapshot](../snapshot.json).

Приоритет P2: Критичное объяснение снятия карточки непонятно пользователю выбранного языка. Критическая потеря данных/компрометация этим evidence не установлена.

Область: Локализованные labels для row unpublish confirmation; связанные hardcoded success text проверить отдельно, они пока source-only. Зависимости / ownership: frontend-admin + Django владелец указанной поверхности; Django gettext/data attributes; MOD-QA-05 для общей modal проверки; не переводить пользовательские сохранённые названия.

Приложение не исправлено. Следующий шаг: согласованный отдельный repair scope, [копируемый промпт](../repair-prompts/MOD-QA-06.txt).
