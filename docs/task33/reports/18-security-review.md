# Stage 18 — independent security and visibility review

Role `security-reviewer`, AUDIT, 2026-10-02. Assigned output only; application code unchanged. LOCAL HEAD `c52b871ce5c18656a9eaf9854e66255c2629364e`, dirty WORKTREE under stage18 run `20261002-112210Z`; findings apply to the worktree, not HEAD or PRODUCTION. Production/external services not contacted.

## Evidence

- `controllers/public_details.py:organization_detail,activity_detail` checks `present(...)[visible]` before rendering or tracking. `services/public_presentation.py:visible` requires a published, active, non-deleted Place; published, approved, non-archived Organization/Program; and a published, non-archived Activity with a visible Place. No revision payload is read by the resolver. A standalone Place has no synthetic Organization.
- Organization branches use `published_place_queryset` plus `current_organization`, which requires a visible Org and current affiliation (`controllers/public_details.py:21–23`). The review feed uses `public_review_queryset` and links each approved review to its original Place; template has no Org aggregate rating (`public_entity_detail.html:31–35`). Published programs are filtered by approved/non-archived state.
- `public_presentation.py:current_organization,contact_data,present` refreshes the Place/Organization link from storage and gates inherited contacts and Program data on current affiliation, avoiding a stale related-object cache. Detach service severs live Program links and copies an approved local snapshot; a later Program edit is not read through the detached Activity. `phone_views.py:reveal_place_phones` retains POST, CSRF, public Place query and throttling while consuming `contact_data`. `seo.py:build_place_seo_payload` and map serialization consume the resolver for shared name/price/contact inputs. Template URLs and text use Django autoescaping. `safe_web_url` permits only HTTP(S) with netloc and no URL credentials, and now returns empty for malformed URLs.
- `tracking.py:track_subject_view` records only visible Organization/Activity subjects with schema2 identity once per request; no Place event is emitted by this function. Existing Place tracking remains separate.

## Finding and residual risks

- **SEC18-01 closed in source recheck.** `public_presentation.safe_web_url` catches malformed URL `ValueError`; `contact_data` validates the local website before selecting a current Organization fallback (`services/public_presentation.py:53–79`). Focused negative fixtures now cover malformed legacy website and local-phone/WhatsApp precedence (`test_task33_public_details.py:test_invalid_legacy_contact_does_not_crash_and_uses_valid_active_fallback`, `test_local_phone_keeps_whatsapp_local`). Lead reported RED 1E+1F/12; final GREEN remains lead-owned evidence. No availability failure remains in the inspected code path.
- Shared resolver is a display helper, not an authorization guard for arbitrary future callers. Current public routes check visibility before rendering; future callers should continue to check `visible` or use published querysets. This is a maintenance boundary, not a current leak.
- No confirmed pending payload leak, Org rating fabrication, stale inherited contact exposure, unsafe URL scheme, or analytics subject duplication in inspected source. This is source evidence; rendered browser and isolated integration tests remain lead-owned.

## Checks and handoff

Executed: Codebase Memory `home-ramin-kidsmap`, full generation `2026-10-02T11:32:24Z`, relevant path coverage metadata match with best-effort caveat; bounded source/routes/template/test inspection; synthetic `urllib.parse.urlsplit` reproduction (`https://[invalid` → `ValueError`). No isolated Django tests, browser, live SMTP, production or external calls by this reviewer. Graph absence was not used as proof.

Handoff: **frontend-reviewer** for final QA04/browser evidence and stage18 report; **django-reviewer** for regression coverage if resolver or contact semantics change. Source recheck closed SEC18-01; final isolated test result remains lead-owned.
