# Executed commands and boundaries

2026-10-16, `C:\kidsmap`; shells PowerShell / Ubuntu-24.04 WSL. Commands below record this execution; scratch launchers and historical profiles are not general continuation commands. No production invocation.

| Command / invocation | Exit / result |
|---|---|
| `git status --short --branch`; `git remote -v`; `git branch --show-current`; `git rev-parse HEAD`; `git worktree list --porcelain` | 0; clean task33-progress/e4e05cc…, expected origin; second pre-existing detached worktree preserved |
| `git ls-remote --heads origin refs/heads/codex/module09-transfer-2026-10-16-r1` | 0; 852938d96764ae315b92859e3651e5ea62054a36 |
| `git fetch --no-tags origin refs/heads/codex/module09-transfer-2026-10-16-r1:refs/remotes/origin/codex/module09-transfer-2026-10-16-r1` | 0; expected tip; Git's normal fetch performed automatic packing |
| `git log -5 --format='%h %s' origin/codex/module09-transfer-2026-10-16-r1`; `git rev-list --left-right --count HEAD...origin/codex/module09-transfer-2026-10-16-r1` before checkout | 0; starting branch 0/12 behind; no divergent commits |
| `git -c gc.auto=0 -c core.longpaths=true checkout --no-overwrite-ignore --track -b codex/module09-transfer-2026-10-16-r1 origin/codex/module09-transfer-2026-10-16-r1` | 0; only after repeated clean WORKTREE/index check |
| `git status --short --branch`; `git rev-parse HEAD`; divergence command after checkout | 0; clean target, exact checkpoint, 0/0 |
| `python .tmp/module09-pc-resume-2026-10-16-r1/snapshot.py` | 0 entry and post-native; source1019/HEAD/branch/index tree/sharedMO/active_run/task33 ref MATCH |
| `wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/scripts/build_isolated_locales.py build --output /mnt/c/kidsmap/.tmp/module09-pc-resume-2026-10-16-r1/locales --locales ru az en --compiler native` | 0; 3 current catalogues |
| `wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/scripts/build_isolated_locales.py verify --manifest /mnt/c/kidsmap/.tmp/module09-pc-resume-2026-10-16-r1/locales/manifest.json` | 0; verify also executed before each django.setup |
| `wsl -d Ubuntu-24.04 -- sh /mnt/c/kidsmap/.tmp/module09-pc-resume-2026-10-16-r1/start.sh` | 1 at seed tuple unpacking; migrate/info succeeded; initial pg_isready polling not ready, migration later connected. Harness failure, no product verdict |
| Corrected seed attempt | 1; own app container no longer running after WSL discontinuity |
| `docker inspect m09pc-r1-app m09pc-r1-pg --format '{{.Name}} exit={{.State.ExitCode}} oom={{.State.OOMKilled}} error={{.State.Error}} finished={{.State.FinishedAt}}'` | 0; owned app255/PG0, oom=false; no foreign restarts |
| `docker start m09pc-r1-pg m09pc-r1-app`; own `python3 …/proxy.py` | 0 for starts; proxy long-running loopback listener held WSL active. Own tmpfs database was empty after stop |
| `docker exec m09pc-r1-app python …/runtime.py migrate`; `… info`; corrected `… seed`; `… serve` | 0 migrate/seed; info0; serve long-running. Rebuilt only empty owned DB. Logs preserved |
| Initial targeted `…/tests.sh` | 1, harness URLconf error: i18n_patterns cannot be included. No application/assertion edits; only scratch URL composition fixed |
| `npx --yes --package @playwright/cli playwright-cli --help \| head -55` in WSL | Pipeline0, CLI refused Node18 as unsupported; browser not started, not PASS |
| `npx --yes --package node@24 --package @playwright/cli playwright-cli -s=m09pc-r1 open about:blank --config=/mnt/c/kidsmap/.tmp/module09-pc-resume-2026-10-16-r1/playwright.json` | 0; independent Chromium155 session, external allowlist installed before app navigation |
| `wsl -d Ubuntu-24.04 -- sh /mnt/c/kidsmap/.tmp/module09-pc-resume-2026-10-16-r1/tests.sh` corrected run | 1 expected RED; 10 methods / 14 assertion failures / 0 errors / 3 failing methods, 7 passing |
| `wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/.tmp/module09-pc-resume-2026-10-16-r1/browser_driver.py browser-initial.js`; `… snapshot` | 0; real author editor inspected before selectors used |
| `wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/.tmp/module09-pc-resume-2026-10-16-r1/matrix.py` | 0 runner completion; 18 expected failing product conflict states, not product PASS |
| `git apply --check --ignore-space-change docs/qa/social-qa03-recheck-2026-10-16-r1/proposed.diff` | 0, no application mutation |
| `git diff --exit-code -- src static templates scripts config locale`; `git diff --cached --exit-code` | 0 after native recheck; application and index unchanged |

The corrected `tests.sh` invoked one runtime with these labels, in this order:

```text
test_social_qa03_conflict_recovery.TypedReviewConflictRecoveryTests
catalog.testcases.test_social_qa01_rating_readback.TypedReviewRatingReadbackTests.test_new_editor_and_foreign_candidate_have_empty_rating
catalog.testcases.test_social_qa02_rejection_feedback.TypedReviewRejectionFeedbackTests.test_rejected_edit_feedback_is_author_only_and_keeps_current_projection
catalog.testcases.test_task33_reviews.ReviewVersionPostgresConcurrencyTests.test_two_edits_compare_and_swap_then_two_approvals
catalog.testcases.test_place_review_cooldown.PlaceReviewCooldownTests.test_early_repeat_is_429_and_never_overwrites_review
```

Runtime invocation: `docker exec m09pc-r1-app python /mnt/c/kidsmap/.tmp/module09-pc-resume-2026-10-16-r1/runtime.py test <labels above>`. Candidate module imported directly from the recorded docs candidate directory; no new application test file. Test DB dropped by the test runner. CAS unit cases use documented cooldown0; persisted429 guards use120s. Native Specialist has its existing no-cooldown semantics.

Native calls and per-cell exits: [browser-commands.jsonl](browser-commands.jsonl). All browser diagnostics remain in [matrix](matrix.json); expected console409 and18InvalidStateError are retained. Source check output, final Git/docs/PNG integrity gate and NOT RUN scope: [verification](verification.json). No complete module09/project run.

Final metadata gate: `python docs/qa/module09-pc-resume-2026-10-16-r1/verify_artifacts.py`. Initial exit1 was a porcelain whitespace parsing error in this new QA helper; [attempt retained](gate-attempts.json). Leading status columns were preserved, original source/index/scope assertions retained. The final result is recorded in verification; this gate does not declare the product fixed.
