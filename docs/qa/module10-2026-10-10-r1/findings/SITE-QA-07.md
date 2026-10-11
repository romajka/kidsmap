# SITE-QA-07 — EN/AZ подписи переключателей остаются RU из-за существующих .mo

**OPEN / P2 / LOCAL C:\kidsmap / module10-2026-10-10-r1 / 2026-10-10.** Классификация: pre-existing LOCAL locale/environment artifact failure. Execution: /root sequential, свежие native Chromium и own isolated DB. Production UNKNOWN. Исполнитель аудита не менял application sources/существующие assertions; чужой drift зафиксирован в [SOURCE-DRIFT](../SOURCE-DRIFT.md).

**Роль:** admin. **URL/endpoint:** `/admin/catalog/sitevisibilitysettings/1/change/`.

**Шаги:** Открыть EN/AZ settings во всех ширинах. Сравнить rendered labels, runtime gettext и raw .mo с существующими .po.

**Ожидание:** EN/AZ переводы трёх подписей публичных разделов.

**Факт:** 12 native cells показывают русские labels. В .po переводы есть; raw .mo/runtime возвращают русский msgid. Существующие .mo не компилировались и соответствуют entry WORKTREE.

**Перепроверка WORKTREE:** Supplemental native process8825/8826 started from current-snapshot.json after recorded foreign source drift. Module10 relevant handlers/templates/MO remain unchanged; own reports preserve entry evidence. SITE-QA-01 current recheck is GET only; upload/delete proof earlier, identical handler hashes, no new security mutation.

**Приоритет и эффект:** P2: основные section controls не локализованы на двух языках; изменение settings.source не исправляет runtime без locale build.

**Первопричина / гипотеза:** Подтверждено: source/runtime artifact mismatch для данных msgid. Нельзя выводить отсюда состояние production locale build.

**Source:** `locale/en/LC_MESSAGES/django.po:22787`; `locale/az/LC_MESSAGES/django.po:22945`; `locale/en/LC_MESSAGES/django.mo`; `locale/az/LC_MESSAGES/django.mo`. Source refs — объяснение, rendered evidence перечислено ниже. Confidence: высокий для наблюдаемого эффекта; confidence root указан отдельно.

**Доказательства:**

- [mo-evidence.json](../mo-evidence.json)
- [matrix-filled.result.txt](../matrix-filled.result.txt)
- [current-matrix.result.txt](../current-matrix.result.txt)
- [current-settings.result.txt](../current-settings.result.txt)

**Область исправления:** Установить/проверить проектный reproducible locale build для точного checkout; согласовать объём обновления compiled artifacts. Не менять assertions для зелёного результата.

**Владелец / зависимости:** Locale pipeline и release reviewer; UI labels после реального build в отдельном authorized repair scope.

**Следующий шаг:** отдельный repair scope с конкретным планом. [Готовый самостоятельный промпт](SITE-QA-07-repair.txt). Аудит ничего не исправляет.
