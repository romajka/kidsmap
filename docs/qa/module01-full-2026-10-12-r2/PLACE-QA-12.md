# PLACE-QA-12 — rejected admin candidate save loses posted input

P2 OPEN, LOCAL final approved owner/admin-focus diff on HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51. No evidence of a recent regression: backend `domain_admin/place.py` remains identical to HEAD.

Native admin two tabs load fictional Place4 on owned QA11 profile. A changes AZ name and saves draft. B changes name with its stale candidate token and saves draft. Newer A is protected, but the resulting B form no longer contains B's unsaved name. All18 RU/AZ/EN×360/390/768/1024/1280/1440 cases independently showed this outcome. This is loss of uncommitted input, not overwrite of the canonical record.

Evidence: `../place-qa11-fix-2026-10-12-r1/admin-cas.result.json` and its18 native `admin-conflict-*.png` referenced rows. Actual source cause: `src/catalog/domain_admin/place.py:2103` catches post-validation `ValidationError` outside atomic save, reports message and redirects to `request.path`, so GET rebuilds current canonical fields and drops the submitted form. Owner-only QA10 is a different consumer and remains closed by its own scoped evidence.

Repair not performed. Proposed scope: preserve bound scalar/nested form input after typed candidate CAS rejection without re-executing writes or changing tokens/ACL/candidate/live; usable separate current comparison. Future specific plan: `docs/superpowers/plans/2026-10-12-place-qa12-admin-cas-retention.md`.
