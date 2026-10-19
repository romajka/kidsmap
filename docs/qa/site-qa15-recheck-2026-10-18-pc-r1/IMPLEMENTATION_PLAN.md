# SITE-QA-15: Settings conflict protection Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.
> Session override: execute inline under the canonical KidsMap workflow. No new agents or unavailable skill dependencies are needed; existing user/repository instructions govern scope and approval. No commits.

**Goal:** Prevent a stale settings form from silently replacing a newer save, while retaining the second tab's text/checkbox draft for explicit user review.

**Architecture:** Signed full-row snapshot bound to row/section/actor, checked against a locked current SiteSettings instance before ModelForm save. Conflicts return409 with a bound form; no automatic merge, token refresh or POST retry. Main-image AJAX writes join the same row lock and update only their own field plus updated_at.

**Tech Stack:** Existing Django6.0.2/Python3.12/PostgreSQL17, Django signing/transactions/forms/templates/gettext, current native Chromium CLI. No new dependency or schema migration.

**Spec:** [SITE-QA-15](../module10-full-2026-10-18-pc-r1/findings/SITE-QA-15.md), [impact map](IMPACT_MAP.md), [fresh report](REPORT.md). This package is PLAN ONLY / approval pending. [Exact patch](proposed.diff), [before/candidate hashes](candidate-manifest.json).

## Global Constraints

- Preserve HEAD852938d/transfer branch, retained SITE01/SOCIAL fixes and all foreign WORKTREE/QA/refs/index. active_run NONE. Production not accessed; no commit/push/deploy/reset/clean/stash/switch.
- Implementation exact6files below. Model/schema/presets/CSS/JS changes are outside this plan. SITE06 validation and SITE14 transport-draft recovery remain separate.
- Tests only DJANGO_TESTING1, fresh owned normal/test DB, isolated media/private-media/cache/email/TMPDIR, disabled external integrations and current RU/AZ/EN MO verified before django.setup.
- Once this plan is approved, its test/apply/verification/report steps need no repeated approval. Wider files/policy require a separate plan.

## Exact scope

|File|Change|
|---|---|
|`src/catalog/domain_admin/site.py`|Signed revision payload/form/admin mixin; six settings section editors and direct SiteAnalytics editor; serialized partial-field main-image AJAX writes|
|`src/catalog/templates/admin/catalog/shared_settings_change_form.html`|Conditional revision input; conflict alert/focus, current-version new-tab link and file-reselection notice; other consumers remain conditional|
|`src/catalog/testcases/test_site_qa15_settings_concurrency.py`|New21methods:20 ordinary cases and1 PostgreSQL TransactionTestCase with simultaneous clients|
|`locale/ru/LC_MESSAGES/django.po`|Append3messages, preserve every existing byte/entry|
|`locale/az/LC_MESSAGES/django.po`|Append corresponding3messages|
|`locale/en/LC_MESSAGES/django.po`|Append corresponding3messages|

No existing test assertions need adaptation. Current bounded search found existing settings tests exercising GET/model saves, not a proxy form POST fixture that would require a new token; this is not an exhaustive dynamic-call guarantee. Existing33 targeted methods passed unchanged.

## Product policy to approve

1. **Whole-row conflict:** after any SiteSettings value changes, a previously opened form gets409, including disjoint fields/sections. There is no silent merge. Snapshot contains only a digest and row/actor/section identity, not raw setting values; changes through `QuerySet.update()` are detected even if updated_at is not advanced.
2. **Draft retention:** the409 document is the bound submitted form. Text/checkboxes remain visible and escaped. The old token stays old; repeatedly pressing Save remains409. No success message or server/file/log-entry save on conflict. No automatic page reload/replay.
3. **Explicit recovery:** a keyboard-accessible link opens the current version in a new tab; the old draft remains open for manual copying. File inputs cannot be repopulated by browsers: selected files are not stored on a rejected request and a localized notice requires reselection. This does not claim persistence after closing/reloading the draft tab.
4. **Permissions:** existing admin_view/CSRF/volunteer/model permissions remain authoritative. A missing, altered, wrong-actor or wrong-section revision is409 only after normal access gates. Legitimate fresh submissions retain302 and existing save/continue behavior.
5. **All relevant admin writers:** include the six visible settings section forms and the normally unlinked direct SiteAnalytics change form. SiteSettings compatibility change endpoint remains its existing redirect. Statistics changelist behavior/navigation/permission presets remain intact; the direct analytics editor gains the shared form shell and revision protection.
6. **Media interaction:** existing main-image AJAX handlers retain SITE01 permission checks. Lock SiteSettings before upload/delete, save only `[field_name, 'updated_at']`; gallery image creation is a separate table and does not invalidate a settings revision. Two standalone AJAX uploads still follow serialized last-writer behavior; this plan protects settings-form snapshots rather than adding AJAX client revision tokens.

## Task 1: Regression and server concurrency boundary

**Consumes:** current SiteSettings concrete fields, ModelAdmin changeform atomic transaction, normal permission gates, request actor and hidden revision.
**Produces:** `_settings_revision_payload(obj, actor)`, `_SettingsRevisionForm`, `_SiteSettingsConcurrencyAdminMixin`; signed snapshot verified before writes under a row lock.

- [x] Save candidate21methods and execute them against unchanged application, together with33 existing SITE01/media/sidebar/public-section methods. Current54method RED:16 failed candidate methods,5 candidate+33 shared PASS,36failure observations/0errors/exit1. Two real concurrent clients return302/302 rather than exactly302/409.
- [ ] Before application: revalidate every before-hash/branch/index/retained source1028 and candidate bytes. Use a new fix package and owned runtime; do not rerun this package's launchers against old DB/evidence.
- [ ] Fresh RED using the same21method candidate module and33existing labels in a newly isolated profile. `run_red.py` records the exact labels. Preserve failed controls/fixtures and distinguish app failures from setup errors.
- [ ] Apply exact candidate `site.py`, retaining SITE01 permission gates before all mutation logic. The core token payload is:

