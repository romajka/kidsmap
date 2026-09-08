# KidsMap engineering team upgrade plan — 2026-09-08

Goal: strengthen the existing eleven-role system against the supplied 28-section brief, without application changes.
Architecture: `.agents` remains the single definition/knowledge/routing source; native `.codex/agents/*.toml` files only load those definitions. Preserve the empty `.codex` placeholder in history before creating its directory.
Spec: user attachment `pasted-text-1.txt`, supplied in this session. Authorization covers agent definitions, knowledge, orchestration, workflows and reports; no application fixes, production actions, deletions, commit or push.

- [x] DISCOVER: record clean starting HEAD, existing 15 definitions and seven retained copies; discover Codebase Memory and installed Codex.
- [x] AUDIT: graph-first backend/security discovery by two bounded specialists; coordinator verifies UI/SEO/analytics/infra and documentation conflicts in source.
- [x] MAP/DESIGN: preserve 11 active IDs; keep data migration with database owner and performance with layer owners; refresh snapshot and missing source-of-truth domains.
- [x] UPDATE: shared memory/evidence/handoff contract; all 15 requested sections for each active role; focused pricing/schedule/permissions knowledge; explicit workflow support and browser widths.
- [x] NATIVE: preserve placeholder, add 11 TOML loaders without model or permission overrides; validate against official format and local parser where available.
- [x] VALIDATE: execute A PricingPlan, B volunteer isolation, C schedule_mode, D Place card as independent read-only role tasks; score routing/source/scope/handoff/safety, repair prompts and retest affected cases.
- [x] VERIFY: parse registry/TOML, check required headings/references/roster/workflows, inspect diff and ensure application hashes unchanged; produce results, inventory decisions and diff stat.

Local starting snapshot: `d75b34f4db5d4ba484cf8392ff3ae0c9939031e2`, clean worktree. Production: not accessed in this run; 2026-09-06 observations are historical.
Codebase Memory: project `home-ramin-kidsmap`, fast index, persistence=false; static/docs exclusions and template parse gaps require direct-source fallback. No graph artifact copied into the repository.
Execution: coordinator plus at most three disjoint specialists, no duplicate compatibility roles. Existing user authorization permits this plan to be executed now.
