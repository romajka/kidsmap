# MOD-QA-04 — Escape не закрывает мобильную административную навигацию

OPEN · P2 · 2026-10-10 · LOCAL WORKTREE/HEAD 8d188b316f800fbedf0b1e376905dfd4924cb1b6 · run module08-2026-10-10-r1. Browser evidence produced by /root; no independent specialist execution. Confidence HIGH для факта. Production UNKNOWN. Класс: существующий baseline текущего локального source, не regression от этого аудита.

Роль: admin. URL/endpoint: `/ru/admin/; /ru/admin/catalog/place/`. Проверенные cells: RU/AZ/EN × 360/390/768.

Шаги: Фокусировать кнопку навигации, открыть Enter, нажать Escape. Проверить видимость sidebar и body.sidebar-open. Затем активировать оставшуюся сфокусированной кнопку Enter.

Ожидание: Escape закрывает открытое перекрывающее меню и сохраняет понятный видимый фокус.

Факт: После Escape sidebar остаётся видимым и sidebar-open сохраняется во всех 9 cells. Enter на прежней кнопке закрывает его. При pointer попытке нажать эту кнопку открытый sidebar/logo перекрывает её.

Причина / границы гипотезы: Обёртка использует data-widget=pushmenu; локальный kidsmap_admin_sidebar.js обрабатывает клавиши accordion-пунктов, но не обеспечивает Escape для внешнего sidebar. Runtime подтверждает отсутствие closure. Точная ответственность vendor pushmenu/местного adapter требует решения при исправлении.

Source: static/admin/js/kidsmap_admin_sidebar.js:1–82; административный header data-widget=pushmenu / Jazzmin PushMenu. Доказательства: [matrix.result.txt](../matrix.result.txt), [final-proof.result.txt](../final-proof.result.txt), [sidebar-Escape-proof-ru-390.png](../screenshots/sidebar-Escape-proof-ru-390.png), [sidebar-Escape-proof-en-768.png](../screenshots/sidebar-Escape-proof-en-768.png). Полная [матрица](../matrix.json), [snapshot](../snapshot.json).

Приоритет P2: Пользователь клавиатуры остаётся с перекрытым содержимым и фокусом на закрытом меню элементе. Критическая потеря данных/компрометация этим evidence не установлена.

Область: Интеграция header/sidebar PushMenu: Escape, видимый close/toggle и возврат фокуса. Зависимости / ownership: frontend-admin + Django владелец указанной поверхности; Vendor Jazzmin/AdminLTE; accordion semantics не ломать; не приписывать sidebar role=dialog без решения по контракту.

Приложение не исправлено. Следующий шаг: согласованный отдельный repair scope, [копируемый промпт](../repair-prompts/MOD-QA-04.txt).
