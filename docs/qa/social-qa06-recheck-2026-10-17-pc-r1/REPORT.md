# SOCIAL-QA-06 — CONFIRMED OPEN/P2, PLAN COMPLETE

2026-10-17, Asia/Baku. Свежая проверка подтверждает отсутствие программного selected state в звёздах оценки сайта. **Application changes0; implementation approval PENDING** на новый scope: только src/catalog/templates/pages/site_reviews.html. [План](IMPLEMENTATION_PLAN.md), [полный candidate](candidate-site_reviews.html), [unapplied diff](proposed.diff), [hashes](candidate-manifest.json).

Source classification: существующая причина текущего WORKTREE, не environment/QA-harness failure. Native Space/Enter меняют hidden rating=3 и рисуют три active stars; accessibility tree содержит пять обычных buttons1…5 без selected radio. Реальный screenreader NOT RUN.

## Снимок

C:\kidsmap, branch codex/module09-transfer-2026-10-16-r1, LOCAL HEAD852938d96764ae315b92859e3651e5ea62054a36; task33-progress=e4e05cc213b34e2d771ecb854901bfd016d1db51, index tree881e0c48c7d557c46221beb3b2410a157982f861, staged diff empty. Сохранён dirty approved SOCIAL03–05.1021source/PO совпадают с final SOCIAL05; active_run:NONE/sharedMO/.cbmignore прежние. [Entry](source-entry.json), [final](source-final.json), [preservation](preservation.json).

SOCIAL01–05 сохраняют scoped LOCAL closures; module09 OPEN. ADJ-ACTIVITY-TITLE из05 соответствует историческому SOCIAL07, не отдельное новое исправление; в этом06run оно не перепроверялось и не менялось. SOCIAL07–09/full ACCEPT09/global автоматически не запускались. Один lead выполнял канонические frontend/browser/accessibility checks последовательно, без независимых subagents.

## Source discovery

Graph C-kidsmap ready/rootC:/kidsmap, generation2026-10-16T18:56:53Z; найден SiteReviewsController. Template coverage partial90/119/131/freshness metadata_changed; controller/sharedJS coverage unavailable. Relevant source прочитан, literal search использован для динамических template/JS связей. Exhaustive/dead-code/reindex выводов нет, graph caches не сохранялись.

site_reviews.html:161–167 содержит hidden name=rating default5 и radiogroup с translated group name, но children — обычные type=button с aria-label1…5. Inline paint() около200 меняет только class.active; click меняет hidden, роли/checked/roving focus отсутствуют. Shared review_submission.js отправляет FormData и делает form.reset() после success. Server controller/default/range не являются причиной06.

Другие data-review-stars implementations находятся в place_detail.html и home.html; template-only diff не меняет их. Один первоначальный literal query включал отсутствующий предполагаемый includes/review_form.html и вернул nonzero; actual consumers найдены поиском в существующих каталогах, app files не создавались.

## Новый runtime

Own m09s06-plan-r1-app/pg, internal network m09s06-plan-r1-net, volume m09s06-plan-r1-pgdata, DB m09s06_plan_r1/testDB test_m09s06_plan_r1. Repo bind RO, только own scratch RW. DJANGO_TESTING=1/cleared env до setup, no .env/prodcredentials; отдельные cache/media/private-media/locmem email, fictional author/two reviewers/2approved reviews.

Fresh RU/AZ/EN MO построены из текущих PO и проверены до setup, sole LOCALE_PATHS=.tmp/social06-pc-plan-r1/locales/locale; sharedMO прежние. Loopback33336, hidden own WSL proxy, отдельная CLI session social06-pc-plan-r1/Chromium155.0.8059.12; Python3.12.15/Django6.0.2/PG17.11. Browser localhost-only/external blocked. [Runtime](runtime-info.json), [live-final](live-final.json), [locale manifest](locale-manifest.json).

Bounded PG readiness: одно not-ready наблюдение→ready; prepare в целом0. Proxy readiness без transient failures. Косметический stdout prepare сохранил PLAN05 из reviewed helper; исправлена только ignored helper подпись без повторного seed/prepare. Actual06container/DB/порт/source/soleMO проверены отдельно.

## Fresh native evidence

