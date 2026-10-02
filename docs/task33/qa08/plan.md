# Stage08 publication implementation plan

Goal: approved live content and versioned candidates through the existing VolunteerPlaceRevision pipeline.
Architecture: typed nullable targets on the existing revision; one locked patch service. Place legacy fields remain approved, Program propagation uses the same transaction. Existing forms adapt validated data to patches; no new screens or autosave.
Spec: docs/task33/prompts/08.md, architecture sections редакции/публикация.
Constraints: only08; preserve05–07; no production/commit/push; clean isolated QA04 harness; real independent review required.

- [ ] Add failing real ORM tests for retained live descriptions, disjoint immediate price edits, stale overlapping approval/schema/source rejection, whole dependent bundles, ACL/revocation, closure/readiness and Program propagation.
- [ ] Extend models/volunteer.py with explicit typed targets and schema/base/dependency metadata, additive0120 generated in isolated PG. Existing rows remain Place revisions.
- [ ] services/publication.py provides propose(actor,target_type,target_id,patch,schema_version,expected_version,revision_version,submit,explicit_save), review(actor,revision_id,version,approve,note), publish(actor,place_id,expected_version), snapshot/dependencies. Only allowlisted content fields, fresh ACL under Organization→Place→Program→Activity→revision locks. Approval patches only changed fields, compares those fields and fresh dependencies; immediate price amounts/schedule apply only explicit save and outside dependent bundles.
- [ ] Adapt volunteer save/review, owner form save/submit, admin save/publish, CSV/JSON imports to the shared contract. Reject stale schema/base tokens before mutation. Preserve old public status during editing.
- [ ] Unify readiness and compatibility visibility; optional photos/coords, public-space contact exemption, active approved inherited business contacts. Confirmed closure retains approved detail but excludes listings.
- [ ] Run targeted05–08 and affected suites, isolated migration/check/probes, PG races, full baseline comparison. Fix regressions without weakening original assertions.
- [ ] Independent review and own isolated verification, source SHA/inventory, report08/journal/README/decisions handoff; release only own active_run. Stage09 remains untouched.

Test commands: python3 docs/task33/qa04/run.py --mode all --label catalog.testcases.test_task33_publication --output /tmp/task33-08-red; final add schema/ownership/permissions labels; full without labels. Each output path unique.
