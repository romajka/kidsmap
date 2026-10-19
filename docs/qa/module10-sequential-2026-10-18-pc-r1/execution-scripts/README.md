# Execution support

Root executed these local scripts; no independent agent was used. Current-source reference is source-final.json and own scratch runtime is .tmp/m10-seq-r1/runtime.py. Stage plans/diffs/RED/GREEN evidence are retained, including initial failures and observer corrections. Avoid replay against foreign or production state: fixture mutations are real native UI actions on owned m10seq_r1 only.

Final backend command: python3 .tmp/m10-final-tests.py → run_stage_tests.py 99 green plus exact labels in evidence/final-backend-labels.json. Test runner validates fresh own DB name and clears environment before Django setup. Native command: python3 docs/qa/module10-sequential-2026-10-18-pc-r1/browser_driver.py <script-name>, Chromium session m10-seq-r1. Final accepted browser matrix is composed transparently from raw final-public and native OFF-precondition retired-r2 runs; original ON200 expectation failures and initial script compilation error are retained.

Preservation command: python3 .tmp/m10-final-preservation.py validates source, prior41packages/8514files, Git/index, sharedMO, foreign container identity/state and restored original fixture values. Final artifact verification: PYTHONDONTWRITEBYTECODE=1 python3 docs/qa/module10-sequential-2026-10-18-pc-r1/verify_artifacts.py. Verification reads only.
