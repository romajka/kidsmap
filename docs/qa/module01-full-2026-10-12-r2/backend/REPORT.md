# ACCEPT-01 r2 backend gap probes

Django-reviewer `/root/accept01_contracts`, AUDIT ONLY delegated slice of approved `docs/superpowers/plans/2026-10-12-module01-completion.md`. Application repairs QA09/QA10 owned by parent/integration; this agent changes only own backend evidence/probes. Checkout `/home/ramin/kidsmap`, branch task33-progress, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51. Prior dirty docs/reports and concurrent changes preserved; active_run NONE unchanged. PRODUCTION NOT RUN.

## 1. State / inventory

Canonical source taxonomy:17categories/104subcategories in `taxonomy-source-inventory.json`; actual isolated DB validated105pairs:104migration-seeded plus1quality-fixture subcategory; probe output states105/17. Shared validation `catalog_structure.validate_taxonomy` checks actual parent relation, allows null/null compatibility, rejects unknown code/mismatched subcategory. This is not evidence all104 rows were selected through native UI. Native category/subcategory permutations owned by parent.

Standalone owner creation uses existing OwnerPlacesController/form/publication pipeline. Organization branch route POST `account/organizations/<org>/branches/create/` → BranchCreateForm → `business_team.create_branch`: current branch.create authorization, AZ name/category, duplicate guard and explicit allow_separate, owner inherited from current org owner, inactive draft, business affiliation version-pinned. Informational links do not create business grant. Probe covers owner,foreign owner,duplicate,separate branch; delegated branch.create role/native workflow remain parent/integration evidence.

## 2. Strengths / contracts

Backend remains final validator. Publication and private drafts re-read active actor and current object authorization, then compare versions inside row locks. Actor-bound photo UUID cache accepts committed retry with same result without new candidate. Gallery IDs/order/file names use source contracts mapped in r1 backend report; r2 adds caps/limits/real format probes.

Coordinates0/0 are numerically valid but outside geographic dataset coverage; can persist an unpublished draft but publication requires valid geographic contract. No-point and partial/out-of-range cases are distinct: range invalid status vs absent optional-point locality fallback; no conflation with falsy0.

## 3. Findings

No new finding assumed from source. Final23tests PASS exit0; no new backend application defect confirmed in this bounded corpus. Existing findings09/10 repair acceptance owned by parent/integration; custom negative probes cannot close them.

## 4. Tech debt / discovery

Codebase Memory graph discovery reused from r1 and exact image normalizer symbols queried again. Actual source read for image/photo/form limits, taxonomy/branch, geographic assignments, publication and ServerDraft behavior; source-entry records per-path hashes. Graph absence not evidence of unused paths. Library docs not substituted for current business code.

## 5. Isolation / risks

Own PostgreSQL TEST DB test_accept01_backend_20261012_r2 on previously owned START container, Docker binding freshly inspected127.0.0.1:52523 only (`postgres-loopback.json`). Test DB distinct from START/UI/integration DB. Credentials read only locally from ignored START scratch; no .env loading. Own LocMem cache/media/private-media/email under ignored r2 backend scratch. Environment allowlisted; DJANGO_TESTING=1; external socket connect/connect_ex rejected except owned PG. Fresh own RU/AZ/EN gettext native profile at `.tmp/module01-full-2026-10-12-r2/backend/locales`, sole LOCALE_PATHS verified before django.setup. No shared MO mutation.

Source-entry includes concurrent root changes; application business services unchanged. Parent authorized running while additive photo metadata patch was underway; this suite does not assume byte-identical final transport until final source gate. Runtime tests are TestClient/services, not a running rendered browser process.

## 6. Legacy / removal

No deletion candidates or app changes. Existing-live readiness and scalar prices remain intentional compatibility consumers. Preserve all previous reports/stands.

## 7. Exact checks and gaps

Commands:

- `.venv/bin/python scripts/build_isolated_locales.py build --source-locale locale --output .tmp/module01-full-2026-10-12-r2/backend/locales --locales ru az en --compiler native` →exit0,3catalogues (`locale-build.txt`).
- `.venv/bin/python scripts/build_isolated_locales.py verify --manifest .tmp/module01-full-2026-10-12-r2/backend/locales/manifest.json --source-locale locale` →exit0.
- Compile own3probe scripts in memory →exit0, no pyc/artifact writes.
- `docker inspect start-local-2026-10-12-r1-pg --format '{{json .HostConfig.PortBindings}}'` →exit0, only loopback binding.
- `.venv/bin/python docs/qa/module01-full-2026-10-12-r2/backend/run_probes.py > docs/qa/module01-full-2026-10-12-r2/backend/probes.txt 2>&1` →attempt1 exit1,23tests22PASS/1fixture ERROR in6.851s. Second transactional testcase had flushed EDU taxonomy from first; own fixture now recreates EDU before setup. Existing assertions/application unchanged; `probes-attempt1.txt` retained. Final rerun exit0,23tests PASS/0FAIL/0ERROR/0SKIP in6.160s; Django check0issues; own TEST DB destroyed. Exact output `probes.txt` retained.

Prepared23tests:10r1 endpoint/private draft/CSRF/CAS/photo ownership negatives,13new backend gaps. Four real encoded JPEG/PNG/WEBP/HEIF inputs normalized toWEBP; empty/corrupt/15MiB+1/mismatched MIME/GIF rejected; synthetic PNG headers12001side/56MP rejected before decode; valid2600side resized to2400; gallery11files and two actual12MiB uploads exercise cap/batch gates. HEIF plugin/encoder preflight supported. Dimension/pixel header probes are actual files but deliberately non-decodable over-limit headers; positive50MP boundary NOT RUN. Native browser cap/dedup/processing and large physical uploads belong to parent.

Real simultaneous barrier-release tests use separate DB connections/threads, not sequential stale calls: same candidate source/version0 requires one commit+one candidate conflict; private draft same expected version1 requires one commit+one conflict/version2. They prove narrow two-writer backend cases, not exhaustive concurrent ownership/pricing/admin races.

Private photo upload test verifies file outside MEDIA_ROOT, owner attachment200,foreign/guest403. Team editor proposal succeeds then publication denied, revocation/inactive deny. UUID retry ignores first committed response hypothetically and confirms second returns identical result/no version increment; true browser loss after commit and native retry remain parent evidence, not simulated away here.

NOT RUN by this slice: all native transitions/rendered18cells/keyboard, full configured Django/Node corpus and cleanHEAD comparison (integration owns),physical devices/screenreader/external providers/production. No fullmodule PASS inferred.

## 8. Recommendations / handoff

Root kidsmap-orchestrator/browser-qa: reuse canonical inventory and limits; exercise native standalone/network branch/category lifecycle and geographic gate separately from pure number validity; owner absent price_mode control is N/A for that consumer, admin all4policies required. Real browser saved-file promotion must wait both materialization reads/busy0; loading-state rejection is not a server422. Confirm immutable candidate/live via parent read-only transaction readback.

Integration-reviewer: combine own negative gap evidence with full discovery/repair tests; source gate any changed business/transport path after probes before final claims.

## 9. Priority / preservation

No new provisional ID until fresh failed behavior is reproduced and reconciled by parent. No app/assertion edits, foreign process stops, active_run changes, commit/push/deploy/production.

## Source gate after probes

Compared11source paths to entry. Changed concurrent approved paths: src/catalog/photo_views.py, static/js/owner_place_continuous.js. Exact per-path hashes `source-entry.json`/`source-end.json`; all business paths used by gap probes unchanged. Additive transport metadata repair belongs to integration, whose final tests/native chain parent owns. No final whole-checkout acceptance inferred.
