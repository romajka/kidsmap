# Native UI handoff — source and historical selector checklist

Snapshot: C:/kidsmap, task33-progress, HEAD8d188b316f800fbedf0b1e376905dfd4924cb1b6, dirty WORKTREE, active_run NONE. Role django-reviewer; source inspection only. Root owns all native browser observations. Paths below use RU; AZ has no language prefix, EN `/en/`.

## Organization without branches and content moderation

1. Network owner `/ru/account/organizations/create/`: `[data-org-create-form] [name=name_az]`; optional translations in `#disclosure-translations`, contacts in `#disclosure-contacts`, description in `#disclosure-description`. Open the appropriate `details > summary` before interacting with a hidden input. Submit the scoped form.
2. Detail `/ru/account/organizations/<org>/`: edit only `[data-org-edit-form]`. There are unrelated branch/program `name_az` inputs. Autosave status is `[data-draft-status]`; wait for the server result before explicit `[name=submit][value=1]` to avoid testing a harness race.
3. Submit produces pending `VolunteerPlaceRevision`; live Organization remains draft until review. Read-only QA state must expose live status and the candidate status/version/payload separately.
4. Native rejection: moderator `/admin/volunteer/moderation/?kind=organization`, link `/admin/volunteer/moderation/content/<revision>/`. Fill `[name=reason]`; button[name=action][value=return] gives editable `rejected`, value=reject gives final `declined`; value=approve approves. Reason is required in the UI for all three decisions.
5. Alternatively approve from `/admin/catalog/organization/<org>/change/`, `[name=action][value=approve]` posts its content transition. This is not ownership claim approval. The business editor does not expose reject; use the hub for return/reject.
6. Public `/ru/organizations/<public_uuid>/` after status published + approved_at. No-branch organization is valid.

## Place and canonical branch request/confirm

1. Place owner `/ru/account/places/create/`, continuation `/ru/account/places/<place>/edit/`; explicit `[name=form_action][value=save_draft]` and value=submit. Long form has independent section navigation; preserve the saved canonical token, never manually construct an old version.
2. Create/publish the Place before a cross-owner request. To exercise waiting second-owner consent, the network owner and Place owner must be different actors. Same owner confirms both sides during one request and immediately connects; this is the implemented contract.
3. Ready Place selection `/ru/account/organizations/<org>/connections/`: `[name=place_ids][value=<id>]`, button[name=action][value=preview]. The preview `[data-confirm-form] [name=consent]`, button[name=action][value=confirm] invokes canonical request_join/confirm_join, not a direct FK edit.
4. Other owner sees `[data-join-request=<request>] form` in own Org workspace or join-confirmation inbox. Actual action `/ru/account/organizations/<org>/requests/<request>/confirm/`. Read-back request status plus both owner timestamps and Place.organization_id.
5. The canonical request binds ownership versions, owner IDs and Place.content_version. An intervening Place content save may stale the request; it must be explicitly recovered rather than silently approved.

## Program, Activity, groups, tariffs and schedules

1. Org detail `form[action$='/programs/create/'] [name=name_az]`, scoped submit creates a draft Program and opens `/ru/account/organizations/<org>/programs/<program>/`.
2. Program fields name_az/ru/en,description_az/ru/en,category,subcategory; hidden expected_version/revision_version. Submit button name=submit value=1. When already referenced by Activities, check impact_confirmed after reading affected branches. Program approval uses the same content moderation hub or `/admin/catalog/program/<id>/change/` approve transition.
3. Place editor `[data-pc-add-activity]`; `.pc-activity-card` fields `[data-offering-key=program_id]` for a linked approved Program or name_az/description_az/category_id for a local Activity. `.pc-group-card` fields name_az,age_from,age_to,lesson_format,language,schedule_text,conditions_az. `.pc-plan-card` fields title_az,price and other actual DOM controls. Nested controls are checked against current JavaScript/template; historical modules05 functional1/pricing/schedule scripts are selector examples only.
4. Explicit draft save, reload; serialized hidden `[name=nested_pricing]` is a UI round-trip aid, not proof of approved database storage. Read-back candidate nested_pricing and live Activity/OfferingGroup/PricingPlan rows; approve then verify public groups/prices.
5. Place opening schedule is separate from group schedule_text. The shared publication service allows explicit Place opening schedule and isolated amount-only changes live immediately; nested_pricing is generally candidate-gated. OfferingGroup.schedule_text is immediate through its own target. A Place nested tree containing a group schedule does not become globally immediate by that rule.

## Specialist proposal, person claim, cooperation and practice locations

