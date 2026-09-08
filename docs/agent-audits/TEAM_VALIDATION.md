# KidsMap team validation — 2026-09-08

Scope: role behavior on four real read-only impact questions, plus offline structure/native configuration checks. This is **not** a Django/browser/production test pass.
LOCAL HEAD: `d75b34f4db5d4ba484cf8392ff3ae0c9939031e2`; initially clean, agent-system WORKTREE changes only. Production not accessed; current state UNKNOWN.

## Method and acceptance

Coordinator first read the real orchestrator and relevant definitions. Backend/security discovery ran before updates. Updated definitions then received A–D tasks with disjoint report ownership and maximum three concurrent specialists. Each worker applied orchestrator routing then its selected lead sequentially; conditional supporting roles are handoff plans, not fabricated independent executions.

A and D started with fresh context. B and C reused their explicitly identified discovery workers; they reread updated definitions and reverified source/snapshot. That saves context but is not a cold-start evaluation. All used callable Codebase Memory plus coverage and actual source. Index generation changed during the run; static exclusion was observed initially, later full coverage must be checked rather than assumed.

Acceptance dimensions: correct lead, actual source-of-truth, no duplicated ownership, bounded discovery instead of whole-repository rereads, concrete next-role handoff/tests, no unsafe actions or invented execution evidence. A useful UNKNOWN is permitted for runtime/data not inspected; avoid UNKNOWN for source wiring that can be established within the task.

| Task | Lead | Result / evidence |
|---|---|---|
| A: PricingPlan impact | django-reviewer | [A](validation-A.md): model→normalize/serialize/replace/signals→admin/owner/volunteer→filter/map/recommendations/API/SEO. Initial consumer gaps closed by bounded source follow-up; context-reading feedback applied and rechecked. |
| B: Volunteer A / Place B | security-reviewer | [B](validation-B.md): group/middleware/queryset/routes/services/review gates, accidental permissions and public-vs-workspace visibility. Coordinator caught wrong planned manage.py path; corrected and rechecked. |
| C: schedule_mode | django-reviewer | [C](validation-C.md): all five modes, persistence, owner/admin split, importer/export omission, volunteer review, public status and SEO. Prompt feedback repaired and retested. |
| D: Place card redesign | frontend-reviewer | [D](validation-D.md): fresh source audit of shared and separate card surfaces, CSS/JS/data dependencies and future rendered acceptance. Consumer/viewport/reading feedback repaired and source-rechecked. |

## Improvements driven by the runs

1. READ FIRST now means scoped navigation: current snapshot/contracts + relevant source-map rows, with historical domain pages read only as needed. A's first run overread historical knowledge; its follow-up exercised the narrower rule.
2. MCP index_status output is projected to root/status/generation/relevant gaps; no giant graph inventory. Explicit actual source-map path avoids navigation guesses.
3. Schedule acceptance now names regular→other→regular and retained days/text; `{}` unknown differs from populated `is_open=false`. Coordinator checked `build_open_status` directly and C retested the wording.
4. A established relational filter semantics and differences between catalog-map payload and home-map price rendering. Pricing knowledge records this instead of assuming identical presentation.
5. B's future test command corrected from nonexistent `src/manage.py` to root `manage.py`; role quality includes checking proposed commands, not just findings.
6. D added account_favorites as a shared-card consumer, separated volunteer markup, documented full formatted price/empty currency and absent shared schedule row. Historical viewport rows were updated to the common five widths; runtime index coverage takes priority over initial exclusions.

## Executed verification and limits

- `python3 docs/agent-audits/validate_team.py`: checks 11 active roles, 15 required sections, 11 matching native adapters, seven workflows, role/knowledge links, preserved compatibility definitions, scope and empty placeholder. Initial run caught not-yet-created final-report links; final rerun recorded in MASTER_AUDIT.
- `git diff --check`; `git diff --quiet HEAD -- src static templates config scripts deploy Dockerfile .dockerignore docker-compose.yml requirements.txt .github`: whitespace/scope evidence; final rerun required after reports.
- `codex --version`: 0.132.0. Official standalone custom-agent schema verified via [OpenAI documentation](https://learn.chatgpt.com/docs/agent-configuration/subagents) and Context7 `/openai/codex` source references. TOML parsed with stdlib tomllib.
- `codex debug prompt-input`: local offline renderer exited0 after filesystem escalation, output reduced to booleans/names; no raw prompt or private configuration saved. It does not enumerate all custom roles, so it is not proof of a cold native spawn of each role. `--strict-config` is unsupported for this debug command; an initial attempt failed and was corrected.
- `codex doctor --summary --ascii --no-color`: config loaded, exit1 overall due installation-path/update mismatch, terminal and provider reachability; optional MCP issues also reported. No installation/settings/network fixes performed. These environment findings do not prove adapter failure or successful external model connectivity.

Application tests, DB/schema/data checks, migrations, import commands, actual browser rendering, production probes, real OAuth/GA and native cold-spawn behavior are NOT RUN/UNKNOWN. Future Python test commands assume the isolated environment's interpreter has been selected; current shell offers python3, not a guaranteed python alias. No app fixes, deployment, commit or push.
