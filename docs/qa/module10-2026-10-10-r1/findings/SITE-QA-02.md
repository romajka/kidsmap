# SITE-QA-02 — AZ-тексты «О проекте» и пустого каталога сохраняются, но не отображаются

**OPEN / P2 / LOCAL C:\kidsmap / module10-2026-10-10-r1 / 2026-10-10.** Классификация: pre-existing LOCAL application failure. Execution: /root sequential, свежие native Chromium и own isolated DB. Production UNKNOWN. Исполнитель аудита не менял application sources/существующие assertions; чужой drift зафиксирован в [SOURCE-DRIFT](../SOURCE-DRIFT.md).

**Роль:** admin / guest. **URL/endpoint:** `/admin/catalog/siteaboutsettings/1/change/; /admin/catalog/siteemptystatesettings/1/change/; /about/; /catalog/?q=QA10-NO-MATCH`.

**Шаги:** Через админку сохранить разные QA10-маркеры RU/AZ/EN для about_text и empty_results_text. Reload показывает сохранённые AZ-значения. Открыть AZ about и каталог без совпадений на всех шести ширинах.

**Ожидание:** Вывод сохранённого AZ-текста; default только при пустом поле.

**Факт:** Во всех 6 AZ cells обе публичные страницы показывают захардкоженный default. RU/EN тексты выводятся. AZ перевод действительно сохранён, это не fallback.

**Перепроверка WORKTREE:** Supplemental native process8825/8826 started from current-snapshot.json after recorded foreign source drift. Module10 relevant handlers/templates/MO remain unchanged; own reports preserve entry evidence. SITE-QA-01 current recheck is GET only; upload/delete proof earlier, identical handler hashes, no new security mutation.

**Приоритет и эффект:** P2: редактор не управляет основным AZ содержимым.

**Первопричина / гипотеза:** Подтверждено: AZ-ветка шаблона стоит перед проверкой site_about_text/site_empty_results_text.

**Source:** `src/catalog/templates/pages/about.html:76`; `src/catalog/templates/catalog/place_list.html:967`. Source refs — объяснение, rendered evidence перечислено ниже. Confidence: высокий для наблюдаемого эффекта; confidence root указан отдельно.

**Доказательства:**

- [matrix-filled.result.txt](../matrix-filled.result.txt)
- [finish.result.txt](../finish.result.txt)
- [screenshots/filled-az-390-_about_.png](../screenshots/filled-az-390-_about_.png)
- [current-matrix.result.txt](../current-matrix.result.txt)
- [current-settings.result.txt](../current-settings.result.txt)

**Область исправления:** Приоритет сохранённого локализованного значения над default для обоих шаблонов; сохранить языковые fallback правила.

**Владелец / зависимости:** SiteSettings i18n helpers/context; отдельные пустое/заполненное AZ и RU/EN regressions.

**Следующий шаг:** отдельный repair scope с конкретным планом. [Готовый самостоятельный промпт](SITE-QA-02-repair.txt). Аудит ничего не исправляет.
