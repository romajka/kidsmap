# SOCIAL-QA-06 Implementation Plan

> Выполнять checkbox tasks после одобрения конкретного однофайлового scope. Lead frontend-reviewer, browser/accessibility checks последовательно, без независимых subagents. Из пользовательского «дальше» следует PLAN, не implementation06.

**Goal:** программно сообщать выбранную оценку сайта, согласовав её с hidden rating, клавиатурой, hover, focus и reset.

**Architecture:** сохранить пять существующих type=button и hidden name=rating; в том же page template дать кнопкам role=radio/aria-checked и один tab stop. Inline choose() меняет только текущую оценку, checked/tabindex/paint; hover остаётся visual preview. Group name использует прежний переведённый текст, item names1 / 5…5 / 5 задают шкалу без новых PO keys.

**Tech Stack:** Django6.0.2 SSR template, существующий inline JavaScript, native Chromium155; новых dependencies нет.

**Spec:** [finding SOCIAL06](../module09-2026-10-10-r1/findings/SOCIAL-QA-06.md), [repair prompt](../module09-2026-10-10-r1/repair-prompts/SOCIAL-QA-06.txt), [guide PLAN06](../continuation-and-repair-prompts-2026-10-11.md#repair-SOCIAL-QA-06), [fresh REPORT](REPORT.md).

## Global constraints

- Scope ровно src/catalog/templates/pages/site_reviews.html. CSS/controllers/sharedJS/PO/models/schema/routes/existing assertions и другие findings не менять. Полный [candidate file](candidate-site_reviews.html), [exact diff](proposed.diff), [SHA](candidate-manifest.json) reviewable и unapplied.
- C:\kidsmap; branch codex/module09-transfer-2026-10-16-r1, HEAD852938d96764ae315b92859e3651e5ea62054a36, source1021. Сохранить dirty approved SOCIAL03–05, index/task33ref/active_run:NONE, чужие файлы/процессы/sharedMO/.cbmignore.
- Без reset/clean/stash/dirty checkout switch/commit/push/deploy/production. SOCIAL07–09/full ACCEPT09/global автоматически не начинать.
- Тесты только собственные DJANGO_TESTING=1 PG/DB/cache/media/private-media/email, fictional fixtures, cleared env/no .env/prodcredentials. External blocked/SIMULATED. Fresh RU/AZ/EN из текущих PO через builder/verify, sole LOCALE_PATHS до setup.
- Server default rating5 и payload name=rating/range1–5 сохраняются. После reload новая форма по-прежнему default5; сохранённый pending review остаётся с выбранной отправленной оценкой. Не подменять это новой серверной логикой восстановления.
- Generic CSS/05layout и shared rating widgets Place/home/typed остаются вне изменения; broad selector в inline script исполняется только в site_reviews page.
- Browser AX snapshot не является real screenreader/fullWCAG evidence. Успешные unchanged full suites не повторять, existing assertions не смягчать.

## Обоснование и source map

site_reviews.html:161–167 содержит hidden5 и radiogroup, но внутри обычные кнопки с labels1…5. Inline paint() около200 меняет только class.active; click меняет hidden. Родительская группа уже называется переведённым «Ваша оценка». Full radio pattern требует selected checked state и keyboard focus traversal; [W3C APG Radio Group](https://www.w3.org/WAI/ARIA/apg/patterns/radio/) описывает один Tab entry/exit и выбор соседнего radio стрелками.

В этом bounded fix переиспользуются существующие type=button; нативная замена на видимые/скрытые input radios потребовала бы иной CSS/визуальной структуры. Полный keyboard/checked contract реализуется локально без смешивания checkbox/pressed семантики. Numeric fraction plus translated group name даёт контекст шкалы без нового переводимого текста.

Shared review_submission.js читает форму/hidden FormData и вызывает form.reset() после success; новый локальный reset listener возвращает checked/tabstop/paint к реальному default hidden5 после native reset. Его selectors и shared validation не переписываются. Home/place_detail имеют отдельные rating implementations; они не включают этот page template. Actual POST/service/range/ACL остаются серверными.

Graph ready C-kidsmap, но cited template partial90/119/131, freshness metadata_changed и controller/JS coverage unavailable; decisive facts проверены source и native DOM. Не делать exhaustive/dead-code выводов.

## Task1 — authorization/source и сохранённый RED

- [ ] Проверить прямое scope approval этого плана; предыдущее approval05 не относится к06. После approval не спрашивать повторно тот же scope.
- [ ] Сверить [source-entry.json](source-entry.json), current hashes1021/HEAD/index/active_run/sharedMO/foreign artifacts. Own m09s06-plan-r1-app/pg/net/loopback33336/session нельзя reuse без ownership/isolation/source/soleMO proof.
- [ ] Если source unchanged, использовать сохранённый native RED18cells RU/AZ/EN×360/390/768/1024/1280/1440: [matrix](matrix.json) и [rating-cell.js](rating-cell.js). Native Space/Enter input3/paint3 — controls; selected radio/scale/single tabstop/Tab/ShiftTab/Arrow source assertions FAIL. Не повторять полный corpus.
- [ ] При drift создать новый уникальный runtime/freshMO и affected RED; scope/cause drift оценить до patch.

## Task2 — один шаблон

Modify: src/catalog/templates/pages/site_reviews.html, markup163–167 и inline script около200–225. Code steps полностью заданы [candidate-site_reviews.html](candidate-site_reviews.html); hunk полностью задан [proposed.diff](proposed.diff). Новых application/test файлов нет; regression находится в versioned QA helpers.

- [ ] Apply-check, затем применить exact diff:

~~~powershell
git apply --check --ignore-space-change docs/qa/social-qa06-recheck-2026-10-17-pc-r1/proposed.diff
git apply --ignore-space-change docs/qa/social-qa06-recheck-2026-10-17-pc-r1/proposed.diff
~~~

- [ ] На пяти кнопках role=radio; checked только5 по SSR, tabindex0 только5, остальные-1; имена1 / 5…5 / 5. Group label остаётся существующим translated ключом.
- [ ] choose(value,moveFocus=false) обновляет hidden value, все aria-checked, roving tabindex, затем paint; при keyboard стрелке перемещает focus на radio выбранного value.
- [ ] Click выбирает value; Space/Enter сохраняют native button activation без дополнительного keydown submit/double click.
- [ ] Right/Down → next wrap5→1, Left/Up → previous wrap1→5. Home1/End5 — дополнительные supported shortcuts. Для этих keys preventDefault; прочие keys/Tab не перехватывать.
- [ ] Hover только paint, не hidden/aria-checked/tabindex. Mouseleave paint(saved value). Reset → requestAnimationFrame → choose(current reset hidden default5).
- [ ] Только template отличается от entry1021, normalized SHA=after candidate; CSS05/PO/sharedJS/backend/прочие1020source совпадают.

## Task3 — meaningful native GREEN

- [ ] Новый browser context и fresh runtime/template/static origins/soleMO. SSR до inline execution: пять role radio, checked5/tabstop5, hidden5. Это можно получить read-only HTML response; поведение с полностью отключённым JS отдельно не принимается.
- [ ] Повторить18cells [rating-cell.js](rating-cell.js) без ослабления current controls/source assertions: default/Space/Enter/scale/Tab/ShiftTab/Arrow PASS; AX tree должен содержать radio3 checked после активации, вместо buttons без selected state.
- [ ] Выполнить [полный keyboard/reset outcome helper](acceptance-extra.js) RU/AZ/EN×390/768/1440. Helper сейчас NOT RUN на candidate; он не заменяет actual live patch. Проверяет обе пары стрелок/wrap/Home/End, mouse, hover not committed, native form reset/default consistency, one tabstop, focus, no unintentional submit/document overflow.
- [ ] На тех же языках actual native Tab entry/Space/Enter и реальные scroll/viewport PNG после finite animations. Visible focus должен сохраняться, никаких positive tabindex/keyboard trap.
- [ ] Native POST на свежих fictional авторах после выбора3/1/5: actual request FormData rating, pending DB readback, success/reset checked5 и reload public projection/сохранённый rating. Проверить guest no form/API auth, invalid rating0/6 server rejection, CSRF403/no writes. Нельзя ослаблять серверный range/менять payload под UI.
- [ ] Native error/loading guard: явно SIMULATED delay/abort до server delivery; selected radio и ввод сохраняются, busy/button disabled, после ошибки управление возвращается, один POST без auto retry. Hover/pointer preview не должен незаметно отправлять другую оценку.
- [ ] Три existing backend methods, прошедшие05 на том же неизменённом backend source, не повторять полным suite. Backend/additional affected tests запускать только при новом regression concern; native POST/range/ACL readback — fresh acceptance этого изменения.
- [ ] Small shared smoke: Place detail rating, home отсутствие changed page-specific handler, typed Activity/Specialist/Event reviews в390/768/1440 RU/AZ/EN; scope неизменен, не повторять целиком06соседние findings. Existing SOCIAL07/Activity technical title оставить OPEN и не менять assertions.
- [ ] Console/pageerrors/static404/font/icon/PNG hash+dimensions, no new document overflow. Physical/other browsers/real screenreader/fullWCAG NOT RUN без отдельного запуска; не называть эти группы PASS.

## Task4 — evidence/stop

- [ ] Новый уникальный fix-run REPORT/verification/commands-exits-counts/source/PNG/RED→GREEN/SIMULATED/failedattempts/NOTRUN, approval recorded.
- [ ] Preservation: остальные1020source, sharedMO/index/HEAD/branch/task33ref/active_run/.cbmignore, прежниеpackages и entrycontainer IDs/states. Whole-machine continuity не утверждать по Docker snapshot.
- [ ] SOCIAL06 закрыть только после actual scoped acceptance. Новая guide note отдельно от истории, next prompt с фактическими путями. SOCIAL07–09/fullACCEPT09/global/production/commit/push/deploy не начинать автоматически.

## Self-review

Даны один точный файл/full candidate/diff/hashes, SSR/initial/selected state, keyboard/mouse/hover/roving focus/reset, translated group plus scale names, POST/range/default/ACL и failure guards, shared consumers, evidence preservation. Backend/CSS/PO исключены из application scope. Syntax-only node check и apply-check не являются post-patch GREEN. Candidate непроверен в живом приложении, implementation approval PENDING.
