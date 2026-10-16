# ACCEPT-07 — LOCAL FAIL: ACCESS-QA-06 OPEN

2026-10-15, Asia/Baku. Полная локальная приёмка выполнена в режиме **AUDIT ONLY**. Исторические ACCESS-QA-01–05 подтверждены CLOSED LOCAL (03=ORG02 — alias ранее принятого исправления). Обнаружен новый P3 **ACCESS-QA-06**: форма обрезает крайние пробелы точной фразы удаления. Исправление не выполнено — нужен отдельный [PLAN](PLAN-ACCESS-QA-06.md). Модуль07 целиком не закрыт, module08 не начат. Production не проверялся.

## 1. Snapshot, scope и роли

Фактический root `/home/ramin/kidsmap`; HEAD `e4e05cc213b34e2d771ecb854901bfd016d1db51`; branch `task33-progress`; dirty WORKTREE; active_run NONE. [Entry](entry.json):28813project-file hashes,62foreign container identities,1known live QA HTTP process. Full-run стартовал после approved ACCESS05: его четыре PO-записи уже входят в entry. В ACCEPT application-файлы не менялись; proposed forms/test diff остался только артефактом.

Один исполнитель, последовательные канонические kidsmap-orchestrator/integration-reviewer/django-reviewer/security-reviewer/frontend-reviewer/browser-qa; независимое исполнение специалистов не заявляется. Прочитаны реальные .agents/registry/roles/architecture/source-of-truth/audit contract, guide и relevant module07 history. Исторические localhost/PID/FAIL не использованы как доказательство текущего snapshot. Graph-first discovery затем проверена source; graph cache не сохранялся. Skills: debugging/planning/TDD/verification/accessibility/KidsMap UI/Playwright; для strip использован Context7 с official Django6.0 docs.

## 2. Собственная изолированная среда

[Runtime info](runtime-info.json): Python3.12.3/Django6.0.2,175migrations; PG17-alpine, собственные DB/user `module07_full_r1`, loopbackPG42603/HTTP34133, container+volume `module07-full-2026-10-15-r1-pg`. Own .tmp profile mode700, credentials600; отдельные LocMem cache/media/private-media/filebased email и private JSON mail journal. ENV очищен до setup; checkout .env/production credentials не загружались. Python connect guard допускает только свой PG; browser requests вне собственного origin блокируются. Real external OAuth/SMTP/SDK NOT RUN; tool/host-wide firewall isolation не заявляется.

Base code retention policy inactive; own policy **SIMULATED-QA07** извлечена из existing TEST_POLICY. Её включение только в own QA settings не является policy approval/production readiness. Final processor проверен на5своих UI-confirmed scheduled users: actual-now skipped5/5, затем canonical `finalize_account_deletion` с явно SIMULATED now=scheduled_for+1s completed5/5. Никаких ORM-переходов вместо проверяемого UI. Natural30-day wait/backup expiry NOT RUN.

RU/AZ/EN собраны из current PO через scripts/build_isolated_locales.py в собственный fresh output; build0/verify0, sole LOCALE_PATHS до setup. [Manifest](locale-manifest.json). Source942app paths pinned, actual argv/PID/cwd, views/service origins, cached deletion template SHA и opened own MO сверяются [финальным gate](verification.json). Это совокупность source/process/template/behavior/readback evidence, а не доверие echo manifest само по себе.

Для PDF дополнительная граница требовала pinned pypdf==6.20.1, отсутствовавший в shared interpreter. Exact local package скопирован без download только в собственный python-deps;61file hashes [recorded](isolated-dependency-manifest.json). Shared package installs/config не менялись. Родительский sys.path не передавался bounded parser child, поэтому создана собственная venv без pip, с .pth к собственному пакету и read-only project libraries. [Actual owned interpreter + valid bounded child](owned-venv-proof.json). CPU/memory/timeout/validation guards приложения не менялись. Собственный HTTP перезапущен после проверки identity/source; последний argv/PID в [server.json](server.json), actual pypdf origin/version в runtime source. After-dependency private/media checks выполнены заново целево.

## 3. Матрица сценариев

[Role × action × entity CSV](role-action-entity-matrix.csv), [все selected observations](accepted-observations.json), [findings](FINDINGS.md).

