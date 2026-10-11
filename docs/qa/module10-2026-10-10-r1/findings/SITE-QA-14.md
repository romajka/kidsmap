# SITE-QA-14 — Несохранённый ввод settings теряется при обрыве POST

**OPEN / P2 / LOCAL C:\kidsmap / module10-2026-10-10-r1 / 2026-10-10.** Классификация: SIMULATED transport, confirmed LOCAL input-recovery failure. Execution: /root sequential, свежие native Chromium и own isolated DB. Production UNKNOWN. Исполнитель аудита не менял application sources/существующие assertions; чужой drift зафиксирован в [SOURCE-DRIFT](../SOURCE-DRIFT.md).

**Роль:** admin. **URL/endpoint:** `/admin/catalog/sitefootersettings/1/change/`.

**Шаги:** Заполнить footer_email новым вымышленным значением. Через browser route.abort оборвать native form POST до сервера. После browser error нажать Back. Сверить history и DB.

**Ожидание:** Старое значение DB сохраняется; введённое значение можно восстановить и повторить сохранение без ложного успеха.

**Факт:** DB сохраняет старый edited10@example.invalid, ложного save нет. Chromium показывает chrome-error, Back ведёт на account/profile (admin form GET заменён в history), введённый текст отсутствует. Повторный независимый контекст подтверждает результат.

**Перепроверка WORKTREE:** Supplemental native process8825/8826 started from current-snapshot.json after recorded foreign source drift. Module10 relevant handlers/templates/MO remain unchanged; own reports preserve entry evidence. SITE-QA-01 current recheck is GET only; upload/delete proof earlier, identical handler hashes, no new security mutation.

**Приоритет и эффект:** P2 в проверенном сценарии: пользователь теряет несохранённый ввод. Это результат SIMULATED transport, не доказательство production incident.

**Первопричина / гипотеза:** Подтверждён механизм history на simulated transport; SSR form navigation без draft persistence/recovery. Реальный сетевой разрыв/серверный отказ не выполнялся, другие браузеры не проверены.

**Source:** `src/catalog/templates/admin/catalog/shared_settings_change_form.html`. Source refs — объяснение, rendered evidence перечислено ниже. Confidence: высокий для наблюдаемого эффекта; confidence root указан отдельно.

**Доказательства:**

- [finish.result.txt](../finish.result.txt)
- [network-proof.result.txt](../network-proof.result.txt)
- [screenshots/network-entered-final.png](../screenshots/network-entered-final.png)
- [screenshots/network-error-final.png](../screenshots/network-error-final.png)
- [screenshots/network-back-final.png](../screenshots/network-back-final.png)
- [current-network.result.txt](../current-network.result.txt)

**Область исправления:** Предложить минимальный план восстановления ввода/повторной отправки для settings SSR form. Не обещать save до ответа сервера; исключить secret fields из возможного локального draft.

**Владелец / зависимости:** Frontend-admin form lifecycle/cache/history; injected abort + reload/Back and successful-save cleanup; реальный disconnect отдельная проверка.

**Следующий шаг:** отдельный repair scope с конкретным планом. [Готовый самостоятельный промпт](SITE-QA-14-repair.txt). Аудит ничего не исправляет.
