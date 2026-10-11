# SITE-QA-06 — Файл PNG с неверным содержимым сохраняется и ломает публичный логотип

**OPEN / P2 / LOCAL C:\kidsmap / module10-2026-10-10-r1 / 2026-10-10.** Классификация: pre-existing LOCAL application failure. Execution: /root sequential, свежие native Chromium и own isolated DB. Production UNKNOWN. Исполнитель аудита не менял application sources/существующие assertions; чужой drift зафиксирован в [SOURCE-DRIFT](../SOURCE-DRIFT.md).

**Роль:** admin / guest. **URL/endpoint:** `/admin/catalog/sitegalleryimage/ajax-upload/; /ru/`.

**Шаги:** Через native file chooser отправить qa10-bad.png (MIME image/png, содержимое Synthetic invalid PNG). Reload медиахаба и главной.

**Ожидание:** Ошибка валидации и сохранность прежнего валидного изображения.

**Факт:** Ответ 200 success=true, FileField заменён. После reload admin/public img.complete=true и naturalWidth=0. После фиксации доказательства валидный logo восстановлен через UI.

**Перепроверка WORKTREE:** Supplemental native process8825/8826 started from current-snapshot.json after recorded foreign source drift. Module10 relevant handlers/templates/MO remain unchanged; own reports preserve entry evidence. SITE-QA-01 current recheck is GET only; upload/delete proof earlier, identical handler hashes, no new security mutation.

**Приоритет и эффект:** P2: ошибочный файл повреждает глобальный публичный бренд и заменяет предыдущий рабочий файл.

**Первопричина / гипотеза:** Подтверждено: FileField и custom AJAX save не декодируют/не валидируют содержимое изображения до замены.

**Source:** `src/catalog/models/site.py:78`; `src/catalog/domain_admin/site.py:997`; `src/catalog/domain_admin/site.py:1010`. Source refs — объяснение, rendered evidence перечислено ниже. Confidence: высокий для наблюдаемого эффекта; confidence root указан отдельно.

**Доказательства:**

- [media-errors.result.txt](../media-errors.result.txt)
- [screenshots/invalid-file-saved-admin-mobile.png](../screenshots/invalid-file-saved-admin-mobile.png)
- [screenshots/invalid-file-public-mobile.png](../screenshots/invalid-file-public-mobile.png)
- [screenshots/logo-restored-public.png](../screenshots/logo-restored-public.png)
- [current-boundary.result.txt](../current-boundary.result.txt)

**Область исправления:** Проверять содержимое/разрешённые форматы до сохранения, лимиты и безопасное замещение. Ошибка должна сохранять старый файл и честный UI.

**Владелец / зависимости:** Storage/file lifecycle, validation, SITE-QA-01 authorization; реальные HTTP/native chooser tests.

**Следующий шаг:** отдельный repair scope с конкретным планом. [Готовый самостоятельный промпт](SITE-QA-06-repair.txt). Аудит ничего не исправляет.