| Сценарий | Проверено | Результат |
|---|---|---|
| Login/register/verification/reset/account/profile/settings/team/deletion/Google-disabled UI |14rendered states × RU/AZ/EN ×6widths =252states; root/controls/focus/error/long text |PASS в границах валидных oracle; raw caveats ниже |
| Reset dialog |18cells: Tab trap, settled Escape/opener, visible submit outline; simulated localhost AJAX abort preserves input |90PASS |
| Native auth lifecycle |RU/AZ/EN390/1440: mismatch, actual local OTP, wrong/reused OTP, resend cooldown, normalization, profile+avatar save/reload, native logout, actual local reset/new password/replay, safe next, duplicate email |72PASS; console/network captured |
| Auth negatives |expired initial fixture, bad/no-CSRF logout/register, GET mutation denial, remember session/persistent, unknown-email reset no-mail |24PASS |
| Role/URL/API/download/media boundaries |anonymous/author/person/owner/network/employee/outsider/volunteer/moderator/reviewer/staff/admin ×3languages; own/foreign entities; headers; no domain side effects |888PASS |
| Certificates |native person withdraw/re-publish/reload, public HTML only eligible doc; after finalization guest/author deny and reviewer/admin private download |9 +24PASS |
| Place/org team lifecycle |native invite/accept/decline/cancel/role/revoke, stale version409, removed open-tab save403/input preserved, transfers/fresh direct URL bounds |21 +13PASS; org18inbox cells +native decline/cancel/replay21PASS |
| Org loading/conflict |18cells, explicitly SIMULATED localhost delayed409; disabled submit/repeat protection/preserved input |54PASS |
| Long-email team/select/empty sections |native invite,18cells full text/control geometry and keyboard select; native Space cancel |37PASS |
| Suspended grant |actual inactive precondition, forbidden active=True400, unchanged data,3languages |9PASS |
| Media positive/negative control |ordinary public PNG200; actual existing legacy private file404/no marker |2PASS on current runtime |
| Account deletion/cancel/reset |8native cases, signed private status/old session/code replay, actual local letters, correction and cancel; native new password after cancel |72 +15PASS |
| Person-linked deletion |native pending relations +person request; actual own final processor5cases, private access after unlink |2 +9PASS + service/readback |
| Exact phrase extra spaces |new native signup/mail/confirmation, wire raw string preserved, RU/AZ/EN390/1440 |30controlPASS /6sourceFAIL → ACCESS06 |

Widths360/390/768/1024/1280/1440 are rendered matrix coverage. Stateful auth/deletion lifecycle uses390/1440; API/SQL checks have N/A width. This is not a claim of the full Cartesian product of every role/action/state/browser/width. Empty member/invitation sections are covered in initial and later team states; all other possible empty combinations not exhaustively enumerated. Native select keyboard action is checked; OS popup pixels/cross-browser rendering NOT RUN.

## 4. Backend / commands / regression

**338existing unique methods accepted PASS:** one completed321method module corpus via project `config.test_runner.KidsMapTestRunner`, plus17disjoint specialist screen security methods. 9of17 passed initially;8ENV failures were retried only as an8method subset after own runtime repair. No existing assertions changed. [Exact inventory/result](backend-verification.json), [selectors](full-test-selectors.json).

- [full-tests-final](full-tests-final.status.json): exit0; Found/Ran321,306.765s test time,389.702s process; OK. Fresh own testDB creation destroyed only its prior interrupted testDB, then destroyed it normally.
- [additional-security](additional-security.status.json):17,9PASS/8ERROR, exit1: missing pypdf in fixture setup.
- [parent-only recheck](additional-security-recheck.status.json):8ERROR, exit1: bounded child could not inherit parent's dependency path. Fail-closed validation preserved.
- [owned-runtime recheck](additional-security-owned-runtime.status.json):8/8PASS, exit0,2.612s test time.
- [proposed ACCESS06 regression](access06-proposed-RED.status.json):4methods,24expected source subtestFAIL,0ERROR; exit1,23.321s. Only QA proposal file, no app test-file added yet. Two positive methods preserve valid-code/phrase success and wrong-code denial. Expected RED is not module GREEN.
- Native per-script exits/counts in `*.status.json` and [commands.jsonl](commands.jsonl); exact reproducible driver invocations/hashes in [browser command provenance](browser-command-provenance.json). Private code substitutions/transcripts remain in ignored scratch.
- [finalize-owned](finalize-owned.status.json): exit0,5actual-now skipped/5SIMULATED-future completed. [Counters/readback](finalization.json). [Final synthetic state](state-final.json) omits deletion UUIDs/tokens.

Completed321body was not rerun. Later runs targeted independent missing coverage/environment or a newly found source cause. New proposed four tests are distinct from the338existing methods.

## 5. Browser, PNG и oracle provenance

Selected source-scope observations: **2232PASS /6FAIL**, [rows](accepted-observations.json). These are observations, not2238independent end-to-end tests.6FAIL all belong to ACCESS06. Native exit0 alone was never treated as semantic PASS.

[624native PNG manifest](png-manifest.json) covers the saved audit attempts, including retained QA failures. Not all624are accepted independent state proofs: earlier same-name duplicate attempts overwrote some own screenshots and are not counted as separate immutable evidence. Selected manual view: settings RU390, space-before/result EN390, team-long-select AZ360; [visual limits](visual-review.json). PNGs contain no working mail code/token/status URL bar. Other frames have native geometry/state checks and hashes, not a claim of manual review of every pixel.

[Oracle provenance](oracle-provenance.json) keeps60raw observations separately (58FAIL/2PASS): hidden empty avatar preview incorrectly counted as a broken visible image,250ms Escape visibility sampled before settled animation, and “suspended” API tested on an active grant. Original assertions/results remain. Independent rendered image/fallback36PASS, settled dialog18cells and actual inactive-grant9PASS resolve only those QA gaps. Source06FAIL was not removed or reclassified as harness.

