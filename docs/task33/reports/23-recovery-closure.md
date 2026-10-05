# Stage 23 — independent R1 data/recovery rehearsal

Reviewer `/root/stage23_db_review`, canonical `database-reviewer`; local synthetic-only QA scope. LOCAL HEAD `015d031d8eb17114bd860159dde805b38df3c13c`, dirty `task33-progress` WORKTREE; no production connection, credentials, deployment, backup script, commit or push. The final tested dirty runtime is the frozen, content-addressed **LOCAL** artifact `r1-local-sha256-df5c662e67f05511b710eae38cd678e170dfa514f483852f15ccf101c5369af3`, not HEAD alone and not a production image.

The artifact matches all **2703/2703** allowlisted files in the Linux QA mirror. A post-rehearsal cross-check found three Windows working-copy `.mo` files differed from the compiled Linux `.mo` bytes; all other Windows allowlisted files matched. The frozen Linux runtime is the tested snapshot, and the three locale binaries must be reconciled by the lead before describing the Windows tree as byte-identical.

## Application and migration exercise

New `catalog.testcases.test_task33_r1_acceptance` ran through unchanged QA04 launcher on a fresh Linux mirror:

```powershell
& 'C:/Program Files/WSL/wsl.exe' -d Ubuntu-24.04 -u root --exec /bin/bash /mnt/c/kidsmap/scratch/task33-stage22/run-linux-qa.sh all stage23-r1-acceptance-red-20261003-1125 --label catalog.testcases.test_task33_r1_acceptance
```

Exit0, **5/5 PASS**, 0 failures/errors/skips, Django check and `makemigrations --check` PASS, 164 applied/0 pending migrations, discovery 1615 unique/0 duplicates. PostgreSQL17.11, Django6.0.2, Python3.12.3, psycopg3.2.10; clean env/no external credentials, network/libpq guards, cleanup PASS and socket/run roots removed. Raw synthetic evidence: `/root/task33-evidence/stage23-r1-acceptance-red-20261003-1125/` outside Git. The stamp says `red` because it was reserved before execution; its actual result is green. The five tests cover seven actors and false same-address match; scoped owner/manager review reply and moderator decision; volunteer proposal requiring separate staff approval; conversion row/URL preservation over partial/resume/rerun; and post-switch count-drift without deleting the new row. Earlier stage07/12/16/22 modules retain their separate evidence.

## Native restore and media

`docs/task33/qa23/rehearsal.py` prepends the QA23 bridge to the **unchanged** QA04 launcher. The child verifies that exactly one running QA04 nonce-owned Docker container has network none, no ports, tmpfs PGDATA and the child's private Unix-socket mount before calling native PostgreSQL tools. Initial `qa23-first-20261003-1130` failed before rehearsal because QA04's fixture imported `commands.dump`; the bridge now exports it. That failed run still cleaned its owned container/socket. Container-guard unit test was observed red for a missing module, then green after the guard was implemented.

Preliminary native rehearsal:

```powershell
& 'C:/Program Files/WSL/wsl.exe' -d Ubuntu-24.04 -u root --exec /bin/bash /mnt/c/kidsmap/docs/task33/qa23/run-linux-probe.sh second-20261003-1134
```

Exit0, launcher `status=PASS`, `child_exit=0`, cleanup PASS, run/socket roots removed. It preserved source-row digests and media bytes through dry-run and 21-piece one-batch interruption/resume/rerun. After synthetic post-switch Place, Organization, approved/pending Program edition, Activity, Group, direct/group tariffs, PlaceReview/reaction and uploaded JPEG, writes-off mode returned public GET200 and HTTP POST503; the new rows and approved Program snapshot remained. A **531637-byte** custom-format `pg_dump` taken **after** the writes restored into a second database inside the same owned container. Source and restore matched row digests across **94 public-schema tables**, including catalog, auth grants, rights and migration state; **25 media files** matched byte hashes in an external copied media tree. Synthetic-only raw evidence and dump: `/root/task33-evidence/qa23-second-20261003-1134/`. No old dump was restored over new records.

## Final frozen-artifact verification and audit handoff

Final command on the lead's source-frozen Linux mirror:

```powershell
& 'C:/Program Files/WSL/wsl.exe' -d Ubuntu-24.04 -u root --exec /bin/bash /mnt/c/kidsmap/docs/task33/qa23/run-linux-probe.sh final5-20261003-1530 /root/task33-artifacts/r1-local-sha256-df5c662e67f05511b710eae38cd678e170dfa514f483852f15ccf101c5369af3/artifact.json
```

Exit0, child0, **PASS**, cleanup PASS with owned container and both run/socket roots removed. Synthetic evidence: `/root/task33-evidence/qa23-final5-20261003-1530/` outside Git; raw post-switch custom-format dump is there, not committed. The child verified its unique nonce-owned Docker container (network none, no ports, tmpfs PGDATA, private Unix socket), 21 mapping pieces, forced mid-batch rollback, partial checkpoint1, resume and rerun, unchanged source row/media digests, and post-switch records retained despite count drift. HTTP writes-off returned public GET200/POST503 without row changes. A **531672-byte native pg_dump** taken after the new writes restored to the separate `qa_stage23_restore` DB. Source and restore count plus row digests matched for **all 94 public-schema tables**; **25 media files** had equal copied byte hashes.

The bridge verified the archive SHA, manifest identity/SHA, every one of **2703** extracted source files, Python version, interpreter hash and full installed dependency inventory. The subprocess imported application code from that frozen standby, set `TASK33_R1_WRITE_MODE=off`, applied its own AF_UNIX and libpq guards for the one named restore DB, and read it in `BEGIN READ ONLY`. It confirmed the new Place, retained approved Program snapshot under a pending edition, direct and group prices, current review and reaction, actual media bytes and distinct AZ/RU URLs; public GET200 and unsafe POST503. `compatible_standby_read.status=PASS`, not NOT_RUN. This demonstrates a compatible local reader/recovery strategy with post-switch writes retained. It does not authorize production activation or substitute for a production immutable image and data-specific dry run.

Earlier v1–v4 rehearsals also passed (`/root/task33-evidence/qa23-final-20261003-1330`, `/root/task33-evidence/qa23-final2-20261003-1400`, `/root/task33-evidence/qa23-final3-20261003-1430`, `/root/task33-evidence/qa23-final4-20261003-1500`). Browser QA helper corrections and organization-workspace mobile CSS fixes changed the archive identity. Backend, migrations and acceptance-test bytes stayed the same. The v5 result above is the final artifact-aligned evidence.

Independent source review raised an interim hypothesis about an owner pin move carrying an old location override, but `publication.propose` filters unchanged snapshot values out of the candidate. The final real `OwnerPlaceEditForm` → `publication_forms.save_form` regression passed in the public specialist's isolated **184/184** suite and confirmed the old override expires after a pin move. Final source also emits only an opaque HMAC of the current audit in a readable signed token; raw reason and actor remain restricted to validated staff revision handling. Explicit override changes require author permission at proposal and approval. I reviewed this boundary and found no remaining confirmed P0/P1; the report `23-db-review.md` retains the separate P2 schema invariant.

Named handoff: `release-reviewer` and lead `integration-reviewer` attach this frozen-artifact result, source hashes, query/browser/full-suite evidence and R1 stop criteria. Production pilot participant selection and activation remain separate.
