# Stage 09: draft transport and UI states

The current owner wizard keeps its browser recovery copy. New owner screens in stages 12–14 will use this server contract. Autosave never submits a publication candidate or changes Place/Organization live fields.

## Transport

- `POST /api/drafts/` (`application/json`, Django CSRF): `draft_id` (client-generated UUID recommended for replay safety), `target_type`, optional `target_id`, `schema_version: 1`, `source_version` (0 for new), `expected_version` (0 on first write), `fields` (allowlisted partial content). A retry with the same UUID and identical first payload returns the same version 1 draft. A different payload with version 0 returns 409.
- `GET /api/drafts/` lists only the signed-in actor's currently authorized drafts, metadata only. `GET /api/drafts/<uuid>/` restores fields after a fresh permission check. The same API works on another device after sign-in.
- `POST /api/drafts/<uuid>/photo/` accepts one `photo` plus `expected_version` as multipart data. Only a successfully normalized and stored image updates the draft and version. `GET` on that path streams the private photo after a fresh permission check; there is no public media URL.
- `POST /api/drafts/<uuid>/materialize/` accepts `{"expected_version": n}`. It creates at most one nonpublic Place from a sufficiently filled new Place draft; missing name/category yields 422. The draft photo remains private and is not copied into public media at this step.
- Successful responses include `draft_id`, `schema_version`, `version`, `source_version`, `saved_at` (ISO timestamp), `status: server_saved`, `errors: {}`, `photo_saved`, target identity, and fields on detail/save. Responses have `Cache-Control: no-store`.
- Validation/shape error: 400, `status: invalid_request`, structured `errors` and `submitted_fields` where supplied. Incomplete materialization: 422 and field errors. Foreign or revoked access: 403. Missing draft: 404. Stale draft/source/schema: 409, current draft metadata and untouched `submitted_fields`. Server failure during JSON save: 503, `status: unavailable`, submitted fields retained in the response. A 409 never silently merges two devices.

## UI state mapping for later screens

| State | Trigger | User-facing meaning/action |
|---|---|---|
| Browser-only | Local write, no acknowledged POST | Saved only on this device; file inputs are unsaved. Retry server save. |
| Saving | POST in flight | Keep current input and disable only duplicate in-flight submit. |
| Server saved | 2xx with matching draft ID/version | Show `saved_at`; on another device retrieve from server. Photo is saved only when `photo_saved` is true after upload 2xx. |
| Offline/unavailable | Offline, network failure or 503 | Keep browser copy and visible input; show retry, never claim server save. |
| Conflict | 409 | Keep local text and offer explicit reconciliation with current server version. Never replace it automatically. |
| Validation error | 400/422 | Keep input, show returned field errors, allow correction. |
| Forbidden | 403 or account switch | Stop autosave and hide previous account's server content. Require fresh authorization; do not retry with stale actor. |

Browser fallback key must contain account ID and object or creation-session identity. The existing owner wizard keeps its `data-draft-key` value for form compatibility and adds account ID when building the localStorage key. Files are never serialized to localStorage. The later screen integration should generate and retain one client UUID per create draft, debounce POSTs, send the latest acknowledged version, and wait for the photo upload acknowledgement before showing a server-saved file state.
