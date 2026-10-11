# SITE-QA-13 — Фокус диалога удаления медиа выходит за modal

**OPEN / P2 / LOCAL C:\kidsmap / module10-2026-10-10-r1 / 2026-10-10.** Классификация: pre-existing LOCAL keyboard/accessibility failure. Execution: /root sequential, свежие native Chromium и own isolated DB. Production UNKNOWN. Исполнитель аудита не менял application sources/существующие assertions; чужой drift зафиксирован в [SOURCE-DRIFT](../SOURCE-DRIFT.md).

**Роль:** admin с клавиатурой. **URL/endpoint:** `/admin/catalog/sitegalleryimage/`.

**Шаги:** Открыть удаление logo. Дождаться анимации. Tab несколько раз, Shift+Tab. Сверить activeElement и aria-modal dialog. Escape, проверить сохранность файла.

**Ожидание:** Начальный фокус внутри диалога, Tab/Shift+Tab циклически остаются в нём.

**Факт:** Фокус остаётся/возвращается на background delete button; forward Tab не находится внутри modal. Escape после завершения анимации корректно закрывает и не удаляет файл.

**Перепроверка WORKTREE:** Supplemental native process8825/8826 started from current-snapshot.json after recorded foreign source drift. Module10 relevant handlers/templates/MO remain unchanged; own reports preserve entry evidence. SITE-QA-01 current recheck is GET only; upload/delete proof earlier, identical handler hashes, no new security mutation.

**Приоритет и эффект:** P2: keyboard пользователь не может надёжно работать с подтверждением удаления; focus уходит за блокирующий слой.

**Первопричина / гипотеза:** Гипотеза, не подтверждённая первопричина: взаимодействие initial focus/focus trap/других loaded admin handlers. Сам эффект фиксируется activeElement trace и native UI; требуется отдельное событие-by-событие исследование перед исправлением.

**Source:** `static/admin/js/kidsmap_notifications.js:107`; `static/admin/js/kidsmap_notifications.js:316`. Source refs — объяснение, rendered evidence перечислено ниже. Confidence: высокий для наблюдаемого эффекта; confidence root указан отдельно.

**Доказательства:**

- [modal-proof.result.txt](../modal-proof.result.txt)
- [visual-final.result.txt](../visual-final.result.txt)
- [focus-proof.result.txt](../focus-proof.result.txt)
- [screenshots/modal-final-viewport.png](../screenshots/modal-final-viewport.png)
- [current-focus.result.txt](../current-focus.result.txt)

**Область исправления:** Воспроизвести после bringToFront/ожидания, установить точную причину focus ownership. Исправить начальный фокус/trap/restore без изменения разрешений или удаления данных.

**Владелец / зависимости:** Unified notifications modal + loaded admin JS; Enter/Space/Tab/ShiftTab/Escape, all18 cells and other dialogs regression.

**Следующий шаг:** отдельный repair scope с конкретным планом. [Готовый самостоятельный промпт](SITE-QA-13-repair.txt). Аудит ничего не исправляет.
