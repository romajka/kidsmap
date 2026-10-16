# OFFER-QA-07 offline candidate-base supplement

Implementation inside the previously approved plan `docs/superpowers/plans/2026-10-14-offer-qa07-stale-draft-restore.md`: same OFFER-QA-07, same permitted `static/js/owner_place_continuous.js`. User also requested completion of every module05 problem2026-10-14. No new source files/business contracts/ACL/CAS/schema/PO.

Fresh RED: `offline-recheck.result.json` — simulated unavailable draft POST, A cached input without server draft ID; B native explicit candidate-only save leaves live source_version unchanged; normal A reload silently overlays B. `candidateVersion` always0 because template has no candidate_version input; actual candidate version already exists in server-signed publication_token. Earlier scoped07 PASS addressed other paths; offline-only case reopens07 until this acceptance.

- [x] Read candidate metadata from existing hidden publication_token when no direct candidate field exists. Base64URL decode only candidate integer; failed/unavailable metadata =>null, requires explicit recovery. Backend signature/CAS remains authority; no opaque token contents in evidence/localStorage and no restored token field.
- [x] Preserve local fields and recovery backup; matching actual source+candidate resume remains valid. Existing legacy candidate0 cache will require explicit choice when current real candidate differs.
- [x] In candidate-conflict UI use existing translated server_conflict message instead of raw English technical detail. Preserve field-target messages for other errors. No new translation keys.
- [x] Browser RED→GREEN offline no-ID/same-source new candidate; ordinary local current-base resume, cached retired server row, source-version drift, malformed metadata fallback; RU/AZ/EN ×6 widths recovery choice/focus/layout. Real private restore never applies live data.
- [x] Backend334 methods already passed on unchanged Python code. After JS-only patch, run node syntax and native affected checks only; refresh owned runtime receipt, no full repeated backend suite. Record phased source hashes/failures/SIMULATED/NOT RUN and preserve all other source/stands/active_run.

Completed locally: native offline RED3PASS/1FAIL → GREEN4PASS, recovery68PASS/18cells, malformed metadata4PASS, classified conflict8PASS. Node syntax exit0. Current-base private resume and explicit old-input recovery preserve live. Source phases/foreign locale blocker and full-module OFFER10 FAIL are separate; no general module PASS claimed.
