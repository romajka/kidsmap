# SOCIAL-QA-10 — recheck / PLAN

LOCAL current WORKTREE, /root canonical kidsmap-orchestrator, 2026-10-18 Asia/Baku. No independent agent claims. Mode PLAN ONLY. Alias ADJ-ANONYMOUS-LOGIN-08, count once.

## 1. Состояние

CONFIRMED OPEN/P2; concrete two-file plan complete, implementation approval pending. C:/kidsmap transfer branch, HEAD852938d96764ae315b92859e3651e5ea62054a36, source1024 unchanged, index/ref/active_runNONE retained. [План](IMPLEMENTATION_PLAN.md), [точный diff](proposed.diff), [candidate manifest](candidate-manifest.json).

Fresh own app m09s10-plan-r1-app and loopback33390; existing owned isolated m09full-r1-pg reused only after running/volume/internal-network identity proof. New test_m09s10_plan_r1, cache/media/private-media/locmem email and own3MO; no production credentials/.env. Runtime verifies source and locale manifest before django.setup, sole LOCALE_PATHS. Normal QA fixture DB belongs to the preceding full audit; browser repro uses guest GETs only.

## 2. Что работает

Actual localized auth/login returns200/form in every cell. Four candidate guard/next regressions already pass; four shared tests retain foreign404, revoked403, method/CSRF guards and external-next rejection. No access bypass established.

## 3. Дефект и причина

18native RU/AZ/EN×six widths: protected inbox302→/accounts/login/404, expected login recovery FAIL18.54 guest action GET header probes share the same default login target.0 unhandled pageerrors;18 expected404 console errors retained. Native screenshot manifest and recheck.json are current proof.

Four unparameterized login_required decorators are in workflow_notifications.py. Existing location-resolution and account CBV patterns already specify account_login. Named route is auth/login; no matching accounts/login route. Scope: four explicit named-login decorators plus one new eight-method test file; preserve decorator order and all bodies. Global LOGIN_URL and shared auth/routes/templates/PO/services/schema remain outside scope. POST next semantics remain original; authenticated GET to an action remains405, never automatic POST replay. This plan fixes target resolution/inbox recovery, not expired POST UX redesign.

## 4. Tech debt

Dynamic Django decorator/route edges are not complete in graph. Generation2026-10-16T18:56:53Z, relevant metadata changed; direct source verified. No global setting change merely because it is fewer lines.

## 5. Risks

Touching a controller already carrying approved SOCIAL08 changes requires exact diff and preservation. Global settings would have wider/default third-party impact; bounded decorators follow existing source convention. Keep all _mine/locks/currentness/CSRF/method/ownership logic intact. Production applicability/introduction UNKNOWN.

## 6. Dead/legacy

No deletion or legacy cleanup proposed. Graph absence is not evidence to remove anything.

## 7. Тесты и ограничения

Candidate outside app path:8methods,4failed methods/24subtest assertion failures,4PASS. Four affected existing methodsPASS. Total12methods,24failures/0errors,exit1,1.535s. Exact command/labels and output in evidence/red-tests.sh and red-tests.log; assertions unchanged. Exact candidate was not applied; GREEN and candidate rendered preview NOT RUN. No repeat of the successful169-method full module corpus. Physical devices/screenreader/cross-browser/external services/global suite/production NOT RUN.

## 8. Рекомендация / handoff

Approve [IMPLEMENTATION_PLAN](IMPLEMENTATION_PLAN.md): four @login_required(login_url="account_login") lines in the controller and new test_social_qa10_notification_login.py with8methods. After approval exact patch,12targeted GREEN,18native cells plus actual password/inbox round trip per language, preservation and scoped closure. Existing full ACCEPT09 applies only to prepatch1024 snapshot; SOCIAL11/module09 remain OPEN. No automatic module10 or fix11.

## 9. Приоритет

SOCIAL10/P2 OPEN; scoped implementation approval pending. No P0/P1 established. No application changes, commit/push/deploy/reset/clean/stash/checkout switch or active_run assignment. Previous15 packages and guide history preservation are checked in verification.json.

За время PLAN m09s06-plan-r1-app изменил running→exited; причина UNKNOWN, агент не останавливал/не перезапускал entry containers.52идентичности сохранены; actual state delta записан в container-preservation.json и verification.json.
