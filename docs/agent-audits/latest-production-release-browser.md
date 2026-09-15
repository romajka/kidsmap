# Latest-main isolated rendered browser QA

2026-09-15. browser-qa role and KidsMap UI/front-end skills read. User authorized full latest-main release; parent assigned local synthetic verification. Final source snapshot80d1df8958cc047e354d8e2be5a73f56591d9a29 (parent committed same checked files). No production data/credentials/application writes performed by this role.

## Isolation and commands

Disposable Docker `kidsmap-latest-browser-db`, imagepostgres:17-alpine, port127.0.0.1:55617, data tmpfs. New synthetic database and staff/owner accounts only. Initial postgres:17 pull was cancelled in favor of already available17-alpine. Scratch settings `/tmp/kidsmap-latest-release/browser_settings.py`: DJANGO_TESTING=1, isolated DB/cache/media, LocMem email, external analytics/maps/IndexNow disabled, localized URLs=True. Sessions stored mode0600 in scratch, never report.

`/tmp/kidsmap-latest-release/browser-manage migrate --noinput`: exit0 all migrations, logbrowser-migrate.log. Source modules from `/home/ramin/kidsmap/src`; env-i launch. `browser-manage runserver 127.0.0.1:8771 --noreload`, final session70501 after middleware/catalog restart. Two ready synthetic places plus owner draft fixtures; image generated locally. Chromium1228 real rendered browser via installed Playwright, fresh contexts; network allows localhost plus font assets only.

## Checked and fixed

- Admin list/add/edit AZ/RU/EN ×390/768/1024/1280/1440:45 rendered matrix cases. Add/edit localized URL controls/instruction tested. Matrix rerun against frozen source recorded below.
- Real admin chooser clicks AZ→EN→RU: destination and html lang match. Found prefix-cookie conflict (EN cookie +RU URL404); admin owner fixed middleware with backend regression. Browser same conflicting combination now200.
- Found new sorting toolbar width regression at390: sort+columns nonwrapping row put columns right455px. Scoped approved fix only `static/admin/css/pages/kidsmap_changelist.css`: mobile wrap and menu width bounds. Final sort dropdown left21.7/right341.7 within390. Actual created_asc/created_desc clicks reorder fixtureID1 oldest correctly.1280 sort also works. Existing recommendations nowrap and squeezed list heading were outside new sorting diff and were preserved.
- Admin JSON names import/confirmation/save →clear localStorage→reload: names persist; pricing JSON, structured schedule JSON and saved URL triplet identical. `node admin-import.cjs`: exit0, no pageerrors.
- Owner wizard save-and-leave with localStorage getter throwing SecurityError and real uploaded image: successful server save followed by dashboard navigation. Independent disposable DB query confirms draft_saved=True, photo_saved=True, photo_exists=True. No reliance on localStorage evidence.
- Owner save-and-leave failure: synthetic HTTP500 transport response keeps form and name, displays retry error; actual invalid-phone validation also stays form and retains name. `node owner-failed-save.cjs`: final exit0, zero pageerrors. Initial interception used too-specific URL and did not intercept POST; corrected globally and reran. No production traffic involved.

## Artifacts and reproduction

Scratch scripts in this directory: `browser-smoke.cjs`, `admin-interact.cjs`, `admin-import.cjs`, `owner-save-leave.cjs`, `owner-failed-save.cjs`, `owner-header.cjs`. Run with `node /tmp/kidsmap-latest-release/<script>`. Screenshots `admin-{list,add,edit}-{az,ru,en}-{390,1280}.png`, `sort-{390,1280}.png`, `owner-{az,ru,en}-{390,1280}.png`. Structured matrix `browser-matrix.json`. Local-only input/setup browser-seed.py/browser-manage; credentials omitted here.

## Limitations

No whole-site regression or production browser/admin mutation; parent owns backend suite and deployment. Existing recommendation-strip nowrap/squeezed mobile list heading were not redesigned. External integration behavior not certified. Comprehensive keyboard/a11y audit not performed; dialogs, sorting, chooser, save-and-leave and header menu interactions sampled. Admin names-only import preservation tested; exhaustive schedules/prices scenarios remain backend suite responsibility.

## Final frozen-source results

`browser-smoke.cjs` final exit0:45 cases, zero pageerrors, zero HTTP400+;42 no-document-overflow cases. Three list390 cases still show document overflow from existing recommendations/table/header layout; new sorting toolbar itself fits and works. This is explicitly not a claim that all admin mobile layout is fixed. Before/after new sorting bounds measured and screenshot inspected.

`owner-header.cjs` final exit0: AZ/RU/EN×390/1280 six cases, zero overflow/pageerrors. Mobile burger opens drawer and close button closes it; desktop language dropdown opens and Escape exercised. An initial immediate visibility assertion ran before animation settled; replaced with proper visibility wait, final pass.

Actual screenshots visually inspected after final changes: sort-390.png (sorting menu within viewport), owner-ru-390.png (wizard/header visible, mobile content fits), admin-edit-en-1280.png (English URL controls, Copy/Open labels, pricing/editor text). Final report concerns source80d1df89; server restarted after Python/gettext changes before final checks. Browser source edit ownership was only narrow changelist CSS, now committed by parent; no further edits pending.
