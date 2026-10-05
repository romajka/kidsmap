# Stage26 — bounded Event schema / legacy transition

IN_PROGRESS. Canonical database-reviewer `/root/stage26_domain`; APPROVED IMPLEMENT inherited from parent stage26. LOCAL HEAD `015d031d8eb17114bd860159dde805b38df3c13c`, dirty WORKTREE21–26, C:\kidsmap. Incoming265 files preserved by parent in `26-entry-manifest.json`; production NOT_CONTACTED, commit/push/deploy/27+ NOT_RUN.

Owned scope: Event fields/invariants in `src/catalog/models/place.py`, `models/event_domain.py`, model exports, migration0133, `test_task33_event_schema.py`, this report. Other workers own services/ACL/query/UI; their edits are preserved.

Plan: test-first PostgreSQL XOR/online/aware-interval/history/snapshot guards and isolated seeded0132→0133 migration; observe causal RED via parent-coordinated harness; add bounded fields and append-only history; conservative legacy migration with precise status rollback; run GREEN plus all Task33 via parent. No shared mirror concurrent harness runs.

Schema agreement: `organizer_organization`/`organizer_specialist`, `organizer_resolution=resolved|legacy_unresolved`, `event_format=physical|online`, `occurrence_state=scheduled|cancelled|rescheduled`, `occurrence_version`, `venue_label`, six-key `venue_snapshot` (`label,address,district,metro,lat,lng`), readonly `legacy_publication_status`. Unresolved historical records retain both organizer FKs null; new service creation explicitly resolves one organizer. Never infer organizer from name, owner or venue.

Publication statuses remain draft/pending/published/rejected. Old expired/cancelled convert to published only with proven published_at, otherwise draft. Snapshot on historical published records uses Event own location columns exclusively; related Place today is not historical evidence. Readonly legacy status marker preserves exact reversal. No production data audit or transfer claimed.

Discovery: Codebase Memory C-kidsmap ready; Event graph class resolves to place.py. Exact path coverage returned coverage_unavailable/metadata_changed for operated files; scoped source verification used. Canonical role, registry, engineering/audit contracts and relevant architecture/source-of-truth/database/legacy/business/schedule/deployment references read. TDD and verification-before-completion applied.

Checks: parent-coordinated causal RED `wsl -d Ubuntu-24.04 -u root --exec /bin/bash /mnt/c/kidsmap/docs/task33/qa26/backend_run.sh all stage26-all-red2-20261003 --label catalog.testcases.test_task33_event_domain --label catalog.testcases.test_task33_event_schema --label catalog.testcases.test_task33_event_public`:31 tests,17 failures +17 errors (subtests counted),0 skipped; wrapper1/child34. Evidence `/root/task33-evidence/stage26-all-red2-20261003`; missing fields/history model/migration APIs were expected causes. Guards enabled, external credentials absent,166 applied/0pending, cleanup PASS. These are preimplementation failures, not a GREEN result.

Parent follow-up `/root/task33-evidence/stage26-target-green1-20261003`:52 tests,5 failures,0 errors. Own7 schema/migration tests exposed exactly3 causal negative subtest failures: unknown approval timestamp invented during an unrelated edit; reconstructed-PK history save; bulk conflict-upsert overwriting history. Other schema cases, including forward/reverse/reapply migration and reconciliation idempotency, passed. Parent owns other2 failures and their remediation; no assertion relaxation.

Bounded fixes: approval timestamp is assigned only on initial publication, never on an already approved unknown-time row edit; occurrence history save rejects caller-supplied PKs to prevent Django update fallback (including concurrent constructed-PK overwrite); bulk conflict-upserts rejected. Normal save/update/bulk_update/delete guards remain. Actor FK retains SET_NULL (source contract); an additional direct account-deletion test was not run by this role. Direct SQL immutability is not claimed. Fixture reversal validates original legacy rows only; populated-domain operational rollback NOT_RUN.

Own five Python source AST parses and scoped `git diff --check` passed after fixes. Final GREEN pending parent run.

Named handoff: django-reviewer `/root` owns fresh organizer ACL, snapshot collector and atomically recorded future reschedule/cancel; public reviewer owns list/calendar parity and historical snapshot consumers.

## Late approved-format review

Parent scoped follow-up: preserve first approved physical/online format when content returns to draft; reject during generic ModelForm validation before save. Added2 meaningful tests (schema total9), each physical→online and online→physical. Physical case also retains an unknown historical approval timestamp and the approved snapshot across unpublication.

Parent RED `/root/task33-evidence/stage26-format-red-20261003`:17 tests,4 failures +1 error. Four causal subtest failures cover model rejection and generic ModelForm._post_clean in both directions. Other7 schema/migration tests passed. The additional error was parent's invalid synthetic Specialist fixture keyword `full_name_az` (corrected to actual `name`), not an application regression.

Changes after RED: `models/event_domain.py:_approved_occurrence/validate_event_format_history` recognizes published_at, current published state or retained approved physical snapshot; `Event.save` rejects format changes before clearing geography/snapshot; `Event.clean` reads the persisted source and reports `event_format` during ModelForm validation. An explicit trusted occurrence-service flag retains its existing capability; current reschedule service does not modify format. Generic clean retains pure-field validation, while admin's existing _post_clean performs full historical validation with nonfield error mapping. Final fresh GREEN pending parent.

## Final parent verification

Root execution `stage26-task33-final2-20261003`:551/551 unique tests PASS, including all9 schema cases and72 new Event cases;0F0E0skip. Source: reports/26-results.json and retained `/root/task33-evidence/stage26-task33-final2-20261003`. `check`/`makemigrations` exit0,167 applied/0 pending, guards enabled, external credentials absent, cleanup PASS. This is attributed parent execution, not independent execution by the schema implementer. Independent security final19/19 checked15 current critical source hashes, including Event model/helper/migration, source admin and service. All earlier PENDING schema GREEN notes above are resolved by this fresh execution; production/operational rollback scope remains NOT_RUN.