```python
values = {field.name: field.value_to_string(obj) for field in obj._meta.concrete_fields}
digest = hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()
payload = {"row": obj.pk, "section": obj._meta.label_lower, "actor": actor, "digest": digest}
```

- [ ] Use `signing.dumps/loads` with the exact salt in the candidate. It is a state token, with no separate expiry policy; a token remains usable only while its actor/section/full-row digest matches. Signing does not replace permission or CSRF checks.
- [ ] Keep queryset `select_for_update()` limited to POST. Local installed Django `ModelAdmin.changeform_view` wraps POST in `transaction.atomic`; its `get_object` consumes this queryset before form validation. No late-only check in save_model.
- [ ] Bind actor to a per-request returned form subclass; do not store request/actor on the shared ModelAdmin instance. Form.clean compares the signed payload against the locked instance before `_post_clean` constructs submitted values.
- [ ] Preserve posted revision on every invalid POST. Only GET signs a fresh snapshot. Form conflict sets non-field ValidationError `stale_settings`, and the renderer sets409.
- [ ] Serialize main-image AJAX with `transaction.atomic` and `SiteSettings.objects.select_for_update().get(...)`. Upload changes only its image field and updated_at; delete keeps its existing file/cache behavior inside the row lock. No gallery schema/action changes.

Actual implementation is fully reviewable in [candidate backend](candidate/src/catalog/domain_admin/site.py). No candidate behavior has been run GREEN.

## Task 2: Bound conflict response and translations

**Consumes:** renderer context `km_settings_revision_enabled`, `km_settings_revision`, `km_settings_conflict`, `km_settings_current_url`, `km_settings_reselect_files`.
**Produces:** hidden signed token only for protected forms; bound409 error/recovery UI; three translated messages.

- [ ] Apply exact shared-template candidate. The revision field is conditional, so Gallery/CatalogContentSettings shared-template consumers do not gain an unrelated settings token.
- [ ] Keep the original error rendering and existing escaped bound widgets. On conflict add `role="alert" tabindex="-1" autofocus`, a same-path link with `target="_blank" rel="noopener noreferrer"`, and the file notice only when request.FILES was submitted.
- [ ] Append exactly the three PO messages. Verify prior PO bytes as an unchanged prefix, including all existing metadata/context/plurals. Compile current catalogs to a new green-only owned locale directory; do not overwrite shared MO or the red locale snapshot.
- [ ] Update runtime/source guards to the new approved stage (source1029 including the new test) and select the fresh green locale manifest/LOCALE_PATHS before django.setup. All candidate source/template/PO static checks currently pass; repeat after exact application.
- [ ] Fresh native AZ/RU/EN ×360/390/768/1024/1280/1440: same-field and disjoint-field two-tab saves for content-manager and superuser. First save302, second409, stored A unchanged, B text/checkbox draft retained, no success toast, no automatic retry, accessible alert/current-version link, no new layout regression. Existing hidden mobile submit controls/overflow need separate SITE08 attention; native Enter from a text input is an actual tested mobile submit path, not a forced hidden-button click.
- [ ] Native explicit recovery: leave B409 open, open current version in a new tab, verify A/current values; manual copied choice with a fresh token saves successfully. Repeated B token must remain409. Test both `_continue` and `_save` behavior.
- [ ] Test stale file upload rejection/storage invariants/reselection message and fresh file retry; interleave authorized media upload/delete with an open form. Confirm SITE01 denied roles remain unable to mutate media.
- [ ] Smoke all seven protected GET forms and real fresh saves with their existing fields. Keep statistics changelist behavior and Gallery/CatalogContentSettings controls. Canonical AZ is unprefixed; `/az/...` has its pre-existing301 and is not a direct admin403 route.

## Task 3: Verification, preservation and scoped decision

- [ ] Run new21+existing33 methods GREEN with exact commands/counts/exit0; the concurrent case must run on PostgreSQL, not SQLite. Keep denied/CSRF/HTML escaping/no-orphan cases intact. Any genuine test fixture defect must retain its original result and corrected RED proof.
- [ ] Record fresh static checks, template origin, locale manifest, source/candidate/apply hashes, native matrix/operations/readbacks, PNG manifest and console/network classification in a unique fix package. Expected403/409 and blocked external requests are retained, not called console-clean.
- [ ] Reconcile final diff to the exact6files, preserve all prior packages and source outside scope, refs/index/activeNONE/sharedMO/.cbmignore/foreign runtime identities. Append guide/MASTER only after verification.
- [ ] Close only SITE15/P2 LOCAL if all required checks pass; module10 then remains14OPEN and still needs full acceptance after its fixes. SITE06 next needs a separate plan. Module09 closure retained; release/global/production remain unverified.

## Risks and rollback boundary

Conservative whole-row409 may interrupt unrelated-section edits; this is the explicit proposed tradeoff. Direct non-admin/manual/model writers are not turned into a global CAS service; updates to the row invalidate forms, but arbitrary later external full-row saves remain outside this admin contract. Row locks include media storage operations; test timeout behavior without weakening no-write guarantees. No filesystem-transaction guarantee is added for genuine storage failures. Existing data validation/layout/transport-recovery problems remain separate.

Rollback, if needed, reverses only these exact approved byte changes against before-hashes; no reset/clean/stash. No schema rollback is involved. Current candidate remains unapplied and GREEN behavior is NOT RUN. User approval is for this policy and these six files.
