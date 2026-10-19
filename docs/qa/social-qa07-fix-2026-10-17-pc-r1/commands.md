# Commands and outcomes

Executed from C:/kidsmap using Windows PowerShell and Ubuntu-24.04 WSL. Runtime scripts are evidence, not continuation commands.

- Windows git status --porcelain=v1 -uall and refs/index/source hashes: exit0. Own initial WSL status child terminated after slow traversal, not application run.
- bootstrap/apply-approved.py: gates source1021/old artifact hashes/internal own PG/RO mount; initial apply-check whitespace failure1; git apply --check --ignore-space-change and git apply --ignore-space-change exact approved diff exit0; candidate text equality/source1022 gate exit0.
- scripts/build_isolated_locales.py build --output /mnt/c/kidsmap/.tmp/social07-pc-fix-r1/locales --locales ru az en --compiler native: exit0,3catalogues; verify before each setup.
- start-app.sh: initial gate1, corrected isolated hostname, retry0; own fixture seed/serve only. No old prepare scripts executed.
- docker exec m09s07-fix-r1-app python /mnt/c/kidsmap/.tmp/social07-pc-fix-r1/runtime.py test catalog.testcases.test_social_qa07_activity_review_title.SocialQA07TitleTests catalog.testcases.test_social_qa03_conflict_recovery.TypedReviewConflictRecoveryTests.test_stale_draft_renders_with_latest_version_and_no_write catalog.testcases.test_social_qa03_conflict_recovery.TypedReviewConflictRecoveryTests.test_conflicting_script_text_is_escaped_and_preserved: exit0,11tests,5.415s. Pre-test QA host gate failure preserved separately.
- browser_driver.py open --config /mnt/c/kidsmap/.tmp/social07-pc-fix-r1/playwright.json:0; browser-initial.js:0; matrix.py:0,66cells. Each CLI call logged browser-commands.jsonl; matrix source/control assertions unchanged from PLAN07.
- run_json.py edges and run_json.py redirect:0, raw outputs/results retained; assertions all true.
- git-final.ps1:0. publish.py and verify_integrity.py check current sources, prior files, container states, refs/index/MO/active_run, manifest, counts and guide reverse hash: exit0 required before closure.
