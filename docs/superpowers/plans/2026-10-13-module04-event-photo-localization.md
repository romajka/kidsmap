# Module04 Events — EVENT-QA-02/03 repair and ACCEPT-04

Status: COMPLETE LOCAL. Approved scope implemented and verified; original recheck checkpoint retained below.

Checkout /home/ramin/kidsmap; branch task33-progress; HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51; dirty WORKTREE from modules01–03; active_run NONE. Entry snapshot: docs/qa/module04-recheck-2026-10-13-r1/entry.json. Preserve every pre-existing file and running stand.

## Verified scope and cause

EVENT-QA-01: original incorrect RU labels no longer reproduce with current PO compiled into this own isolated profile. Native admin owner/venue labels correct, existing global-label and shared-consumer tests2/2 PASS. This is bounded fresh verification, not full module acceptance and not PUBLIC-QA-03/SITE-QA-07 closure. No application patch for QA01.

EVENT-QA-02: reproduced native click→save→reload on draft Event1; photo-clear remains false, preview remains visible, persisted image URL unchanged. Event loads kidsmap_admin_form_shell.js, not Place-specific kidsmap_place_media.js. Shared shell uses nonexistent id_photo-clear in three sites; real checkbox name photo-clear / id photo-clear_id. Event readiness also uses the incorrect id. Programmatic checkbox change currently emits no change event, so readiness can remain stale even after correcting lookup.

EVENT-QA-03: current fresh MO already translates long requirements/recovery text. Remaining four exact owner/admin UI msgids are untranslated: Редактирование мероприятия (fuzzy wrong entity translation); Шаги формы мероприятия; Вперёд; Тип организатора. Native AZ/EN390px render confirms Russian edit badge; untranslated accessibility labels/source present. No rewrite of business instructions or stored AZ content.

## Allowed application files — only four

1. static/admin/js/kidsmap_admin_form_shell.js — three main-photo checkbox lookups and native change notification after main-photo removal.
2. static/admin/js/kidsmap_event_readiness.js — photo checkbox lookup in filled(item).
3. locale/az/LC_MESSAGES/django.po — only the four msgids above.
4. locale/en/LC_MESSAGES/django.po — only the four msgids above.

Own QA scripts/evidence under docs/qa/module04-recheck-2026-10-13-r1 and docs/qa/module04-full-2026-10-13-r1; own ignored runtime .tmp/module04-recheck-2026-10-13-r1. Update module04 status in docs/qa/continuation-and-repair-prompts-2026-10-11.md and docs/qa/module-acceptance-prompts.md only after acceptance. No backend/schema/ACL/CAS/publication policy, other module source, global MO, dependencies, commit/push/deploy/production changes.

## Implementation

### 1. Correct checkbox binding and notification

In three shell photo readers use actual input.form and input.name, preserving file selection precedence and initial preview attributes:
```js
var mainClearCheckbox = mainInput && mainInput.form
  ? mainInput.form.querySelector('input[name="' + mainInput.name + '-clear"]')
  : null;
```
In clearMainPhoto(), set checked=true, update main preview, then dispatch a bubbling change on the actual checkbox (or mainInput when no clear checkbox exists for an unsaved photo). This lets Event readiness/dirty tracking observe the real state:
```js
var changedInput = mainClearCheckbox || mainInput;
if (changedInput) changedInput.dispatchEvent(new Event('change', {bubbles: true}));
```
Do not dispatch inside syncMainPhotoState() because it also handles change events and would recurse.
Event filled(photo): resolve clear using file.form/querySelector by file.name; retain existing stored_photo and uploaded file precedence.

### 2. Exact translations

| msgid | AZ | EN |
|---|---|---|
|Редактирование мероприятия|Tədbirin redaktəsi|Edit event|
|Шаги формы мероприятия|Tədbir formasının mərhələləri|Event form steps|
|Вперёд|İrəli|Next|
|Тип организатора|Təşkilatçı növü|Organizer type|

