# PLAN MOD-QA-13 — зависание при заполнении очереди уведомлений

Новая причина, application patch НЕ применён. P1: при четвёртом уведомлении перестаёт отвечать renderer. Свежий bounded browser recheck: три уведомления рендерятся, четвёртое не возвращает управление за1501ms; закрыт только свой context. Вход уведомлений явно SIMULATED, движок настоящий из текущего checkout; domain writes0. [Native evidence](../toast-capacity-native.js.result.json), [PNG до границы](../screenshots/RED-capacity-three-en-390.png). Это свежая подтверждённая причина, а не ретроспективное доказательство причины исторического AZ UNKNOWN.

Причина: show() выполняет while(children.length>=3) dismiss(oldest). dismiss удаляет узел лишь через220ms, а while синхронно ждёт уменьшения длины: таймер не получает управление. Node VM с контролируемыми DOM/timers исполняет настоящий файл: control первых3 PASS, overflow/уже leaving/rapid overflow3FAIL по timeout250ms. Candidate вне приложения даёт4/4PASS.

Точный scope — **2 файла**:
1. static/admin/js/kidsmap_notifications.js: только capacity branch show(): отменить таймер вытесняемого oldest и синхронно удалить этот узел из container. MAX_TOASTS=3, normal dismiss animation220ms, duration/hover/close/API/modal/локализация не менять.
2. NEW scripts/tests/notifications_toast_capacity.test.cjs: четыре реальные regression проверки исполняемого движка: первые3; четвёртое сохраняет newest3; overflow при leaving не удаляет новые после timer; rapid20 +clearAll. Candidate test в QA, не подключён в scripts/tests до approval.

[Точный JS diff](MOD-QA-13-proposed.diff), [candidate test](toast-capacity-candidate.test.cjs), [unapplied manifest](new-plans-manifest.json). Node control RED1PASS/3FAIL, candidate4PASS, frontend candidate capacity18/18PASS при явно SIMULATED response override. Это feasibility, **не исправление текущего приложения**.

После approval: RED→GREEN4Node checks; настоящий браузер4–20 уведомлений, normal close/clearAll/hover/timer; реальная последовательность публикация↔черновик без ручного очищения очереди RU/AZ/EN×6widths, bounded deadlines, DOM newest3, PNG/console/network, сохранение domain кроме ожидаемых собственных переходов. Совместить с проверками MOD12; модальные dialogs представительно проверить по keyboard. Полный261corpus не повторять. Новый scope отдельно согласовать.
