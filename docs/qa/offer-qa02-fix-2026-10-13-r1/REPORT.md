# OFFER-QA-02 — поля регулярной оплаты и количества

2026-10-13. Root sequential, lead kidsmap-orchestrator. **OFFER-QA-02 CLOSED LOCAL в выполненном scope. Module05 IN PROGRESS.** Независимые исполнители не заявляются. Полная приёмка модуля и другие findings не закрываются.

## 1. Срез и одобрение

Checkout `/home/ramin/kidsmap`, HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`, branch `task33-progress`, dirty WORKTREE сохранён, active_run NONE. Пользователь ответил «дальше» на [конкретный five-file plan](../../superpowers/plans/2026-10-13-offer-qa02-owner-billing-fields.md); выполнен только этот scope. [Entry](entry.json), [verification](verification.json), [runtime](runtime-version-final.json), [exact scoped diff](application.diff), [before/after hashes](source-change-manifest.json).

## 2. Причина и изменение

Owner group editor показывал billing_mode/interval, но не billing_interval_count/billing_cycles/quantity/quantity_unit. Поэтому recurring/month с положительной ценой отвергался422, installment тоже нельзя было завершить. Серверные validators и constraints правильные и не менялись.

Добавлены4 controls в существующую grid: recurring показывает период/count, installment — cycles, one_time скрывает оба. До сохранения переключение сохраняет набранные значения; после реального сохранения неактивные billing values очищаются прежним canonical clean. Quantity/unit доступны вместе; нет фиктивных count1/quantity1/unitlesson defaults. Список14 единиц берётся из PricingPlan.QUANTITY_UNIT_CHOICES на сервере, не дублируется в JS. Новые4 подписи explicit RU/AZ/EN через существующий ui_copy. Только Час/Месяц/Смена в AZ/EN PO исправлены и сняты fuzzy (6 entries).

Точные5 файлов: owner_place_offerings.js, offering_editor_choices в pricing_plans.py, ui_copy в permanent_place_wizard.py, AZ/EN django.po. Repair01 writer сохранён. Прежние грязные изменения в этих файлах защищены before hashes и точным diff от входного WORKTREE: старые PO bytes взяты из неизменённой owned previous build source и совпадают по SHA; source reconstruction также совпадает с entry SHA. Нет CSS/model/schema/publication/ACL/CAS/CI/dependency/other-locale fixes.

## 3. Изоляция / locale

Собственный новый profile `offer-qa02-fix-2026-10-13-r1`: отдельные PostgreSQL container/volume/DB/user/loopback ports, cache/media/private-media/LocMem email/cookies; новые fictional actors и23 Place/Activity/Group/tariff prerequisites. Старые стенды не остановлены/не перенастроены, active_run не присвоен. Актуальные process/port/source receipts — server.json/verification.json; исторические чужие параметры не использованы.

Runtime чистит env, DJANGO_TESTING=1 до setup, не импортирует manage.py/.env, socket connect/connect_ex только к own PG. External browser requests явно blocked (fonts/CDN/maps); реальные интеграции NOT RUN. Собственный current PO build helper/native msgfmt, sole LOCALE_PATHS, startup verify source hashes. [Manifest](locale-manifest.json). Старые common MO/previous compiled profiles не перезаписаны. Secrets only ignored scratch0600, без production данных/credentials.

## 4. RED → GREEN / backend

Fresh [recheck](../offer-qa02-recheck-2026-10-13-r1/REPORT.md): actual owner recurring/installment POST422 и4 отсутствующих controls. Positive rendered regression [RED](positive-red.result.json): expected count control1, actual0, behavioral FAIL (CLI exit0 не считается PASS). [GREEN](positive-green.result.json): тот же selector/expected1, actual1; изменена только phase attribution/fictional fixture routing. Не заменяет дальнейшие persistence проверки.

Ровно2 existing focused backend methods, [native0/2 PASS](targeted-guards.txt), [exact argv/exit](targeted-guards.command.json): target_scoped_roundtrip_and_foreign_ids; trial_fee_and_membership_preserve_regular_headline. Они защищают canonical contract/IDs/ownership/public recurring pricing, а не объявлены failing before UI patch. Старые assertions не изменены. Предыдущие38/whole module/project suites не повторены.

## 5. Реальный браузер и данные

RU/AZ/EN×360/390/768/1024/1280/1440:4 controls, correct new labels/unit options, mode visibility, keyboard Tab skips hidden cycles, unsaved mode toggle preserves count/cycles. Native recurring month/count2/quantity8/lesson draft save→reload; installment cycles3 save→reload; one_time quantity2/hour save→reload clears interval/count/cycles; submit→native moderation approval→public90/owner reload. До approval public20 остаётся. На390 каждого языка дополнительно native count0/cycles0 и empty quantity+unitlesson reject422/input retained; count1 успешно сохраняется/reopens. Никаких checked переходов через ORM.

Native создание нового тарифа через «Добавить тариф», явный membership/month/count1/quantity8/lesson, draft→reload→submit→approve→reload: [7 PASS rows](new-browser.result.json). [READ ONLY](new-readback.json): новый ID создан, исходный tariff20/ID сохранён; новый membership90/count1/quantity8/lesson опубликован. Это отдельный fiction fixture, не ORM checked transition.

Отдельные3 fictional cells: quantity/unit blank pair native save/reload/approve, recurring count1 remains. Actual affected shared consumer — зарегистрированный Place admin nested pricing editor, не отсутствующий standalone PricingPlan admin: RU/AZ/EN rendering/visibility,360/1440 geometry, native staff installment3/quantity2/hour save→approve→reload. Проверка также подтверждает server model unit labels при реальном default LANGUAGE_CODE=az без RU fallback regression.

[Main](browser.result.json), [optional](optional-browser.result.json), [admin](admin-browser.result.json), [focus hit-test](focus.result.json), [console/network](console.result.json).483 accepted assertion rows, не483 самостоятельных tests.94 native PNG originals ([manifest](png-manifest.json)); derived [overview](recurring-overview.jpg). Native field fragment screenshots могут включать фиксированные header/footer; отдельные viewport keyboard PNG и elementFromPoint проверки доказывают, что focus не перекрыт. EN390 native fragment и focused viewport просмотрены. App pageerrors0; console probe no unexpected errors; resource ERR_FAILED коррелирует с явно blocked external requests. Негативные422 main — ожидаемые validation, не network regressions.

READ ONLY10s statement/2s lock [main](readback.json), [extra](extra-readback.json):18 main live rows one_time/quantity2/hour/90, plan/group IDs retained, group active, source version2; revision versions5 или6 соответствуют точному числу успешных saves/review и не выросли от rejected requests. Optional3 live rows recurring/count1/quantitynull/unitempty; admin live installment3/quantity2/hour. Не выгружены production records.

## 6. Сохранность и provenance

Final verifier сверяет все прежние nonignored files, exact source5 before/after, отдельно ignored common MO, HEAD/branch/active_run, current process argv/startup/disk, own PG loopback binding и actual own secret values в assigned text artifacts. Предыдущие source changes/REPORT/index/transfer inputs сохранены. Foreign process control0. Это не universal secret audit и не текущая проверка чужих/исторических runtimes.

## 7. Пределы / открытые findings

OFFER-QA-03–08 остаются6 историческими OPEN для fresh recheck. OFFER-QA-09 остаётся OPEN baseline partial review. Полная локализация всех прежних tariff enums не входит в02: в EN viewport уже существующие role/billing option captions остаются русскими из-за других fuzzy/source entries; evidence retained for locale recheck06, эти msgids не исправлялись. Не заявлен PASS всей формы/всех переводов, исправление error focus03 или partial moderation09.

Full ACCEPT-05/global corpus/no-label wrapper/real integrations/physical devices/Firefox/WebKit/screenreader/production/commit/push/deploy NOT RUN. Показанные UI ширины — Chromium viewports. Scope02 исправлен и принят по текущему dirty LOCAL source, не HEAD-only/production.

## 8. Команды

Exact commands/exits: commands.jsonl, targeted-guards.command.json, readonly-readback.command.json, extra-readback.command.json, locale-final-verify.command.json, final-verification.command.json; browser driver result artifacts имеют собственные statuses отдельно от CLI exit. Setup/check/migrations только own disposable stand. Backend guards один прогон2 cases, без full repeats. [Commands](COMMANDS.md).

## 9. Handoff

OFFER-QA-01–02 CLOSED LOCAL в scoped evidence. Module05 IN PROGRESS. Дальше по порядку [PLAN OFFER-QA-03](next-prompt.txt): error summary направляет фокус не в поле цены. Другие findings не реализуются автоматически. Полная module acceptance один раз после его repairs, общий проектный прогон позже по договорённости.
