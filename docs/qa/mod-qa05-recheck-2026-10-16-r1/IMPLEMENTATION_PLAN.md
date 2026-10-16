# MOD-QA-05 — вернуть фокус на исходную кнопку строки

**CONFIRMED OPEN. Новый scope: один файл, одна строка. Approval pending; diff не применён.**

**Goal:** после Escape/отмены подтверждения снятия с публикации фокус возвращается на видимую кнопку «ещё» той же строки.

**Architecture:** перед открытием confirmation сделать уже сохранённый row trigger активным элементом. Существующий kmModal сам запоминает его и возвращает фокус при закрытии с действующими generation/visibility guards. Общий focus engine в текущем исходнике уже исправлен; повторно его не переписывать.

**Tech Stack:** существующий vanilla JS/DOM focus API и текущий kmModal. Новых библиотек/PO/схем/зависимостей нет.

**Spec:** guide PLAN MOD-QA-05 и исторические findings/repair-prompts MOD-QA-05. Свежий REPORT/native-recheck.js.result.json этого каталога имеет приоритет по фактическому поведению. Авторизация MOD04 этот patch не разрешает. После прямого approval выполнить в этом чате, без нового согласования того же scope; новые причины/существенное расширение согласовать отдельно.

## Свежая причина

RU/AZ/EN×390/1440:6cells,26observations. **20controlPASS/6sourceFAIL**. Начальный фокус на настоящей HTML-кнопке и wrap Tab/ShiftTab работают во всех6cells. После Escape фокус — BODY во всех6cells; исходный trigger остаётся видимым и доступным pointer hit. Все подтверждения отменены, domain unchanged.

Текущий `kidsmap_notifications.js:getFocusableElements` уже использует `a[href]`, исключает отрицательный tabindex/disabled/hidden; `focusWhenVisible` повторяет initial focus до видимости. Исторический SVG-use/initial-focus FAIL больше не воспроизводится. Эти исправления сохранить.

В `static/admin/js/kidsmap_place_changelist.js`, row-action click handler сохраняет `var trigger = activeMoreBtn`, затем вызывает `closeRowActions()`, скрывающий активный пункт меню. До `kmModal.confirm` фокус оказывается BODY/скрытой кнопкой. `kmModal.show` запоминает `document.activeElement`; при закрытии скрытый пункт не проходит существующий visibility guard. Нужен видимый исходный trigger, а не новый modal-engine API.

## Точный файл и diff

Только **`static/admin/js/kidsmap_place_changelist.js`**, row action click handler, сразу после `closeRowActions()` перед `function escapeHtml`:

```diff
         closeRowActions();
+        trigger.focus({preventScroll: true});

         function escapeHtml(str) {
```

Готовый [proposed.diff](proposed.diff), [source/candidate hashes](proposal-manifest.json). Сейчас app file совпадает с исходным hash; candidate не применён. Существующий trigger capture, публикационные условия/AJAX/loading/undo/server endpoints и focus engine сохраняются. Эта же строка обеспечивает корректный opener для confirmation удаления из того же handler.

Backend/test source files не нужны: регрессия проверяется настоящим browser script через воспроизведение BODY→GREEN, не текстовым assert строки JS. Новые QA scripts/JSON/PNG/отчёт находятся в отдельном fix-run; existing assertions не менять.

## Выполнение после approval

- [ ] **1. Snapshot/изоляция.** Проверить checkout/HEAD/branch/dirty/active_run, существующие процессы/контейнеры и hashes. Свой актуальный профиль использовать только после ownership/source/DB/cache/media/private-media/email/locale verification; production/env не читать. Вымышленные записи, DJANGO_TESTING=1, внешние обращения blocked. Текущие RU/AZ/EN PO собрать отдельным build_isolated_locales.py, manifest до setup и единственный LOCALE_PATHS, shared MO не трогать. Без пересоздания чужих стендов.
- [ ] **2. Meaningful RED.** До patch повторить только исходный trigger на собственной fictional опубликованной строке: native more→Enter→снять с публикации→initial focus/Tab/ShiftTab→Escape. BODY вместо trigger — ожидаемый sourceFAIL, контроль initial/trap должен PASS. Сохранить raw JSON и отдельный RED PNG; не перезаписывать GREEN.
- [ ] **3. Применить ровно одну строку.** Проверить source_sha256 из актуального snapshot и единственное совпадение контекста proposed.diff. При drift адаптировать только согласованный handler; новую причину/расширение не включать молча. Не менять общий notifications focus engine и MOD06 i18n.
- [ ] **4. Targeted native GREEN.** Опубликованные Place в RU/AZ/EN×360/390/768/1024/1280/1440, sidebar в доступном состоянии: actual row opener keyboard→warning confirmation→начальный фокус на HTML control→wrap Tab/ShiftTab→Escape и Cancel→возврат фокуса на тот же видимый trigger, видимый focus, viewport hit; reopen/reload. Снимать after-close после штатного удаления backdrop220ms, а не до завершения lifecycle. Return-focus не доказывать одной проверкой activeElement без видимости/hit.
- [ ] **5. Только representative shared guards.** Тот же row-handler danger/delete confirmation — отмена/Escape на390/1440 в каждом языке; никакого реального удаления. Один прямой row-view/link переход и menu Escape как незатронутые controls. Существующие initial focus, sprite и warning/danger control assertions сохранять. Один явно SIMULATED fallback-icon case допускается только как дополнительная проверка существующего renderer, отдельно от настоящих пользовательских flows. Primary/shared engine не изменяется; полный старый modal/CSS/search/sort/columns корпус повторять не надо. Если обнаружится его новая причина — отдельно PLAN, не расширять этот однофайловый scope.
- [ ] **6. Финальная сверка.** Новый snapshot/source/свежие MO/domain before-after fingerprint. Все confirmation в проверке отменяются: это проверка focus/cancel, не тест реального снятия публикации/удаления. Данные должны остаться неизменными. Node syntax/diff checks, semantic JSON gate, exact commands/exits/counts, PNG hash manifest, limits/NOT RUN и сохранность foreign WORKTREE/active_run/стендов.
- [ ] **7. Закрыть только доказанный MOD05 LOCAL.** Обновить статус со ссылкой, старые отчёты сохранить. MOD06–08 отдельные планы; полный ACCEPT08 один раз после завершения задач. Global/production/commit/push/deploy/module09 запрещены.

## Самопроверка

Подтверждён MOD-QA-05, текущая оставшаяся причина только return-focus. Однофайловый/однострочный diff готов; native failing test уже показывает точный эффект. Initial focus/trapping не переисправляются по старому FAIL. План соответствует правилу пользователя «точечные и примерочные проверки сейчас; весь модуль потом». Approval и postpatch GREEN пока отсутствуют.
