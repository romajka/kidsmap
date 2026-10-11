# SITE-QA-05 — Загруженные hero PC/mobile главной не выводятся

**OPEN / P2 / LOCAL C:\kidsmap / module10-2026-10-10-r1 / 2026-10-10.** Классификация: pre-existing LOCAL application integration failure. Execution: /root sequential, свежие native Chromium и own isolated DB. Production UNKNOWN. Исполнитель аудита не менял application sources/существующие assertions; чужой drift зафиксирован в [SOURCE-DRIFT](../SOURCE-DRIFT.md).

**Роль:** admin / guest. **URL/endpoint:** `/admin/catalog/sitegalleryimage/; /admin/catalog/sitebrandingsettings/1/change/; /ru/; /; /en/`.

**Шаги:** Загрузить вымышленные разные home_hero_image/home_hero_mobile_image через native file chooser. Reload подтверждает файлы. Открыть главную на mobile/PC; проверить DOM src/background и rendered screenshot.

**Ожидание:** Обозначенные в медиаредакторе PC/mobile изображения используются соответствующим публичным hero.

**Факт:** Оба файла сохраняются, но ни одна из 18 публичных cells не использует их. Главная остаётся со статическими фото.

**Перепроверка WORKTREE:** Supplemental native process8825/8826 started from current-snapshot.json after recorded foreign source drift. Module10 relevant handlers/templates/MO remain unchanged; own reports preserve entry evidence. SITE-QA-01 current recheck is GET only; upload/delete proof earlier, identical handler hashes, no new security mutation.

**Приоритет и эффект:** P2: успешная загрузка не меняет публичный результат; редактор вводит в заблуждение.

**Первопричина / гипотеза:** Подтверждено для home hero: обновлённый шаблон не потребляет эти SiteSettings fields, несмотря на действующий редактор. Не утверждается, что все остальные image fields также не работают.

**Source:** `src/catalog/domain_admin/site.py:653`; `src/catalog/models/site.py:127`; `src/catalog/templates/pages/home.html`. Source refs — объяснение, rendered evidence перечислено ниже. Confidence: высокий для наблюдаемого эффекта; confidence root указан отдельно.

**Доказательства:**

- [settings.result.txt](../settings.result.txt)
- [matrix-filled.result.txt](../matrix-filled.result.txt)
- [screenshots/home-viewport-en-1440.png](../screenshots/home-viewport-en-1440.png)
- [current-matrix.result.txt](../current-matrix.result.txt)
- [current-settings.result.txt](../current-settings.result.txt)

**Область исправления:** Согласовать конкретно home hero image PC/mobile с текущей композицией и редактором. Перед изменением UI предложить точный план; не удалять поля или DB структуры по отсутствию references.

**Владелец / зависимости:** KidsMap UI design и product contract; no-image fallback, mobile/PC, reload/cache.

**Следующий шаг:** отдельный repair scope с конкретным планом. [Готовый самостоятельный промпт](SITE-QA-05-repair.txt). Аудит ничего не исправляет.
