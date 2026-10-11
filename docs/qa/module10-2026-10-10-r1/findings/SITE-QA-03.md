# SITE-QA-03 — Редактируемый текст контактов не используется публичной страницей

**OPEN / P2 / LOCAL C:\kidsmap / module10-2026-10-10-r1 / 2026-10-10.** Классификация: pre-existing LOCAL application failure. Execution: /root sequential, свежие native Chromium и own isolated DB. Production UNKNOWN. Исполнитель аудита не менял application sources/существующие assertions; чужой drift зафиксирован в [SOURCE-DRIFT](../SOURCE-DRIFT.md).

**Роль:** admin / guest. **URL/endpoint:** `/admin/catalog/sitecontactssettings/1/change/; /ru/contacts/; /contacts/; /en/contacts/`.

**Шаги:** Сохранить contacts_text_ru/az/en через админку, reload и затем публичные contacts в 18 cells.

**Ожидание:** Публичная страница выводит сохранённый текст соответствующего языка.

**Факт:** Ни один из 18 contacts display checks не находит сохранённый QA10-текст. Footer phone/email при этом обновляются и видны.

**Перепроверка WORKTREE:** Supplemental native process8825/8826 started from current-snapshot.json after recorded foreign source drift. Module10 relevant handlers/templates/MO remain unchanged; own reports preserve entry evidence. SITE-QA-01 current recheck is GET only; upload/delete proof earlier, identical handler hashes, no new security mutation.

**Приоритет и эффект:** P2: настройка создаёт ложное ожидание успешного изменения публичных контактов.

**Первопричина / гипотеза:** Подтверждено: context processor отдаёт site_contacts_text, но contacts.html не потребляет его.

**Source:** `src/catalog/context_processors.py:319`; `src/catalog/templates/pages/contacts.html`. Source refs — объяснение, rendered evidence перечислено ниже. Confidence: высокий для наблюдаемого эффекта; confidence root указан отдельно.

**Доказательства:**

- [matrix-filled.result.txt](../matrix-filled.result.txt)
- [finish.result.txt](../finish.result.txt)
- [screenshots/contacts-viewport-ru-390.png](../screenshots/contacts-viewport-ru-390.png)
- [current-matrix.result.txt](../current-matrix.result.txt)
- [current-settings.result.txt](../current-settings.result.txt)

**Область исправления:** Связать текст настройки с публичным содержимым контактов; оставить phone/email/social отдельными полями.

**Владелец / зависимости:** Единый публичный text rendering и i18n contract; проверить HTML escaping и длинный текст.

**Следующий шаг:** отдельный repair scope с конкретным планом. [Готовый самостоятельный промпт](SITE-QA-03-repair.txt). Аудит ничего не исправляет.
