# MOD-QA-05 — В подтверждении снятия с публикации фокус остаётся на BODY

OPEN · P2 · 2026-10-10 · LOCAL WORKTREE/HEAD 8d188b316f800fbedf0b1e376905dfd4924cb1b6 · run module08-2026-10-10-r1. Browser evidence produced by /root; no independent specialist execution. Confidence HIGH для факта. Production UNKNOWN. Класс: существующий baseline текущего локального source, не regression от этого аудита.

Роль: admin. URL/endpoint: `/ru/admin/catalog/place/ → row menu → toggle-publication confirmation`. Проверенные cells: Все 18 language/width cells; cause повторён в RU/AZ/EN × 390/1440.

Шаги: Фокусировать row more-actions, Enter, выбрать снятие с публикации. Нажимать Tab и Shift+Tab, затем Escape.

Ожидание: Начальный фокус внутри alertdialog, кнопки доступны Tab/Shift+Tab, после Escape фокус возвращается на видимый row opener.

Факт: Начальный фокус BODY, последовательные Tab остаются BODY. Escape закрывает modal, но фокус не возвращается opener. В списке focusables первый элемент — SVG use href=#kmi-warning с tabIndex=-1 и aria-hidden=true.

Причина / границы гипотезы: getFocusableElements включает любой [href], в том числе SVG use. Warning confirm не соответствует primary/danger selector, поэтому autofocus и trapping используют нефокусируемый use. lastFocusedElement записывается после закрытия row menu, без явного видимого opener; native readback возвращает BODY.

Source: static/admin/js/kidsmap_notifications.js:64–75,90–138,157–177,319–327; static/admin/js/kidsmap_place_changelist.js:row action handler. Доказательства: [supplement.result.txt](../supplement.result.txt), [final-proof.result.txt](../final-proof.result.txt), [modal-focus-cause-ru-1440.png](../screenshots/modal-focus-cause-ru-1440.png), [modal-focus-cause-en-390.png](../screenshots/modal-focus-cause-en-390.png), [modal-focus-restored-en-390.png](../screenshots/modal-focus-restored-en-390.png). Полная [матрица](../matrix.json), [snapshot](../snapshot.json).

Приоритет P2: Подтверждение публикационного действия практически недоступно через прямой Tab-путь; потеря фокуса после закрытия. Критическая потеря данных/компрометация этим evidence не установлена.

Область: Общий kmModal focus engine + передача/восстановление row trigger. Только реально focusable HTML controls; warning tone учитывать. Зависимости / ownership: frontend-admin + Django владелец указанной поверхности; Общий компонент влияет на confirmations в других модулях; отдельно MOD-QA-06 i18n.

Приложение не исправлено. Следующий шаг: согласованный отдельный repair scope, [копируемый промпт](../repair-prompts/MOD-QA-05.txt).
