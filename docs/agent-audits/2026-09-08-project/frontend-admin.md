# Frontend admin audit — 2026-09-08

Role: frontend-admin; execution identity `/root/audit_qa`, executed sequentially after integration-reviewer, **not a second independent agent**. Definition read: `.agents/agents/frontend-admin/agent.md`. Skills: kidsmap-ui-design, frontend-design, fixing-accessibility. LOCAL HEAD `d75b34f4db5d4ba484cf8392ff3ae0c9939031e2`; application WORKTREE equals HEAD, pre-existing agent-system changes preserved. PRODUCTION UNKNOWN, not contacted. Source-only UI audit; rendered behavior belongs to independently running `/root/audit_browser`. No fixes, data changes or new tests in this role.

## 1. Состояние области

Active inheritance: `templates/admin/base.html` → base_site (notifications CSS/JS) → registered Place change_form; configured template roots give repository `templates` priority over app templates. Place form loads `kidsmap_place_form.js` and `owner_pricing_plans.js` together. Volunteer edit extends `admin/volunteer/base.html`, shares section/field templates, but uses its own `volunteer_place_form.js` and `permanent_place_pricing.js`. `services/volunteer_editor.py:editor_context` derives progress from backend readiness; proposal saves remain backend-owned. Actual role controls are not treated as object ACL proof.

Graph reused existing project root/index; specific coverage check reports metadata_match for notifications JS and wizard JS. Directory-level volunteer coverage was not tracked, so direct template/source reads were used. No rendered layout, computed contrast, screenshots or keyboard execution personally performed; browser agent received bounded hypotheses.

## 2. Сильные стороны

Notifications engine has initial focus, Tab cycling, Escape and return-focus logic (`kidsmap_notifications.js:handleKeydown/close/show`), named dialogs and live toast region. Volunteer guide uses native dialog; section controls update aria-expanded; language tabs implement left/right/Home/End and roving tabindex. Dirty state has beforeunload protection. Conflict UI disables saves and explains stale revision recovery. Reduced-motion rules exist in notifications and volunteer CSS. These are source strengths, not a browser certification.

## 3. Реальные проблемы

**UIA-01 — P2: staff price preview can misstate currency and minimum price.** LOCAL, high source confidence; browser confirmation requested. `static/admin/js/kidsmap_place_form.js:672–707` extracts numeric amounts and appends `₼` regardless plan currency; a sole `from=80` also becomes `80 ₼`, losing “from”. `static/js/owner_pricing_plans.js:617–693` independently writes the same computed badge, also appends ₼ and aggregates all active plans without primary-role filtering. Both assets are wired in `src/catalog/templates/admin/catalog/place/change_form.html:8,13`; mutation observer/input callbacks in first script overwrite the shared target (`:710–723`). Backend `services/pricing_plans.py:build_public_price_summary`, especially514–547, treats foreign currency and primary/on-request prices differently. Trigger: edit a foreign-currency exact tariff or a minimum-only tariff and inspect automatically computed price / preview, without saving. Impact: staff sees a misleading public-card prediction; DB currency corruption is not claimed. Owner frontend-admin + Django pricing; next step one server-derived formatter contract and benign rendered comparisons.

**UIA-02 — P2: volunteer has no visible control for place price mode.** LOCAL, high confidence source. `volunteer_forms.py:65–66` makes price_mode hidden; `admin/volunteer/place_form.html:5` renders it hidden; `services/volunteer_editor.py:21` excludes it from generated field sections. The volunteer pricing block renders only plan list/add; its loaded `permanent_place_pricing.js` has no price_mode control. Full staff pricing_editor, in contrast, includes segmented tariffs/free/free_entry_paid_services/events controls. Trigger: new volunteer place intended as wholly free or event-priced; UI cannot select the matching supported Place mode. It can add a free tariff, which is a different data representation; existing hidden modes are preserved but cannot be changed through controls. Impact: incomplete editing capability and inability to express correct mode without staff intervention. Owner frontend-admin; next step expose server-supplied allowed modes and test save/reload/readiness, retaining proposal-only persistence.

**UIA-03 — P2: shared custom field template loses error/help associations.** LOCAL, high source confidence. `admin/catalog/place/form/_field.html:24–29` renders hint/error paragraphs without IDs. Django6 BoundField (`.venv/lib/python3.12/site-packages/django/forms/boundfield.py:299–314`, inspected local dependency source) emits aria-describedby referencing `<auto_id>_helptext` and `<auto_id>_error`. The custom markup lacks those targets; bounded reads of staff/volunteer scripts found no repair. Trigger: focus an invalid ordinary field or field with help text. Impact: visual text exists but assistive description linkage can be dangling; error summary alone does not associate individual field guidance. Owner frontend-admin/a11y; next step supply matching IDs and verify references in invalid local rendered form. Same pattern also appears in owner field partial; one shared audit finding, not duplicate severity inflation.

## 4. Tech debt

Two independent admin price computations target one badge (UIA-01), while volunteer uses a third editor. This duplication is actionable because concrete semantic drift exists, not merely because files are large. Staff carryover fields remain a necessary persistence bridge; preserve them when touching manual form markup. Wizard/helper assets manually enumerate tariff options and rules; avoid adding a fourth interpretation.

## 5. Risks

Cross-locale length, narrow admin layouts, sticky panels, viewport keyboard interactions, dialog stacking and actual toast timing remain browser-owned/NOT VERIFIED here. External Leaflet CDN is loaded by volunteer edit; blocked CDN behavior is not automatically a production outage. Existing backend-owned BE-01 scalar clearing and BE-03 owner schedule loss are documented in backend/qa; source UI audit does not duplicate their IDs. UIA-01 preview difference is separate from those persistence failures.

## 6. Dead/legacy candidates

No deletion recommendation. Retained `pages/includes/permanent_place_workspace.html` volunteer branches may reflect earlier presentation but service routes must be traced before calling them dead. Multiple admin template roots implement loader overrides, not proven duplicates. Legacy price carryover must survive any redesign until data migration policy is explicitly approved.

## 7. Tests gaps

No new Django or browser runs in this role. Reuse explicitly attributed QA evidence: earlier `/root/audit_qa` integration-reviewer ran 538 existing test executions on isolated SQLite, with13 failure records; this does not certify admin rendering. Source-defined keyboard handling is not runtime evidence. Add mode editing round-trip, currency/from/on-request preview parity, invalid-field aria target checks and a staff/volunteer browser matrix. Protected routes require synthetic local identities; no production login used.

## 8. Recommendations

Prioritize preview contract parity and missing volunteer mode control, then field-level error associations. Use existing shared notifications/dialog patterns. Ask browser QA to inspect the exact triggers above across AZ/RU/EN and representative widths; preserve backend validation, proposal access and hidden/carryover fields. Application changes require the agreed implementation plan; this report authorizes none.

## 9. P0/P1/P2/P3

No UI-owned P0/P1 established. P2: UIA-01 misleading computed price, UIA-02 missing mode control, UIA-03 missing description targets. No additional P3 assigned just for style complexity. Source findings remain qualified until rendered evidence is attached by browser QA.