| Проверка | Результат |
|---|---|
| RU/AZ/EN ×360/390/768/1024/1280/1440 |18native cells|
| HTTP/group name/default/stars/Space/Enter/focus/hover/CSRF/layout/DB controls |198PASS|
| Default/Space/Enter selected-radio semantics |54FAIL|
| Single tab stop/scale names/Tab/ShiftTab/Arrow |90FAIL|
| Всего source assertions |0PASS/144FAIL|
| Unhandled pageerrors / HTTP failures / request failures |0 /0 /0|
| Native viewport PNG |36: Space и Enter каждого cell|

[Matrix](matrix.json), [helper](rating-cell.js), [runner](matrix.py), [PNG manifest](png-manifest.json), [CLI commands](browser-commands.jsonl). Runner exit0 означает корректно собранный RED, не product PASS. Исторические72FAIL не переносятся на новую matrix с восемью explicit source checks на cell.

Hidden5 первоначально, Space/Enter→3, active=[1,2,3], focus3. Все roles/aria-checked отсутствуют, все пять tabIndex0, names1…5. Tab из3 переходит к4 вместо имени, ShiftTab из имени возвращает5 вместо selected3, ArrowRight не выбирает4. AX snapshot: radiogroup с пятью button, ни одного checked radio.

Group names уже корректно локализованы: RU «Ваша оценка», AZ «Sizin qiymətiniz», EN «Your rating». Hover5 не сохраняет5, mouseleave возвращает paint3; этот preview contract сохраняется. Document fit продолжает PASS после SOCIAL05. Business POST в baseline нет; до/после aggregates равны2reviews/2approved/0pending/0reactions. QA login/session setup fictional, пароль/OAuth NOT RUN.

Вручную просмотрен native Space RU390: три звезды и keyboard focus видны. Screenshot/AX snapshot не являются real screenreader evidence.

## Предложение и проверки

Один template: role=radio/aria-checked, roving tabindex, SSR selected5; names1 / 5…5 / 5 задают шкалу, translated group label прежний, новых PO strings нет. choose() согласует hidden/checked/tabstop/paint, стрелки перемещают focus с wrap, Space/Enter остаются native button activation. Hover только preview, reset синхронизируется с реальным default hidden5.

[W3C Radio Group Pattern](https://www.w3.org/WAI/ARIA/apg/patterns/radio/) задаёт checked state и keyboard entry/exit/стрелки. Home/End в candidate — дополнительные shortcuts. Переиспользуются текущие кнопки; переход на native input radios потребовал бы иной структуры/CSS за пределами минимального scope.

Apply-check0; node syntax check inline candidate0; Django Template parse0 в own testing runtime; syntax-only acceptance helper0. Это не post-patch/browser GREEN. Candidate не применялся ни к app file, ни к текущему DOM. [Acceptance-extra](acceptance-extra.js) для будущего actual patch — NOT RUN.

Backend suites в06run NOT RUN: unchanged source, последние3unique affected methods из SOCIAL05 PASS0F/0E,0.355s сохранены, не объявляются fresh06запуском. После approval нужны actual native POST/range/ACL/error/reset/reload readbacks.

Промежуточный wrapper записи отчёта получил TypeError из-за Markdown backticks до вызова apply_patch; повтор с plain text успешен. Application/результаты checks не менялись; это tooling attempt, не source FAIL.

## Preservation / следующий шаг

IDs/states всех35entry containers сохранены, добавлены только own2контейнера06, foreign restarts0. Whole-machine process continuity NOT VERIFIED. Все6предыдущих PC packages/manifest/verification сохранены; source/CSS/sharedMO/.cbmignore прежние. Новая guide note отдельно от истории, reverse-removal SHA подтверждает прежние байты.

NOT RUN: app patch/post-patch GREEN/acceptance, actual POST/range/error/loading after candidate, backend suites, real SR/fullWCAG/physical/other browsers, external integrations/production/commit/push/deploy, SOCIAL07–09/full ACCEPT09/global/module10. Без reset/clean/stash/dirty checkout switch, старые PNG не догружались.

После approval точного [однофайлового плана](IMPLEMENTATION_PLAN.md): source/runtime/locale gates, сохранённый unchanged RED, exact patch, actual18cellGREEN +9extended keyboard/reset cases, native POST/range/ACL/error и небольшой shared smoke. Дополнительный файл/причина требуют отдельного scope. Закрывать только06 по actual evidence. [Commands](commands.md), [verification](verification.json), [artifact manifest](artifact-manifest.json), [next prompt](next-prompt.txt).
