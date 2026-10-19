# SITE-QA-23 — add-only Continue creates image then opens forbidden editor

**OPEN / P3 / LOCAL, 2026-10-18.** Separate pre-existing navigation contract, not an unauthorized write or SITE20 regression. [Fresh prepatch native baseline](../evidence/browser-add-baseline.json): add-only gallery actor can legally add; `_save` POST302→admin index200, `_continue` POST302→new object's change GET403, each exactly1new row/1adminLog/file. Original template already offered both actions on desktop.

[Actual applied-source matrix](../evidence/browser-add-green.json) reproduces6Continue403 paths:3languages×360/1440, after invalid-file200/no-write and valid retry. All12valid native additions persist exact bytes/caption and one log;6Save exits land200. The6landing200 failures are deliberately retained, not changed to green. New mobile editable marker exposes the same existing route behavior at360.

Source: installed Django6.0.2 ModelAdmin.response_add unconditionally redirects `_continue` to `obj_url`; `_changeform_view` requires change on POST and view/change on GET. `SiteGalleryImageAdmin` has no response_add override. [Installed source references](../evidence/library-contract.json). No source change to this path in approved SITE20 diff. Backend ACL remains correct: actor has add only and GET existing/new object is forbidden.

Impact: successful add is presented as403; retry may duplicate an image (duplicate retry impact not independently tested). Confidence high for native route/storage behavior. P3 navigation/usability; production UNKNOWN. Owner Django-reviewer/frontend-admin. Next separate concrete policy/plan: either offer only Save/exit to add-only actors or route successful Continue to an accessible destination. Do not grant change permission as a workaround. No fix of SITE23 authorized/applied here.

SITE20's view-only forbidden save presentation is closed within its approved exact scope. Shared-template controls/permissions tested separately from post-add navigation; no blanket all-native PASS. With separate SITE24 statistics message overflow, Module10 now15OPEN(9P2/6P3)=13−20+23+24+25, full acceptance pending.
