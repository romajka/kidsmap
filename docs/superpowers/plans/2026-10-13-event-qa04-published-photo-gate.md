# EVENT-QA-04 — published Event must reject explicit primary-photo removal

Status: COMPLETE LOCAL. Approved supplemental scope verified; original boundary retained below.

Checkout /home/ramin/kidsmap; branch task33-progress; HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51, pre-existing dirty WORKTREE preserved, active_run NONE. No commit/push/deploy/production.

## Fresh reproduction and root cause

Own Event3 was created/submitted/rejected/corrected/approved through real browser. After repairing no-op EVENT-QA-02 button, actual photo-clear POST is sent. Save/reload leaves status=published and photo empty. Explicit READ ONLY readback: docs/qa/module04-full-2026-10-13-r1/readback.json, main=3. Original audit explicitly did NOT test the gate because clear was never submitted.

Root: EventAdminForm.clean() in src/catalog/domain_admin/place.py, publication checklist. ClearableFileInput returns literal False for explicit removal. The generic falsy fallback reads the stored instance photo before model construction, so photo is mistakenly counted as present. Domain publication checks do not independently require photo, allowing save. This is an existing gate bug now observable after UI repair, not evidence of production impact.

QA test: docs/qa/module04-full-2026-10-13-r1/event_photo_gate.py uses actual admin POST and independent literal expectations response200/errors/photo unchanged/statuspublished. Native test RED result recorded in published-photo-gate-red.txt; inspect exact outcome before implementation. Published photo removal must be rejected under existing publication checklist. Draft removal remains allowed.

## Additional allowed source/test files — only two

- src/catalog/domain_admin/place.py: EventAdminForm.clean(), one fallback condition. Preserve all earlier Place changes in this dirty file.
- src/catalog/testcases/test_event_admin_photo_clear.py: new behavioral regression tests for published clear rejection, unchanged stored photo, draft clear success, valid replacement and invalid/stale POST persistence.

Own QA/evidence in existing module04 run directories, current locale profile reuse (no new locale strings/compilation required); guide/status/plan receipt links only after acceptance. No other backend/service/schema/rules/ACL/CAS/dependency/test-assertion changes.

## Minimal patch

Existing fallback:
```python
if self.instance and self.instance.pk:
    val = getattr(self.instance, field_name, None)
```
Replace only its condition inside publication checklist:
```python
if self.instance and self.instance.pk and not (field_name == "photo" and val is False):
    val = getattr(self.instance, field_name, None)
```
Explicit False stays missing; unchanged committed FieldFile retains existing fallback. Existing translated publication error used, no new copy. Draft / explicit unpublish paths continue to skip publication checklist by current policy.

## Targeted verification and module handoff

1. Record current RED before patch; add persistent regression tests with actual synthetic admin POST. Preserve old assertions.
2. After patch run only new photo-clear tests and EventAdminReadinessTests/affected EventAdminVersionTests, with own DJANGO_TESTING=1 PostgreSQL/media/cache/email. Existing136 method results retained by provenance; do not repeat full module batch after one condition patch unless affected failures require it.
3. Native fresh published upload/save/reload→clear/save error→reload must retain same stored photo and published state. Draft clear must still persist; cancel file selection / replacement after clear, gallery deletion/reorder/save and public image continue to work. Prove READ ONLY readback.
4. Repeat affected admin media/error/readiness cells RU/AZ/EN×360/390/768/1024/1280/1440 with real selected admin language, keyboard/focus/error, PNG/console/network. Unchanged owner/public module matrix remains retained; repeat public image readback affected by restored fixture photo. Only own stand process can be restarted, verify running source hashes.
5. Keep new ID OPEN until actual acceptance, no module PASS based only on backend. Finish independent ACCEPT-04 checks already authorized. New unrelated defects require distinct scope, never auto-fix.

## Approval receipt

User: «Да, исправь EVENT-QA-04 и заверши модуль». Approved in this chat on2026-10-13.

## Root-cause refinement within approved scope

The RED→first patch test exposes an earlier branch: False == 0 in Python, so generic `not val and val != 0` skips both fallback and missing-photo handling entirely. The first proposed fallback-condition patch is insufficient. Final minimal implementation handles explicit photo False before that numeric-zero-preserving generic condition:
```python
if field_name == "photo" and val is False:
    missing.append(str(label))
    continue
```
Original generic fallback is otherwise unchanged. Same approved ID, same server method/file and existing publication contract; no scope expansion. Preserve failed first attempt evidence.

## Final execution handoff

COMPLETE LOCAL; authoritative report docs/qa/module04-full-2026-10-13-r1/REPORT.md and verification.json. Checkpoint hypotheses/failed probes above remain history; final7-file diff and current locales-v6 evidence take priority. No commit/push/deploy/production.
