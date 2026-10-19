# SOCIAL-QA-06 — CLOSED LOCAL, scoped template acceptance

2026-10-17, Asia/Baku. Пользователь одобрил [однофайловый план](../social-qa06-recheck-2026-10-17-pc-r1/IMPLEMENTATION_PLAN.md) сообщением «одобряю». Изменён только **src/catalog/templates/pages/site_reviews.html**. Selected rating теперь представлен одним checked radio; hidden value, visual paint и Tab state согласованы. Сохранены default5, mouse/keyboard activation, hover preview и server payload/range.

SOCIAL01–06 CLOSED LOCAL в записанных scopes; **module09 остаётся OPEN**. SOCIAL07/Activity technical title не исправлялся. Full ACCEPT09/global/production не выполнялись.

## Изменение и итерация

Первоначально применён exact approved candidate: пять role=radio, aria-checked, шкала1 / 5…5 / 5, roving tabindex, choose(), стрелки/wrap/Home/End, reset sync. CSS/sharedJS/controllers/PO/models/routes/schema/test assertions прежние.

Meaningful extended test обнаружил **9resetFAIL**: у hidden input присваивание value меняет также defaultValue/value attribute. После choose2 native form.reset() сохранял2. [Native diagnostic](reset-diagnostic-cli.txt) показывает initial5/default5 → chosen2/default2 → reset2/default2.

В том же одобренном файле добавлен захват исходного defaultRating до первого choose; reset callback использует его. Это необходимая итерация согласованного reset scope, не новый scope. [Initial exact diff](initial-applied.diff), [итоговый diff](applied.diff), [reset iteration](reset-iteration.json). Immutable PLAN/candidate/failed evidence сохранены. Итог отличается от candidate только захватом defaultRating и одним аргументом reset callback; initial one-file SHA не выдаётся за final SHA.

## RED → acceptance

[Свежий PLAN RED](../social-qa06-recheck-2026-10-17-pc-r1/REPORT.md)18cells/198controlPASS/144sourceFAIL использован после проверки всех1021unchanged source и live origins. Не повторялся полный корпус. [RED hash/reference](red-reference.json).

| Группа | Результат и source attribution |
|---|---|
| RU/AZ/EN ×360/390/768/1024/1280/1440 |18cells,198control/144semantic-keyboardPASS,0FAIL на initial approved candidate|
| Extended mouse/стрелки/wrap/Home/End/Tab/reset |9cells,117PASS/9resetFAIL исходного candidate сохранены|
| Targeted reset recheck final source |9cells/27PASS, включая9прежних reset assertions|
| Native SSR/Tab/Space/Enter/POST/reload/range/ACL/CSRF/error |9rows/68PASS на final source|
| Shared home/Place detail/typed Activity/Specialist/Event ×RU/AZ/EN ×390/768/1440 |45cells/270bounded controlsPASS на final source|
| Native PNG |107, включая9retained reset-failure и2SIMULATED transport кадра|
| Captured unhandled pageerrors |0|

18cell matrix и117extended non-reset PASS сохранены с initial source snapshot: последняя коррекция касается только reset. Проверено, что остальные executable statements первоначального candidate прежние; повторены только9затронутых reset cases, затем actual native actions на final source. Не утверждается, что все initial captures сняты после reset-итерации. Assertions не ослаблены, исходные9FAIL не переписаны в PASS.

[Matrix](matrix.json), [initial extended](initial-acceptance-extra.json), [targeted reset](reset-recheck.json), [actual actions](actions.json), [shared](shared.json), [PNG manifest](png-manifest.json), [commands](commands.md), [source final](source-final.json).

## Проверенное поведение

AX tree после Space/Enter содержит radio «3 / 5» checked, остальные unchecked. Group name остаётся translated RU/AZ/EN. Один tabstop, native Tab entry/exit и ShiftTab к selected, Right/Down next wrap5→1, Left/Up previous wrap1→5, Home1/End5. Mouse click/hover preview сохраняют hidden/checked contract; hover не фиксирует другое значение.

