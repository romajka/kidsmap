# ACCESS-QA-01 — дополнение scope: видимый focus submit

**Статус: требуется отдельное одобрение дополнительного CSS-файла.** Основной [план](../access-qa01-recheck-2026-10-14-r1/IMPLEMENTATION_PLAN.md) реализован в login.html: focus lifecycle проверен, backend/reset сохранён. ACCESS-QA-01 пока OPEN: keyboard focus на submit визуально не обозначен.

Исходный план прямо ограничивал приложение login.html и требовал предъявить дополнительный CSS scope, если existing indicator недостаточен. Это тот же ID и его acceptance «видимый focus», дополнительная причина в cascade. Новые ACCESS02/04/05 не входят в scope.

## Подтверждение

[Visible-focus matrix](visible-focus.js.result.json): RU/AZ/EN×360/390/768/1024/1280/1440,54 observations36PASS/18FAIL. Все18FAIL — submit. `:focus-visible` становится true, но outline остаётся none, shadow/background/color не меняются. Native expanded probe проверил также border/transform/filter/::before: изменения отсутствуют. Success и close имеют видимые существующие indicators.

Причина: `static/css/site.css:22797` `.page-account_login .auth-form > .btn` (specificity0,3,0) перекрывает box-shadow общей `.btn:focus-visible` около19387 (0,2,0). Submit находится непосредственно в `.auth-form`; success снаружи формы сохраняет индикатор. Это source/cascade, не ослаблять assertion до одного `matches(':focus-visible')`.

## Точный минимальный diff

**Дополнительно изменить только** `/home/ramin/kidsmap/static/css/site.css`, сразу после `.km-modal-submit-btn` около23642:

```css
#resetPasswordModal .km-modal-submit-btn:focus-visible {
  outline: 3px solid var(--brand-turf);
  outline-offset: 3px;
}
```

Existing token `--brand-turf: #136f38` объявлен в текущем CSS около684. Контур остаётся внутри свободных отступов dialog, отделён от зелёной кнопки белым промежутком3px. ID-scoped правило затрагивает только submit этого modal. Общие кнопки login/reset/registration/admin, default/hover/loading, размеры, layout и тексты не менять. Никаких PO/backend/API/schema/ACL правок.

## Проверка после одобрения

- [ ] Сверить текущие HEAD/WORKTREE/active_run и CSS SHA с entry; сохранить чужие изменения.
- [ ] Применить только указанный CSS rule. Сохранить reviewable diff двух application files: ранее одобренный login.html + этот CSS.
- [ ] Обновить expected source manifest и перезапустить только собственный fix process после argv/cwd/PID проверки; новый sole locale build нужен только если current PO изменился. Общие MO не перезаписывать.
- [ ] Повторить только18 failed submit indicator cells: keyboard Tab, default→focus-visible actual outline/shadow difference, видимый3px contour и PNG, bounds/reload/Tab/Escape/return. Existing36PASS success/close и162focus/324states/54real-reset/3edge/9boundaries сохранять с source provenance; unchanged backend9/full module не повторять.
- [ ] Negative consumers: убедиться source selector scope и native unchanged main login/standalone reset buttons RU390/EN1440. Их исходные стили до/после сопоставить; это affected shared CSS cascade boundary, не весь корпус.
- [ ] Записать commands/exits/PNG manifest/source/locales/preservation; закрыть только ACCESS-QA-01 при GREEN18 и остальных сохранённых evidence. Иначе OPEN/NOT RUN.

Без commit/push/deploy/production. Не занимать active_run, не менять чужие процессы/стенды. ACCEPT-07 остаётся после остальных задач; module08 не начинать.

**Достаточное одобрение:** «Одобряю CSS_SUPPLEMENT_PLAN.md, добавь видимый фокус кнопки отправки для ACCESS-QA-01».