Main matrix diagnostics: blocked external font requests/resource errors, no observed local request failures. Auth authoritative recovery captures pageerror/local failure0. Simulated dialog abort/409 are explicitly simulations. Console capture is scoped per scripted page/context; not a claim of a host-wide or cross-browser clean console.

## 6. Confirmed findings и policy notes

**ACCESS-QA-06 P3 OPEN:** added leading/trailing spaces are trimmed by CharField before the strict service sees them; HTTP accepts and deactivates. It contradicts help text and existing service whitespace test. Browser6cells and proposed HTTP/form24subfailures confirm it. Login and the correct own email-code remain required; no foreign-account deletion or data leak established. [Finding](FINDINGS.md), [minimal plan](PLAN-ACCESS-QA-06.md), [applicable un-applied diff](proposed-ACCESS-QA-06.diff).

Historical01/02/04/05repair reports retained;03 remains ORG-QA-02 alias, no duplicate patch. ACCESS05 four translations are accepted and were not expanded during AUDIT. Default inactive production policy was not activated.

After SIMULATED finalization5, linked person/owner data are unlinked, consent revoked, direct public doc access denied.6synthetic private documents remain for authorized reviewers/admin. Existing email/history/org-invite retention is not declared a leak or auto-fixed: real retention/legal/backup decisions and natural expiry remain outside this local simulation. Readback now has COMPLETED5/CANCELED4/SCHEDULED6; the latter are deliberately retained failing ACCESS06 fixtures, not unprocessed instances of the earlier5-case finalizer check.

## 7. QA failures, сохранность и исправления среды

All fixes here were QA harness/environment only; app0changes:

- Incomplete stock-runner attempt SIGTERM(-15),227.32s: own runner omitted project's state reset; not counted as completed321.
- Next runner import hit own `queue.py` shadowing stdlib and spawned a duplicate browser queue, not tests. Own duplicate tree stopped; file renamed browser_queue.py. [Preflight](runner-preflight.output.txt) verifies stdlib queue +canonical runner; successful321then ran once. Earlier repeated matrix/modal/auth outputs/receipts are retained where available; overwritten attempts are not counted separately.
- Initial auth script used a hidden desktop menu at390. New valid recovery family used actual mobile drawer; six successful cases are authoritative. RU console capture uses separate r3family. Early partial/signup duplicates are not accepted as completed chains.
- Initial post-image login selector matched login+hidden reset submit; zero-row failure retained, corrected separate r2QA script.
- Initial ACCESS06 fixture surname contained digits; registration correctly denied and deletion path NOT RUN. Separate r2uses the already-valid fictional surname; 6actual source failures are from r2.
- PDF dependency/child environment repaired only in own directories; parser limits/source/assertions preserved, only8affected methods rerun.
- Initial final-gate exit1 had26PASS/2QA-oracle mismatches: whitespace-stripped git status and removal of integer deletion id instead of secret subject_reference. [Original verdict](verification-initial.json) and [exact independent raw-status/sanitized-state proof](verifier-correction.json) retained. Corrected only these QA comparisons; no application/test assertions changed. Final gate rerun checks evidence, not the full backend/browser corpus.

Final gate compares all28813entry project files (only current07guide status edits allowed), shared MO,942source paths, HEAD/branch/active_run,62foreign container ID/name/ports/state and1known HTTP identity. Four older HTTP processes had already disappeared after the earlier chat interruption before this full entry; continuity remains NOT VERIFIED as recorded in ACCESS05, none restarted. This full run does not retroactively prove them preserved or prove arbitrary host-process/production availability. Only own HTTP processes were restarted with verified argv/cwd/source/PG identity. No reset/clean/stash/commit/push/deploy/active_run assignment.

## 8. NOT RUN / ограничения

New06patch/GREEN/final module PASS; global all-module corpus/module08; actual external Google OAuth/SMTP/integrations; natural retention waiting/backup expiry/legal approval; production/Nginx/deployment; cross-browser/real screen reader/native OS-popup pixel capture; exhaustive Cartesian role × all UI states × all widths. Synthetic stored documents test ACL/cache/consent, not the content of real user documents. No claim of production security/readiness or Google visibility.

## 9. Решение и следующий шаг

**Module07 LOCAL FAIL / OPEN ACCESS-QA-06.** Existing historical01–05closed locally in tested scope; no new repair automatically applied. The concrete new plan changes only `src/catalog/forms.py` (strip=False for one field) and adds one reviewed regression file. [Proposed diff/source hashes](access06-plan-source.json); git apply --check0. User approval of ACCESS05 does not authorize these files.

Следующий шаг — отдельное одобрение [PLAN ACCESS06](PLAN-ACCESS-QA-06.md), затем только целевые проверки и fresh source-provenance summary acceptance. [Copyable repair prompt](repair-ACCESS-QA-06.txt), [next prompt](next-prompt.txt), [final verification](verification.json). Module08 автоматически не начинать.
