# SITE-QA-04 — Настройки CTA и placeholder главной игнорируются

**OPEN / P2 / LOCAL C:\kidsmap / module10-2026-10-10-r1 / 2026-10-10.** Классификация: pre-existing LOCAL application failure. Execution: /root sequential, свежие native Chromium и own isolated DB. Production UNKNOWN. Исполнитель аудита не менял application sources/существующие assertions; чужой drift зафиксирован в [SOURCE-DRIFT](../SOURCE-DRIFT.md).

**Роль:** admin / guest. **URL/endpoint:** `/admin/catalog/sitebrandingsettings/1/change/; /ru/; /; /en/`.

**Шаги:** Сохранить разные home_cta_text_* и home_search_placeholder_* через UI. Reload админки, затем главная во всех 18 cells.

**Ожидание:** Сохранённые локализованные CTA и placeholder выводятся на главной.

**Факт:** По 18 FAIL на CTA и placeholder; вместо QA10-маркеров hardcoded тексты. Title/subtitle/search-label и декор реагируют на настройки.

**Перепроверка WORKTREE:** Supplemental native process8825/8826 started from current-snapshot.json after recorded foreign source drift. Module10 relevant handlers/templates/MO remain unchanged; own reports preserve entry evidence. SITE-QA-01 current recheck is GET only; upload/delete proof earlier, identical handler hashes, no new security mutation.

**Приоритет и эффект:** P2: два опубликованных поля редактора не влияют на основной публичный UI.

**Первопричина / гипотеза:** Подтверждено: HomeController формирует hero_cta_text/hero_search_placeholder, шаблон использует literals вместо этих context values.

**Source:** `src/catalog/controllers/home_controller.py:119`; `src/catalog/controllers/home_controller.py:122`; `src/catalog/templates/pages/home.html:43`; `src/catalog/templates/pages/home.html:261`. Source refs — объяснение, rendered evidence перечислено ниже. Confidence: высокий для наблюдаемого эффекта; confidence root указан отдельно.

**Доказательства:**

- [matrix-filled.result.txt](../matrix-filled.result.txt)
- [settings.result.txt](../settings.result.txt)
- [screenshots/home-viewport-ru-390.png](../screenshots/home-viewport-ru-390.png)
- [current-matrix.result.txt](../current-matrix.result.txt)
- [current-settings.result.txt](../current-settings.result.txt)

**Область исправления:** Связать CTA/placeholder с context, сохранить defaults и выбранный язык без копирования fallback в сохранённый перевод.

**Владелец / зависимости:** HomeController trimming/default policy; 18 native cells после save/reload.

**Следующий шаг:** отдельный repair scope с конкретным планом. [Готовый самостоятельный промпт](SITE-QA-04-repair.txt). Аудит ничего не исправляет.
