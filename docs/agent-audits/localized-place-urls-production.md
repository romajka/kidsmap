# Localized place URLs: production release evidence

Date: 2026-09-14. Scope: stable localized Place URLs, related admin preview and import instruction. Explicit user request authorizes deployment and push; unrelated dirty worktree changes were excluded using an isolated release checkout.

## Exact release

Base: `ef91dbe761f340a2c4d37bdc0b96638522aa6edf` (initial clean production and local HEAD). Feature commit: `47859f54c80f8b65c262261c5e531cc024fc9fbe`,33 files including scope report. All32 source/plan/validation manifest hashes match the isolated committed tree. Candidate Docker image: `sha256:7328e063f36ed35b209be7445e1475d7d054adcbbb60377418744ec069fc41d5`.

Fresh isolated release checks:404 Django tests in112.795s, OK;30 rendered admin combinations (add/edit, AZ/RU/EN, five widths), real import/save/reload and stable slugs with tariff preserved. The built server image passed42 URL/admin/SEO/prompt tests in19.604s against a disposable PostgreSQL17 container without production credentials, network access to production, or shared media/cache. Two initial image-test setup attempts stopped before running tests: missing settings module, then missing synthetic database URL password. Both corrected in the test launcher; application source unchanged.

## Production discovery and content review

Read-only transactions/timeouts counted337 places,75 publicly visible. Authorized temporary export contained only public IDs, existing slugs, three names and three descriptions. All75 were manually reviewed against their descriptions. Three missing translated name fields found:41 RU/EN,61 EN. No public unusable transliterations or Cyrillic-script AZ/EN names. No legacy slug exceeds60 characters.

Applied via one transaction with exact-source compare and public-visibility filter: seven fields across three public places. Filled the three missing names and61 EN description; corrected31 opening description sentence in all three languages after explicit user confirmation that this is children's gymnastics. Brand spelling of41 retained as existing AZ name. Remaining text and pricing fields unchanged; updated_at reflects these editorial corrections. No hidden-place content exported.

Review limits:19/20 and207/320 may be duplicates, no merge/deletion performed.46 EN description is title-only. Official brand spelling not independently verified; no invented branch qualifiers or claims added.

## Recovery and current rollout

Backup retained only on server under a protected task-specific directory; no existing backups removed. Full custom-format PostgreSQL backup restored successfully into a separate temporary PostgreSQL17 container with no network:337 places recovered. Temporary restore container removed. Prior image and static archive retained, environment snapshot kept privately on server. No full DB or secrets copied locally.

Production checkout fast-forwarded to feature commit. Migration catalog0113 applied successfully; check/migrate --check pass. Collected2169 static files,5140 post-processed. URL JS, importer JS and URL CSS collected hashes exactly match release source. Replaced only web; PostgreSQL/Redis remained healthy and running. Home and old RU place sample return200. New URL feature flag remains disabled at this report snapshot.

Backfill dry-run:337 examined,337 would_change,0 manual_review;337 AZ addresses preserved,326 RU and325 EN slugs generated.11 RU and12 EN missing translations belong only to hidden places and retain legacy fallback until names are provided.

Mass backfill was blocked by automatic approval review citing historical AGENTS.md production read-only rules. The user then explicitly confirmed the requested exception (fill337 places, activate URLs, push main). Automatic approval review still rejected the same action, explicitly stating that it would refuse despite that confirmation. No workaround or partial mass-update attempted. Activation and final public225-page/legacy/sitemap checks remain blocked by the execution policy, not by missing user authorization. Feature flag stays disabled; fallback preserves all existing public links. The release workflow does not run backfill. Code publication is handled separately; this report does not claim completed activation.
