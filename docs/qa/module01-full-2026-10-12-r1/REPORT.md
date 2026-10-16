# ACCEPT-01 — fresh full-module audit, 2026-10-12 r1

**Decision FAIL; no module01 sign-off.** Two confirmed local P2 findings PLACE-QA-09/10. Mandatory gaps are explicit. No application repairs. Existing PLACE-QA-01–08 scoped results remain valid historical evidence, not reopened by old r2.

Execution: /root lead/browser, independent integration-reviewer and django-reviewer with disjoint report ownership, canonical definitions read. Supports ran in parallel on separate TEST DB/cache/media; root UI transitions performed through browser. Parent consolidated findings; no independent visual specialist claimed.

## 1. State and snapshot

Checkout /home/ramin/kidsmap; branch task33-progress; HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`. Entry dirty WORKTREE only pre-existing untracked START report directory. End adds own audit dir and only row01 of module acceptance journal. active_run NONE unchanged. [Entry](entry.json), [runtime](runtime-version.json), [preservation](verification.json), [ledger preservation](ledger-preservation.json).

START preserved at127.0.0.1:51665/PID80429, DB start_20261012_r1. Own ACCEPT at **http://127.0.0.1:41039**, PID102556, separate DB `accept01_20261012_r1` on the already-owned fresh local PostgreSQL17.10 container loopback52523 (not a historical Windows port/container). Own media/private-media/cache/LocMem email, settings/runtime, fresh native RU/AZ/EN build; [manifest](locale-manifest.json) verified before django.setup and again at finalization. DJANGO_TESTING=1, DEBUG=False, no checkout .env, cleared allowlisted env; external app credentials empty, Python socket egress restricted to owned PG, browser external origins aborted. This is runtime guard, not OS network sandbox. No production contacted.

Runtime entry=startup=disk: 2792 files, digest `d8c972148de8ba3cb3cafb8f0a6aa9872efa4491a4ecc4bf005a2a6bd8629649`. Original shared MO/app/helper/tests unchanged; integration independently proves2826 tracked paths equal current clean HEAD. Clean-HEAD comparison is identical relevant source in this run, not comparison to donor8d188b31 or production. Input167/18/12442 inventory verified in START, sources present; no required document missing.

## 2. Strengths and performed native flows

- New standalone EDU Place via native UI → partial ServerDraft → reload/logout/login/continue → materialized draft → invalid ages/retained input/error focus → corrected submit → native reject with escaped reason → resubmit → approve/public → mixed name/address/price18 edit → draft/reload → candidate identity gated → approval/public. Rejection18 cells checked; native transitions not ORM. EN empty translation remained empty, public AZ fallback verified as display only.
- Separate network and ART branch created through native UI, free-admission tariff/photo/by-appointment hours saved/reloaded/submitted/approved; public branch observed RU/AZ/EN. Different Place/activity taxonomy also exercised in painting group.
- Tariff kinds free/exact/from/range/on_request and repeated exact switching, native explicit save/reload. Admin all4 price policies free/tariffs/free_entry_paid_services/events and repeated free/paid switch with actual keep-and-disable modal confirmed; no hidden select forcing. Owner continuous has no price_mode control: owner direct four-policy transition NOT RUN; policy testing applies to admin only.
- Opening hours modes by_appointment/variable/events/always_open/regular saved/reloaded; weekdays09–18 preset. Nested ART painting lesson with Saturday14–15/group price20 saved/reloaded/approved. Public contains separate hours and lesson data; scalar projection18–20 includes active group price, not missing amount18.
- Two gallery uploads/native order/reload, saved gallery→main (waited materialization busy guard), replacement/delete, invalid PNG visible row error, distinct-image cap10 and rejection of11th,10 save/reload then mass-delete to1, main clear/reload/restore. Duplicate content was correctly deduplicated in initial attempts. Native corpus not all HEIC/JPEG/WebP/source/pixel/batch-budget cases; backend/full configured image suites have explicit outcomes below. Current3 canonical main/gallery media resources returned200 and decoded: [media readback](public-media-readback.json), [READ ONLY DB fields](readback.json).
- No SDK clear/manual region/district save/reload, unsupported/denied geolocation explicitly SIMULATED. Manual out-of-range and half-pair error UI;0/0 strings preserved, not treated as empty. Geographic full publication gate for0/0 and genuine GPS/provider resolving NOT RUN. Number input rejects native letter keys; invalid-number fill error was own automation assumption, not app bug.
- Simulated dropped-save transport retained input; native retry persisted after reload. Double native click yielded one save request. Stale canonical candidate writes denied422 and input kept; newer canonical preserved in independent fresh view, but recovery UI FAIL (finding10). ServerDraft409 and UUID retry covered separately by backend probes; do not conflate these consumers.
- Real Chrome153, RU/AZ/EN×360/390/768/1024/1280/1440: owner empty/filled/age-error, category/nature/district labels, admin empty/filled/category popup/Escape/outside focus, guest published title/price/address/fallback/geometry. Native Tab cycles105 controls each of18 cells completed; exhaustive focus representation assessment of1px styled inputs remains inconclusive, not additional findings. Specific normal textarea Tab occlusion independently confirmed. Space/Enter/Escape/ShiftTab exercised in applicable selected controls, not every open modal state.

Initial fixture ORM only synthetic accounts/taxonomy/assets; all audited lifecycle changes were UI. Readback explicit READ ONLY with10s statement/2s lock timeouts. Real external APIs/providers/fonts unavailable or blocked; font fallback can affect rendering.

## 3. Real problems

- **[PLACE-QA-09](findings/PLACE-QA-09.md), P2 OPEN:** native nameAZ→descriptionAZ Tab focus hidden under fixed actions at768–1440 on three languages,12 observations/one cause. [Focused768 PNG](screenshots/focused-description-768.png).
- **[PLACE-QA-10](findings/PLACE-QA-10.md), P2 OPEN:** explicit candidate conflict translated summary promises separate current view; action hidden, generic retry state repeats stale token422. Input and canonical newer content preserved. [Conflict PNG](screenshots/candidate-conflict-recovery.png).

No new P0/P1 or data-loss/security finding established in this scope. HTTP422 alone not defect; historical PLACE-QA-08=CROSS-QA-03 not duplicated. New IDs do not prove newly introduced regressions.

## 4. Tech debt / test discovery

[Integration report](integration/REPORT.md): no-label618 IDs, wrapper1952, explicit configured2092; wrapper misses140 current tests, no-label misses1474. CROSS-QA-02 remains known OPEN outside this repair scope. Source/graph metadata checked; templates partial, graph not exhaustive oracle. Exact source/consumer checked for critical findings.

Original helper suite is WSL-specific; own native build/gates pass without modifying original tests or fabricating WSL markers. Current owner continuous has different tariff policy surface than admin/older wizard; callback/selector advice was corrected against actual DOM. Some old test-profile assumptions are not portable.

## 5. Risks

[Backend contract/negative probes](backend/REPORT.md) confirms public/candidate distinction: explicit hours immediate, monetary-only changes immediate under canonical conditions; identity/photos/location/nested conditions gated. Owner cannot publish; foreign IDs/private ServerDraft IDs/CSRF/gallery ownership/CAS protected in10 fresh probes. Test Client evidence not native-role18-cell proof.

Native recovery/UI/focus findings remain OPEN. No production/media privacy claim inferred; candidate normal media storage and private ServerDraft media are separate documented boundaries. Foreign processes/containers untouched; own native sessions only. No release/recovery/real-user data/real-provider acceptance.

## 6. Dead/legacy candidates

None proposed or deleted. No old evidence/assertions changed. Legacy guards/old wizard test mismatches retained as failures/limits; no inference of dead application code.

## 7. Tests, failures, NOT RUN

[Counts](counts.json), [432-cell state/role/language/width matrix](matrix.csv), [qualified observations](browser-observations.json), [exact latest result links](latest-results.json), [command ledger](commands.jsonl), [PNG SHA manifest](screenshots-manifest.json).

- Full explicit configured Django2092 actually attempted:2049PASS/18FAIL/25ERROR/0skip, exit43. All43 rerun sequentially with same failures.42 legacy QA04 guards/missing guard import => behavior behind guards NOT RUN;1 stale specialist assertion expectsGET200 where current routed controller intentionally redirects302. No assertion/guard manipulation. Separate PLACE40/40 PASS, backend custom10/10 PASS. Source equals HEAD; platform/legacy failures reproduced on unchanged source, not app regressions inferred from counts.
- Node117:116PASS/1SKIP exit0. Fresh actual HTML supplemental photo8:7PASS/1FAIL, injected old wizard assumes missing prev control on current continuous form; current native page has no corresponding error. Original helper9:2PASS/6environment FAIL/1Windows skip; separate native4/4 plus actual3-catalog build+verify pass. [Exact commands](integration/COMMANDS.md).
- Final qualified browser observations: `{'PASS': 403, 'FAIL': 13, 'NOT RUN': 3}`. These are observations, not unique independent tests; raw attempts preserved. Matrix432 cells: `{'PASS': 134, 'NOT RUN': 285, 'FAIL': 13}`. Some NOT RUN rows are role N/A, others genuine untested state boundaries; scope column disambiguates. Never infer whole18-cell states/roles PASS from a single native lifecycle.
- 183 retained native PNG, includes some own failed-attempt screenshots; reused own screenshot filenames may have been superseded by a later attempt. Final manifest attests retained images only, not every earlier attempt image. Raw attempt JSON/text preserved; no previous run artifact overwritten. No derived contact sheet counted native. Manual visual reads: focused768, invalid-image1440, admin-age-error1440, initial admin choice360 and gallery cap diagnostics. Other captures automated geometry/text checks; manual inspection of every full-size PNG not claimed.

NOT RUN/gaps: every category/subcategory and every branch variant; owner four price policies absent; complete native file-format/size/pixel/batch budget corpus; full0/0 geographic publication gate; true simultaneous races beyond tested sequential stale views/double click; lost response AFTER server commit (tested abort BEFORE send); complete modal/loading/conflict×all roles×18 cells; exhaustive manual keyboard/screenreader including styled hidden controls; guest private-page18 error matrix; physical devices/Safari/Firefox; real SDK/geocoder/GPS/OAuth/GA/SMTP/IndexNow/fonts/production/CI run. Other modules not automatically audited/repaired.

Own QA attempt errors retained and distinguished: long fictional category exceeded255 before seed corrected; hidden tariff select should use visible price-kind buttons; admin add needs native type selection/query; free-policy modal requires keep-and-disable confirmation; PNG names normalizeWebP; duplicate byte-equivalent gallery images dedup; promotion busy guard not server422; invalid-image error sits in rendered photo row; generic409 oracle wrong for explicit422 consumer; old `.errorlist` selector wrong for custom admin summary; open-age hides instead of disables field; focus1px geometry not exhaustive accessibility proof. [Harness events](qa-harness-events.json) and raw attempts keep failures visible, without app/assertion changes. HTML with form tokens only ignored scratch, never public evidence.

## 8. Recommendations and handoff

No automatic repairs. [PLAN PLACE-QA-09](findings/PLAN-PLACE-QA-09.txt) and [PLAN PLACE-QA-10](findings/PLAN-PLACE-QA-10.txt) are separate copyable fresh recheck/planning prompts; they are NOT implementation approval. Concrete implementation plan still required before any fix. Later ACCEPT-01 rerun must cover findings and outstanding mandatory gaps.

By global guide priority, next recommended task remains **PLAN SITE-QA-01 (P1 ACL)**, after explicit selection; [next prompt](next-prompt.txt). New Place findings remain OPEN. Do not silently add scope or treat this report as implementation plan. Historical r1/r2/module13 MASTER not rewritten; only module01 current journal row linked to this audit.

## 9. P0–P3 and preservation

P0=0,P1=0,P2=2,P3=0 new findings. Overall FAIL, scoped successes/NOT RUN explicit. HEAD/source/helper/shared MO/START docs and process/foreign container IDs/active_run preserved; see verification.json. Only row01 journal modified, all other lines byte-equal. No app/config/schema/assertion fixes, commit/push/deploy/production, foreign cleanup/restart. Own testing databases cleaned by their runners; own START and ACCEPT servers remain available; dedicated browser session closed after audit. Credentials remain ignored scratch with mode600; actual credential-literal scan0matches in own text artifacts. Source/migration execution applies only to own QA setup/test DB.