На final source SSR до выполнения inline JS отдаёт пять radios с checked5/tabstop5/hidden5. Три свежих fictional автора через настоящий browser click отправили3/1/5: actual multipart FormData rating соответствует selected, ровно один POST, response200/ok, DB pending readback совпадает. Success form.reset() возвращает hidden/checked/tabstop5, composer скрывается. Reload начинает новую форму с прежним default5, DB сохраняет3/1/5, public projection остаётся только2approved.

Actual API rating0/6→400, badCSRF→403, guest POST→401, business writes отсутствуют. Guest rating/composer отсутствует. SIMULATED delay/abort перехвачен до server delivery: busy/disabled, rating2 и текст сохраняются, error feedback/return control, один запрос без auto retry и без записи. Это не реальная внешняя интеграция.

Малый shared smoke подтвердил отсутствие site-specific handler на соседних страницах. Existing Place detail picker нативно выбирает3; typed editors доступны. Наблюдение Activity object(1) в9typedActivity cells относится к SOCIAL07 и записано отдельно от checks, не объявлено исправленным/green. Backend suites NOT RUN: unchanged backend, предыдущие05три existing methods не повторялись; свежие POST/range/ACL/readbacks выполнены непосредственно в браузере/API.

Вручную просмотрены native selected RU390, final reset AZ768 и SIMULATED error EN390. AX/screenshot checks не являются real screenreader/fullWCAG acceptance.

## Изоляция и сохранность

C:\kidsmap, branch codex/module09-transfer-2026-10-16-r1, LOCAL HEAD852938d96764ae315b92859e3651e5ea62054a36; task33-progress e4e05cc213b34e2d771ecb854901bfd016d1db51, index tree881e0c48c7d557c46221beb3b2410a157982f861/staged empty, active_run:NONE. Из1021source изменён только template, остальные1020побайтно прежние, включая dirty SOCIAL03–05/CSS05/PO. .cbmignore/sharedMO сохранены.

Один lead последовательно выполнял frontend/browser/Django contract checks; независимых subagents нет. Новый m09s06-fix-r1-app с repo RO/only own scratch RW, проверенный existing own PLAN06 internal network/fictional PG reused. Own cache/media/private-media/locmem email, cleared env/DJANGO_TESTING1 до setup, no .env/prodcredentials. Fresh sole RU/AZ/EN MO проверены до setup. Separate Chromium155/session social06-pc-fix-r1, loopback33337/hidden proxy; Python3.12.15/Django6.0.2/PG17.11. [Ownership](ownership.json), [runtime](live-final.json), [locales](locale-manifest.json).

Для reload изменённого template после reset correction остановлен только собственный exact runtime.py serve PID, затем own server запущен снова; container/PG/foreign processes не перезапускались. IDs/states всех37entry containers сохранены, добавлен только own app. Foreign restarts0, whole-machine continuity NOT VERIFIED. Все70файлов PLAN06 и6prior packages/manifest/verification сохранены. Guide history дополняется отдельной closure note с reverse-removal SHA. [Preservation](preservation.json).

## Ограничения network/evidence

Primary rating matrix:0HTTP/request failures. Actual actions:1намеренный SIMULATED abort, ожидаемые API400/401/403. Shared smoke:81media404events по9уникальным home gallery images, отсутствующим в own MEDIA_ROOT;36external requests к CDN CSS/maps заблокированы localhost allowlist. Это fixture/external limitations, не полностью зелёная media/network приёмка. Assets не догружались, CSS/медиа страницы не исправлялись. Shared control270PASS не означает PASS внешних карт или home gallery.

NOT RUN: real screenreader/fullWCAG/physical/other browsers, real external integrations/gallery-media acceptance, backend suites/full ACCEPT09/global, SOCIAL07–09/module10, production/commit/push/deploy. Без reset/clean/stash/смены dirty checkout. Следующий этап только отдельный PLAN SOCIAL07 по поручению пользователя.

[Verification](verification.json), [artifact manifest](artifact-manifest.json), [execution checklist](implementation-checklist.md), [next prompt](next-prompt.txt).