1. Author `/ru/account/specialists/proposals/new/`; UUID draft continuation `/proposals/<uuid>/`. Step controls `[data-owner-step-target="0".."4"]`. name,experience_years,photo; first-step explicit draft and reload before completing.
2. Direction chips `[data-spec-code=child_psychologist]` or a real current available code; ages and language checkboxes. Consultation format `[data-owner-format-card=both]` or actual format cards.
3. Practice rows locations-0-address/region/price_per_session/phone/is_active/is_primary, `[data-practice-add]`, locations-1-place/region/etc. Real select choice must belong to the actual available fixture Place; do not inject DOM options. Stand-alone address and linked Place are separate practice modes.
4. General price_from/to,duration_minutes,phone; bio_ru/education_ru after `[data-owner-lang-tab=ru]`. Save+reload and native submit. Submission creates pending Specialist and redirects claims; authorship does not grant profile/person/document rights.
5. Claims `/ru/account/specialists/<id>/claims/`: button[name=action][value=request]. Dedicated claim reviewer `/ru/account/specialists/<id>/review/`, button[value=claim_approve] (claim_reject requires reason). Verified person may edit `/account/specialists/<id>/` and upload certificates.
   Profile publication is a separate native admin action: `/admin/catalog/specialist/?id__exact=<id>`, `[name=_selected_action][value=<id>]`, `[data-bulk-submit=mark_published]`. Source mark_published sets published/is_active; it does not establish the person claim.
6. Network `/ru/account/organizations/<org>/specialists/`: specialist select,role,start_date/end_date; form hidden action=propose, scoped submit. Person `/ru/account/specialists/<id>/invitations/` and network both confirm `[data-employment-id] button[value=confirm]`; either side cancels value=cancel. Employment consent does not grant private documents access or replace practice-location links.
7. Certificates `/ru/account/specialists/<id>/certificates/`: document_type,name,file,publish; form hidden action=upload. Identity must stay private; reviewer document_approve is independent from the verified person's later publication consent. Download `/ru/specialists/documents/<document>/download/` is ACL-protected. Repeat with outsider/network staff before calling it secure.
8. Specialist owner profile is not shared candidate/live publication: direct locked save changes fields and sets draft/pending; claim and publication are separate. Do not assume the Place candidate retention policy applies here.

## Event organizer versus venue, occurrence actions

1. Event organizer `/ru/account/places/events/create/`: organizer_organization or organizer_specialist (exactly one authorized current owner), category,name_az. First partial draft then reload.
2. Steps `[data-owner-step-target="0".."2"]`; event_date,start_time_input,end_time_input,end_date with `[data-event-end-date-toggle]`, ages,price_text,phone,description_az. event_format physical/online.
3. Physical venue is a separate related_place selector. Use the actual available published branch; for custom venue use venue_choice_switch custom,region/district/address. Online must not require a physical address. Photo on step2; explicit save_draft/submit.
4. Event has independent moderation/state handling, not VolunteerPlaceRevision. Owner can edit only draft/rejected content, pending/published content edit rejection is deliberate source policy. Organizer cannot be changed through ordinary editing. Published venue_snapshot is immutable historical venue facts.
5. Occurrence manage `/ru/account/places/events/<id>/manage/`, `[data-occurrence-form]`, reason,start_datetime,end_datetime; actual buttons have formaction ending `/reschedule/` or `/cancel/`, hidden expected_updated_at. Future aware intervals use Asia/Baku. Reload and verify own card, Org feed, filters/map, counters and stale second tab.
6. Source hypothesis, not a finding: organization public feed currently filters occurrence_state='scheduled'; after successful reschedule, check whether the still future published Event disappears from the Org feed. Exact source public_details.py, org_events query. Root must reproduce and establish expected product behavior before assigning CROSS ID.

## Detach and employee revocation

1. `/ru/account/organizations/<org>/branches/<place>/detach-preview/`: read impact, `[data-confirm-form] [name=consent]`, button[value=confirm]. Canonical detach nulls affiliation and Program FK, materializes approved Program text/source/version snapshot, preserves Activity/groups/prices, direct grants and publication. Network rights stop because current business affiliation stops.
2. Employee native invite `[data-team-form]`: email,role,scope and selected place_ids; inbox `/ru/account/notifications/` accepts current invitation. JSON API versions are not DOM form versions.
3. Current Org staff/grant/invitation rows have no revoke/role/cancel controls and admin grant screens are read-only diagnostics. Historical ACCESS-QA-03 must be freshly rendered before retaining it as confirmed. Native revoke is NOT RUN if no control exists; independent service/API test can still verify ACL invalidation but does not replace the UI path.
4. CSRF JSON `/ru/account/business/team/organization/<id>/grant/` supports grant_id,expected_version,active=false etc; foreign target IDs must reject. This is HTTP backend evidence only if used by QA directly.

## Sections and intersection checks

Use actual SiteSettings admin UI for events/specialists/organizations OFF/ON; read-only state may hash owned fixture data but must not mutate transitions. Check menu, direct URL, search/map and matching Org nested feeds, then restore through UI. All screenshots must be created afresh on module13 stand. Legacy temporary Place event visibility is separate from Event model visibility. Real SDK/Google/email delivery remain NOT RUN when transport is blocked; a fake map/report adapter is SIMULATED.
