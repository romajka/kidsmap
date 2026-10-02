# Stage07 canonical business actions

Executable source: `src/catalog/services/place_access.py:permission_configuration`, `src/catalog/services/business_team.py:has_action`. HTTP configuration: GET `account/business/permissions/` (authenticated). Clients consume backend config; do not copy enum/rule definitions.

| Target | Action | Direct owner | Explicit employee grant | Network Place actions imply it |
|---|---|---|---|---|
| Place | place.view, place.edit, place.stats.view, place.reviews.reply, place.reviews.report | Yes | Concrete Place or current selected/all_network Org grant | Place actions only |
| Place | place.team.manage | Owner/creator while unowned | No | No |
| Place/Org | ownership.transfer | Current owner | No | No |
| Organization | organization.view, organization.edit | Yes | Separate explicit action | No |
| Program | program.manage | Owner of current Organization | Separate explicit action on that Org | No |
| Organization | branch.create | Yes | Separate explicit action | No |
| Organization | organization.team.manage | Owner | No | No |
| Platform | place.publish, place.reviews.moderate | Business ownership grants nothing | No | No |

Business review reply/report are permission contracts; new business reply/report UI/workflows are not implemented here. KidsMap moderation stays in platform admin. Legacy MANAGER/EDITOR/MODERATOR stored identifiers stay compatible; presets no longer include team.manage or reviews.moderate. Explicit grants cannot contain publication/delegation/moderation/transfer actions. NULL-place legacy records never authorize network access.

selected_places stores exact IDs and requires current confirmed business affiliation. all_network includes future confirmed branches; it does not imply Org/Program/branch.create. Direct Place team survives detach. Org access disappears when link/ownership proof is no longer current. Grant base owner/version is checked on every access; revoked/suspended/inactive/volunteer accounts receive no business access, even with cached user objects.

Team mutation API: POST `account/business/team/{place|organization}/{target_id}/{action}/`, JSON + CSRF. Actions invite/accept/reject/cancel/grant/leave/confirm/suspended/branch. Nested invitation/grant target is checked again under parent locks. Grant/confirm require expected_version; stale returns409; forbidden403; malformed400; missing404. Invitations expire after7 days (engineering default), snapshot owner/version/current grant version and selected Place ownership versions; expired/canceled/stale/replayed acceptance rejected. Existing pre-migration invitations without trustworthy version/expiry require owner reissue; no consent inferred.

Parent lock order Organization→Place(s)→grant/invitation serializes team transitions against transfer/detach/legacy authorized saves. Transfer suspends grants and cancels pending invitations. Owner-only suspended list + explicit versioned confirmation restores chosen employees. Branch creation assigns Organization owner and keeps employee created_by; selected IDs are never extended.
