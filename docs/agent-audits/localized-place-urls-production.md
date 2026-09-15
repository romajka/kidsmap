# Localized place URLs: production release evidence

Date: 2026-09-14. Scope: stable localized Place URLs, related admin preview and import instruction. Explicit user request authorizes deployment and push; unrelated dirty worktree changes were excluded using an isolated release checkout.

## Current status: activated and verified on 2026-09-15

The user changed the execution permission mode and explicitly requested continuation. SSH access and fresh read-only state checks succeeded; the prior execution blocker is resolved. Production continues to run the previously tested feature commit `47859f54c80f8b65c262261c5e531cc024fc9fbe` and image `sha256:7328e063f36ed35b209be7445e1475d7d054adcbbb60377418744ec069fc41d5`. Local/GitHub HEAD before this evidence-only update is `bfc2c28e11b5fc1e4d0a8117ac30836dc8aa9308`; its unrelated admin changes were not deployed by this activation. Existing feature implementation was already pushed in commits47859f54/0223f153.

There are now338 places (one additional hidden record),75 public. A fresh full database backup was retained only on the server and restored successfully into a separate no-network PostgreSQL17 container, recovering338 places. The temporary restore container was removed. The feature-compatible recovery image and explicit recovery instructions are retained on the server. After serving permanent redirects, retain the localized fields, compatible resolver and enabled flag during recovery.

Executed against production:

- `backfill_localized_place_slugs --apply --batch-size 100`:338 examined/changed,0 manual_review;338 AZ paths preserved,326 RU and325 EN slugs generated.
- Immediate `--dry-run --batch-size 100`:338 unchanged,0 would_change,0 manual_review. No second application needed.
- Read-only audit:75 public places,0 missing public names/slugs,0 unexpected populated slugs. An aggregate fingerprint over every Place column except the three localized slug fields was identical before and after backfill: all other Place data remained unchanged.
- Hidden records without translated names retain legacy fallback:12 missing RU,13 missing EN. They are not claimed to have translated names or complete content.
- Set `LOCALIZED_PLACE_URLS_ENABLED=1` and recreated only web with the same tested image. Runtime flag verified true; Django check and migrate --check passed. No database/Redis restart or schema change in this activation.
- Comprehensive external HTTPS verification:225/225 canonical pages returned direct200,225 self-canonical/reciprocal AZ/RU/EN/x-default sets passed,123/123 changed legacy links returned301 to the exact final200 URL.102 old URLs already equal their canonical targets. All225 URLs and their alternate-language sets appear correctly in sitemap (270 total sitemap locations). Zero failures;108.94s,3 workers,20s request timeout. Machine result: [HTTP verification](localized-place-urls-production-http.json).
- All263 hidden places checked internally through HTTP in3 languages:789/789 returned404. No previously hidden record became publicly accessible.
- Fresh rendered Chromium check on public Place4:AZ/RU/EN at390/1280,6 cases; correct visible content/canonical and desktop/mobile switch links, actual desktop AZ→RU→EN navigation without loops;0 pageerrors/HTTP400+. [Rendered evidence](localized-place-urls-production-browser.md).

No source changes during activation. The earlier404 release-source tests,42 built-image tests and30 admin browser cases below remain evidence for this exact deployed feature image, not newly rerun tests. New-place import/save, stable slugs after rename and preservation of existing tariffs were verified in that isolated admin workflow. No synthetic places/accounts were created in production. External search-engine indexing and unrelated content completeness/possible duplicate records remain outside these checks.

## Exact release

Base: `ef91dbe761f340a2c4d37bdc0b96638522aa6edf` (initial clean production and local HEAD). Feature commit: `47859f54c80f8b65c262261c5e531cc024fc9fbe`,33 files including scope report. All32 source/plan/validation manifest hashes match the isolated committed tree. Candidate Docker image: `sha256:7328e063f36ed35b209be7445e1475d7d054adcbbb60377418744ec069fc41d5`.

Fresh isolated release checks:404 Django tests in112.795s, OK;30 rendered admin combinations (add/edit, AZ/RU/EN, five widths), real import/save/reload and stable slugs with tariff preserved. The built server image passed42 URL/admin/SEO/prompt tests in19.604s against a disposable PostgreSQL17 container without production credentials, network access to production, or shared media/cache. Two initial image-test setup attempts stopped before running tests: missing settings module, then missing synthetic database URL password. Both corrected in the test launcher; application source unchanged.

## Production discovery and content review

Read-only transactions/timeouts counted337 places,75 publicly visible. Authorized temporary export contained only public IDs, existing slugs, three names and three descriptions. All75 were manually reviewed against their descriptions. Three missing translated name fields found:41 RU/EN,61 EN. No public unusable transliterations or Cyrillic-script AZ/EN names. No legacy slug exceeds60 characters.

Applied via one transaction with exact-source compare and public-visibility filter: seven fields across three public places. Filled the three missing names and61 EN description; corrected31 opening description sentence in all three languages after explicit user confirmation that this is children's gymnastics. Brand spelling of41 retained as existing AZ name. Remaining text and pricing fields unchanged; updated_at reflects these editorial corrections. No hidden-place content exported.

Review limits:19/20 and207/320 may be duplicates, no merge/deletion performed.46 EN description is title-only. Official brand spelling not independently verified; no invented branch qualifiers or claims added.

## Initial rollout: 2026-09-14

Backup retained only on server under a protected task-specific directory; no existing backups removed. Full custom-format PostgreSQL backup restored successfully into a separate temporary PostgreSQL17 container with no network:337 places recovered. Temporary restore container removed. Prior image and static archive retained, environment snapshot kept privately on server. No full DB or secrets copied locally.

Production checkout fast-forwarded to feature commit. Migration catalog0113 applied successfully; check/migrate --check pass. Collected2169 static files,5140 post-processed. URL JS, importer JS and URL CSS collected hashes exactly match release source. Replaced only web; PostgreSQL/Redis remained healthy and running. Home and old RU place sample return200. New URL feature flag remains disabled at this report snapshot.

Backfill dry-run:337 examined,337 would_change,0 manual_review;337 AZ addresses preserved,326 RU and325 EN slugs generated.11 RU and12 EN missing translations belong only to hidden places and retain legacy fallback until names are provided.

Mass backfill was blocked by automatic approval review citing historical AGENTS.md production read-only rules. The user then explicitly confirmed the requested exception (fill337 places, activate URLs, push main). Automatic approval review still rejected the same action, explicitly stating that it would refuse despite that confirmation. No workaround or partial mass-update attempted. Activation and final public225-page/legacy/sitemap checks remain blocked by the execution policy, not by missing user authorization. Feature flag stays disabled; fallback preserves all existing public links. The release workflow does not run backfill. Code publication is handled separately; this report does not claim completed activation.