Remove fuzzy only from Редактирование мероприятия after replacing its incorrect listing translation. Add absent entries; preserve all other entries/comments. RU unchanged. Build fresh RU/AZ/EN into .tmp/module04-recheck-2026-10-13-r1/locales-v2 using scripts/build_isolated_locales.py; verify manifest and sole LOCALE_PATHS before django.setup. Never overwrite common MO.

## Verification sequence — targeted first, one full module batch at end

Existing RED: red-browser.result.attempt1791880788.json and5PNG. First raw attempt retained; its GET logout405 is a QA-script error corrected by removing unnecessary logout; independent owner context used. Post-admin-login /accounts/profile404 is outside target editor, recorded, not hidden or interpreted as a photo regression.

1. After JS patch, native admin upload/save/reload, remove/save/reload, replacement after clear, cancellation of file selection; compare stored photo via explicit READ ONLY transaction with10s statement/2s lock timeouts. Preview must clear immediately, photo must enter missing checklist, publish control must disable, draft deletion must persist. Confirm genuine published-event photo requirement via actual admin POST/test without weakening rule or any assertion; a server rejection must retain saved photo/lifecycle and stale version protection.
2. Use a new QA regression browser script with hard assertions on checkbox, preview, readiness, persisted media and replacement. RED is current native failing behavior; GREEN is same assertions after patch. Add QA-owned backend behavior probes if necessary; existing Event tests/assertions remain unchanged. Run only affected EventAdminReadinessTests and EventAdminVersionTests during repair; keep already-passing two label test results while source unchanged.
3. Locale checks compare exact compiled strings and native accessible names. Native owner save/reload, two tabs→conflict, recovery choice, failed submit and simulated network abort recovery; verify retained user input/server version. RU/AZ/EN×360/390/768/1024/1280/1440; keyboard/focus/error/loading, PNG/console/network and manifest. Run live shared-shell consumer smoke for admin views loading it; Place uses separate handler, preserve its accepted source unchanged.
4. At end one ACCEPT-04 batch: use explicit existing Event test labels/discovery inventory, not no-label wrapper. Full native checklist from guide includes organizer rights/revocation, specialist linkage, venue permissions, online/offline, Asia/Baku intervals, age/price/contact/translations, primary/gallery/reorder/file errors, drafts each step, submit/reject/correct/approve/edit, cancel/reschedule/expiry, negative ACL/foreignID/CAS/network/map outages, public detail/list/search/old links. Include historical EVENT-ADM01–03, EVENT-A11Y, ACE05/06/07/08/09/16/21, CE-GET/NULL/GALLERY-FIRST/GALLERY-KEYS, applicable COMMON01 copy. Preserve historical reports. No module01–03 full retest; no next module.
5. New unrelated confirmed finding stays OPEN and needs a separate concrete scope approval; continue independent approved checks. External services explicitly SIMULATED/NOT RUN. Report exact commands/exits/counts, source/runtime match, hashes/preservation, PNG manifest, accepted limits. Only actual accepted IDs close; targeted repair does not mean module PASS.

## Own runtime provenance

Current own loopback HTTP127.0.0.1:49583/PID414189, source match verified at runtime-version-final.json; own PG container module04-recheck-2026-10-13-r1-pg, unique DB/cache/media/private-media/mail/cookies, no dotenv, fictional roles, blocked outside connections. Ports/PID are this run receipt only; verify again before continuation. Secrets remain in ignored scratch, never in evidence. Restart only own process after approved source patch; update source manifest and verify at startup. Foreign processes and active_run untouched.

## Approval receipt

User approved implementation in this chat: «lf hf,jnfq» (да работай). Scope EVENT-QA-02/03, four files and module04 acceptance.

## Final execution handoff

COMPLETE LOCAL; authoritative report docs/qa/module04-full-2026-10-13-r1/REPORT.md and verification.json. Checkpoint hypotheses/failed probes above remain history; final7-file diff and current locales-v6 evidence take priority. No commit/push/deploy/production.
