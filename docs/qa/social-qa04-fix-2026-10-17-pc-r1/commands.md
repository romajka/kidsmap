# SOCIAL04 — исполнение одобренного плана

2026-10-17, Asia/Baku; C:\kidsmap, PowerShell +Ubuntu-24.04 WSL. Только собственный isolated profile social04-pc-fix-r1. Ниже реальные bounded commands; .tmp launchers не следует запускать повторно без ownership/source/isolation проверки.

| Команда | Exit/result |
|---|---|
| `python -X utf8 docs/qa/social-qa04-recheck-2026-10-16-pc-r1/verify_artifacts.py` до patch |0;1020sources/refs/index/MO/предыдущие artifacts MATCH; unchanged108cell RED применим |
| `docker inspect m09s04-plan-r1-app m09s04-plan-r1-pg --format …` |0; оба running, own label verified; новый fix profile всё равно создан отдельно |
| `python -X utf8 .tmp/social04-pc-fix-r1/bootstrap.py` |0; approval «одобряю», точный plan SHA и2file scope; исходный source1020 unchanged |
| `git apply --check --ignore-space-change docs/qa/social-qa04-recheck-2026-10-16-pc-r1/proposed.diff` |0 |
| Same `git apply` без `--check` |0; ровно template/newCSS; CRLF patch whitespace warnings отдельно ниже |
| `python -X utf8 .tmp/social04-pc-fix-r1/capture.py` |0; approved source1021, остальные entry sources сохранены |
| `python -X utf8 .tmp/social04-pc-fix-r1/setup_helpers.py` |0; reviewed own settings/helpers variants для нового DB/cache/media/locales/network/port/session; credentials не наследуются |
| `wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/scripts/build_isolated_locales.py build --output /mnt/c/kidsmap/.tmp/social04-pc-fix-r1/locales --locales ru az en --compiler native` |0;3freshMO, sharedMO unchanged |
| `… sh …/social04-pc-fix-r1/start.sh` |0; новый internal network/volume/app/PG, prior container ID/state snapshot |
| `… sh …/social04-pc-fix-r1/prepare.sh` первый вызов |1; pg_isready ещё no response сразу после старта; migrate/seed/tests не выполнялись |
| Same prepare после фактической готовности PG |0; fresh ownDB migrated/seeded, source/MO gated HTTP started |
| PowerShell `Start-Process wsl.exe …proxy.py -WindowStyle Hidden` |собственный независимый loopback33314 proxy; PID только в ignored scratch |
| `… browser_driver.py open about:blank --config=/mnt/c/kidsmap/.tmp/social04-pc-fix-r1/playwright.json` |0; отдельная Chromium155 session |
| `… browser_driver.py browser-initial.js` |0; localhost allowlist до navigation, actual1021source/template/static SHA/sole locales verified |
| `wsl -d Ubuntu-24.04 -- sh /mnt/c/kidsmap/.tmp/social04-pc-fix-r1/green.sh` |0;4unchanged affected methods,0F/0E,1.400s; отдельный own test DB |
| `python -X utf8 .tmp/social04-pc-fix-r1/make_matrix.py` |0; native outcome checks из RED +contrast/focus/unread, action N/A не превращаются в PASS |
| `wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/.tmp/social04-pc-fix-r1/matrix.py` |0;108cells,1188control +1368style/outcomePASS,0FAIL |
| `wsl -d Ubuntu-24.04 -- python3 /mnt/c/kidsmap/.tmp/social04-pc-fix-r1/flows.py` |0;30independent native cases/279PASS, включая controlled400/409 и явно SIMULATED transport/concurrent event |
| `… run_supplement.py focus` |0;6key cells/18PASS, measured focus contrast≥6.0945 |
| `… run_supplement.py guards` |0;3locale cases/24PASS, guest/outsider/CSRF/POST guards/no-write |
| `… run_supplement.py smoke` |0;12role inbox +18shared cells/144PASS, new CSS only inbox, no page overflow |
| `… build_isolated_locales.py verify --manifest /mnt/c/kidsmap/.tmp/social04-pc-fix-r1/locales/manifest.json` |0;3current MO |
| `python -X utf8 .tmp/social04-pc-fix-r1/publish.py` |0;174native PNG copied/hash/dimensions, final live info/30entry container preservation verified |
| `python -X utf8 docs/qa/social-qa04-fix-2026-10-17-pc-r1/verify_artifacts.py` |0; source1021/candidates2/previous manifests/index/refs/active_run/MO/.cbmignore/guide174PNG/links verified; no app/tests rerun |

Единственный post-patch backend GREEN передавал4labels одной команде:

```text
docker exec m09s04-fix-r1-app python /mnt/c/kidsmap/.tmp/social04-pc-fix-r1/runtime.py test
catalog.testcases.test_task33_notifications.WorkflowIntegrationTests.test_invitation_inbox_post_only_recipient_scoped_and_revocation_suppresses_mail
catalog.testcases.test_task33_notifications.WorkflowIntegrationTests.test_csrf_required_for_inbox_actions
catalog.testcases.test_task33_notifications.WorkflowIntegrationTests.test_join_confirmation_form_is_current_owner_post_only
catalog.testcases.test_access_qa02_invitation_decline.InvitationDeclineTests.test_inbox_exposes_decline_for_both_current_invitation_kinds_in_all_locales
```

Actual shell использует continuation backslashes. Exact browser case invocations/exits сохраняются в browser-commands.jsonl; source gates выполняются до django.setup. Native UI/POST/reload проверяют реальные views/services; fixture login — QA-only, expiry/read initial states — fictional setup. READ ONLY snapshots с5s statement/2s lock timeout. Concurrent revoke, malformed extra-field input, finite500ms delay и transport abort имеют отдельную attribution, не выдаются за реальные внешние сервисы.

Apply выдал36 whitespace warnings из-за CRLF строк нового CSS в patch. У всех36 CSS строк нет текстовых trailing blanks; нормализованное содержимое совпадает с approved candidate, git diff --check exit0. LF/CRLF не менялись в чужих файлах. Discovery-only отсутствующий speculative organization.py path исправлен чтением фактического models/business_team.py; ранний probe seed.log до завершения migrate был not-ready, не product failure.

Последующие bounded native flows/smoke/guards/focus и final metadata commands указаны в verification.json и итоговом REPORT. Production/commit/push/deploy и full ACCEPT09/global suites не запускались.
