# SITE-QA-08: перенос уведомления после сохранения — Implementation Plan

> **For agentic workers:** выполнять inline на новом собственном стенде; этот followup ещё не одобрен и НЕ ПРИМЕНЁН. Сохранить основной пакет и весь предыдущий dirty WORKTREE.

**Goal:** завершить responsive-часть SITE08: уведомление об успешном сохранении не расширяет страницу телефона.

**Architecture:** добавить одно правило в существующий stylesheet настроек. `body:has(.km-settings-form-page) #content > .alert` ограничивает действие страницами общего шаблона и только стандартными уведомлениями Jazzmin; вернуть им обычный поток текста и перенос длинной ссылки на объект. Формы ошибок `.km-place-form-alert`, backend redirects, права, поля и соседние редакторы не меняются.

**Tech Stack:** текущие CSS/Jazzmin/Django/Chromium, без новых зависимостей.

**Spec:** [родительский REPORT](../REPORT.md), [прототип](../evidence/browser-followup-prototype.json), [точный diff](proposed.diff), [SHA](candidate-manifest.json). Native RU360 `_continue`: document366 → temporary CSS360 → rollback366;14контролей PASS. Это не applied-source GREEN.

## Global Constraints

- Применён основной двухфайловый patch SITE08. Template SHA `e3791aa31eba0d31ecd14ce559cfca8745185b9ba3950dcc4aa92d224e5cbe29`, текущий CSS `baf70032e5b918a783c136b4fa9449855c6eafb18df13f015a7ff144c7367f83`. Новый CSS-кандидат `074e3405a541bc9c0ce6eaefea013388d48e810d2d9a48eb3a4bb7c940d7474c`.
- Разрешение требуется на этот новый конкретный diff; исходный одобренный diff применён без уточнений. Ни одного дополнительного app изменения в основном пакете нет.
- Только один application file: `static/admin/css/pages/kidsmap_settings_forms.css`. Не менять глобальный shell, template, JS/backend/model/schema/PO/права.
- DJANGO_TESTING=1; env очищен до setup, свежие собственные DB/cache/media/email/locales, внешние интеграции отключены. Текущий33580 и все прежние стенды не перезапускать/очищать.
- Без commit/push/deploy/production/reset/clean/stash/index изменений; active_run NONE/shared MO/.cbmignore/старые пакеты сохраняются.

## Task 1: завершить responsive saved-message state

**Files:** Modify `static/admin/css/pages/kidsmap_settings_forms.css` — добавить в конец только следующий блок. Evidence/test scripts — в новом уникальном `docs/qa/site-qa08-followup-fix-<дата>-<run>/`, без изменения sealed родительского пакета.

**Interfaces:** использует уже существующие marker на body descendant и Jazzmin `.alert` — direct child `#content`. Объектная ссылка, close button, icon и translated message остаются прежними. Не добавляет alternative submit или backend source of truth.

- [ ] **Step 1: свежий snapshot и native RED.** Сверить1033source SHA/refs/index/старые manifests, CSS base SHA выше; при drift перепроверить затронутые выводы. Создать новый owned runtime и synthetic fixtures, подтвердить1033sources/current3locale до django.setup. На RU360 через native branding save установить `brand_name=qa_ru_360`, затем через native footer `_continue` установить `footer_email=qa_ru_360_continue@example.invalid`. После load/завершения sidebar initialization/500ms проверить doc.scrollWidth>360 и actual `.alert` display:flex, сохранить PNG/geometry. Native restore исходных scalar values; четыре ожидаемых synthetic LogEntry явно учесть. Образец процесса — parent browser-followup-prototype.js; удалить из копии только секцию временной style injection/rollback, заменить её actual-source expectation document≤viewport для одинакового RED/GREEN теста; проверка должна сначала FAIL.

- [ ] **Step 2: применить exact one-file diff.** Проверить `git apply --check <absolute followup/proposed.diff>`, base/candidate SHA, сохранить CRLF. Применить только:

```css
/* Jazzmin messages mix anonymous text and an object link; keep normal wrapping. */
body:has(.km-settings-form-page) #content > .alert {
  display: block;
  min-width: 0;
  max-width: 100%;
  overflow-wrap: anywhere;
}
```

Не использовать overflow-x:hidden. SHA результата должен совпасть с candidate-manifest; остальные1032source files сохранить. Перезапустить только новый собственный source-loaded сервер, получить CSS200/точный content SHA, повторить тот же native тест без injected styles/classes/transport.

- [ ] **Step 3: native acceptance.** Saved-message cases AZ/RU/EN ×360/390/768/1024/1280/1440 с коротким и длинным unbroken brand name/email. `_continue` и `_save` сохраняют точное значение, есть один LogEntry/операция, сообщение/ссылка/close видимы и помещаются, document≤viewport. Close через Tab/Enter работает, сообщение не перекрывает поля. Для `_save` отдельно сохранить известную цепочку SITE22; не изменять её/не называть exit-semantic GREEN. Проверить standard9form layout matrix, readonly catalogue hidden mobile controls, native file/JSON errors и связанный summary-anchor focus, Place/Event отсутствие settings stylesheet/marker и неизменную геометрию. Использовать corrected central error observation из родителя: Jazzmin намеренно скрывает duplicate `.errorlist.d-none`; не объявлять такой hidden list продуктовым отсутствием ошибки.

Native public logo/footer/gallery readback повторить после соответствующего save, если эти значения затрагиваются fixture. Public homepage district options строятся по опубликованным Place; не выдавать наличие такого option за доказательство потребления districts_json. Backend105 методов уже прошли на родительском Python/source snapshot; это исторический baseline для нового CSS run, не новый PASS. Дополнительные backend прогоны — при source drift/новом поводе; собственная изоляция остаётся обязательной.

- [ ] **Step 4: зафиксировать результат.** Сохранить actual-source RED→GREEN, native commands/counts/exit, screenshots, exactdiff/SHA и manifests. Проверить сохранность всего родительского sealed package/его prior packages/MO/index/refs/activeNONE/чужих runtimes. Только при полном responsive acceptance закрыть SITE08 LOCAL; SITE22/P3, SITE20/SITE11 и остальные пункты остаются OPEN. Module10 full acceptance pending. Append-only guide/MASTER, без commit/push/deploy.

## Self-review

Причина показана в актуальном source templates/admin/base.html:232–255 и native diagnostics: message содержит anonymous flex text вокруг ссылки на объект. Новый scoped normal-flow rule устраняет этот механизм; не маскирует контент и не ограничивает generic alerts других страниц. Prototype снят и откатился366px. Других application files или изменений save/navigation этот план не разрешает.

**Approval:** one-file followup/proposed.diff, SHA `da5563bc9a2e2d75f6cdf8ffa2b7c1992c440ff2ccbc0d5a2eb8678cd77dde99`. Основание для отдельного решения — AGENTS.md: «Future implementation requires a concrete plan and user approval for its scope»; дополнительное правило отсутствует в уже применённом согласованном diff.
