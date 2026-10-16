# ACCEPT-02 — IN PROGRESS, два scope approvals pending

2026-10-13 Asia/Baku; root, kidsmap-orchestrator `.agents/agents/kidsmap-orchestrator/agent.md`. Последовательное исполнение, независимые specialist runs не заявлены. LOCAL `/home/ramin/kidsmap`, task33-progress, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51 +dirty WORKTREE, active_run NONE. Production UNKNOWN / NOT RUN. Полного PASS module02 нет.

## 1. Состояние области

Пользователь одобрил два конкретных plans ORG-QA-03/04. Application changes только CSS и AZ/EN PO; [reviewable diff](APPROVED_DIFF.patch). Fresh acceptance обнаружила RU fallback regression того же ORG-QA-04 и отдельный baseline ORG-QA-05. Дополнения требуют отдельных concrete approvals; вопросы представлены пользователю, ответов пока нет. Никаких других findings исправлений, commit/push/deploy/production.

[Entry](entry.json), [verification](verification.json): current source match, чужие source/assertions/shared MO и215 прежних NETWORK evidence files сохранены, active_run/HEAD неизменны. Изменения предыдущих PLACE/ORG patches сохранены; не приписываются этому diff.

Собственный runtime `http://127.0.0.1:47277` см. фактический [server.json](server.json) как authority для порта, PID59977; DB module02full_20261013_r1, shared только собственный PG17.10 container module02-remaining-recheck-2026-10-13-r1-pg,127.0.0.1:35715. Уникальные cache/media/private-media/email/cookies/browser session. DJANGO_TESTING=1, наследуемый env очищается; no checkout .env/production credentials; secrets только ignored scratch mode600. Own cloned schema/data затем flush **только этой новой DB**, synthetic seed7actors/32 rich Places; все проверяемые affiliations выполнялись native UI/API. Fixture setup для общей опубликованной программы и expired invitation явно отдельно. После native creation новой ветки33 — own fixture total33.

Fresh RU/AZ/EN [locale manifest](locale-manifest.json), sole LOCALE_PATHS before setup, helper build/verify exit0, shared MO не перезаписаны. [Startup/disk match](runtime-version-final.json). Egress server только own PG; browser remote requests blocked. Real SMTP/SDK NOT RUN.

## 2. Сильные стороны / выполненные сценарии

[Functional index](functional-index.json):93 raw assertions,91PASS/2FAIL. Это функциональный промежуточный пакет, не full matrix или module PASS.

| Сценарий | Fresh evidence |
|---|---|
| Создание без филиалов, partial reload/error/input preservation, draft/server autosave, submit/approve/public, published working draft без изменения live | `lifecycle.result.json`:10PASS |
| Published candidate → return reason → correction/resubmit → approve → публичная версия | `published-roundtrip.result.json`:5PASS, текущий public UUID найден заново |
| Name/address search → native preview → confirm10 rich existing Places | `bulk.result.json`:4PASS; hashes before/after, фото/занятия/groups/pricing/schedule/IDs/owner сохранены |
| Foreign private IDs/API/legacy/no rights; два owner consent; duplicate confirm; owner change invalidates consent; legacy detach requires preview | `api-core.result.json`:19PASS |
| Mixed batch: already_connected / other_network / changed / connected / requested, actual transfer between preview/confirm, same-key replay | `advanced-connections.result.json`, canonical exact codes в `readback.json` |
| Stale request recovery cancel/new consent, other-party refusal, delivery loss receipt/retry | `recovery-lost.result.json`:6PASS; SIMULATED browser response delivery loss, server operation real |
| Detach approved common program, direct grant survives/network access removed; native explicit transfer A→B; create separate branch33 | `detach-transfer.result.json`:7PASS; protected hashes/snapshot preserved before/after |
| Role descriptions/pending-no-access/native inbox accept | `team.result.json`:6PASS |
| Recipient rejection real API, owner cancel, replay refusal, direct grant, employee cannot manage | `team-api.result.json`:7PASS |
| Native role change/two-tab409/revoke/reload/denial/direct grant; selected scope invite/accept/allowed selected/denied other; native pending cancel | `team-management.result.attempt1791870206.json`:12PASS |
| NoJS honest disabled controls, missingCSRF403, GET405, receipt actual other actor inaccessible | `nojs-security.result.json`:4PASS |
| Expired invitation real canonical accept denied | `expiry.result.json`:1PASS; SIMULATED expiry timestamp fixture |
| Admin create/draft/submit/approve/candidate, selection/business consent/informational confirmation | `admin-flow.result.json`:8PASS/1raw probe FAIL, state verified published in READ ONLY readback |

[Readback](readback.json) — explicit READ ONLY, statement_timeout10s/lock_timeout2s: eight invariant flags true, exact mixed result map, admin organization4 published, bulk ten connected, detach11, explicit transfer14→B, branch33, informational27 owner unchanged. [Preservation](preservation-before.json)/[after](preservation-after.json) hashes10 unchanged. [Detach before](detach-before.json)/[after](detach-after.json): owner/status/snapshot/group/pricing/media preserved, common-program link became local.

## 3. Реальные проблемы / failures

**ORG-QA-04 OPEN**: после approved AZ/EN entries RU отсутствующие14 strings fallback к default az. Lazy labels на RU дают AZ. [Repair report](../org-qa04-fix-2026-10-13-r1/REPORT.md), [concrete RU expansion plan](../org-qa04-fix-2026-10-13-r1/PLAN-RU-FALLBACK.md). RU файл ранее явно не входил в scope. Незакрытая regression сохранена, не замаскирована PASS.

**ORG-QA-05 P2 OPEN**: mobile columns dropdown x=-31.296875, mouse checkbox вне viewport. [Baseline/patch comparison](../org-qa03-fix-2026-10-13-r1/columns-baseline.result.json) воспроизводит то же на исходном entry CSS. [Plan](../org-qa03-fix-2026-10-13-r1/PLAN-ORG-QA-05.md): margin-left:auto в existing `.km-columns-details`. Temporary QA prototype18/18 geometry/mouse PASS, не application acceptance.

Raw mixed-row FAIL — QA text case mismatch: ожидалось uppercase «Измен», UI корректно пишет «Данные изменились»; exact canonical map readback верен. Assertions приложения не менялись, raw сохранён. Raw admin-approve count FAIL не трактуется автоматически как business failure: actual state published, subsequent rendered unpublish button available. Count discrepancy root cause не доказана окончательно; fresh visible-state gate остаётся NOT RUN, первоначальный FAIL не переписан.

Harness попытки: `team-management.result.json` timeout на ошибочном guessed data attribute, до mutations; corrected literal actual `data-grant-row` попытка12PASS. QA helper `preservation.py` сначала использовал неверный `photos` manager, исправлен на actual `gallery`, before/after сохранены. HTTP/CLI exit0 не равен acceptance; errors и rows учитываются отдельно.

## 4. Tech debt

Shared CSS mobile popup alignment и default-catalogue RU fallback требуют маленьких отдельным образом согласованных corrections. Global translation cleanup не входит.

## 5. Risks

Current dirty diff содержит известную RU regression. Production не изменялся. Старый pre-patch recheck runtime оставлен нетронутым, его source snapshot после patch исторический. Three new owned profiles source/current match. Credentials не включены в reports; original launcher другого ПК не запускался.

## 6. Dead/legacy

Legacy paths проверены как поддержанные; удаления не выполнялись.

## 7. Tests gaps / NOT RUN

[Explicit test discovery](discovery.json):248 уникальных IDs по19 labels. Global corpus/CROSS-QA-02 discovery не принят. Полный module test run **ещё NOT RUN**, чтобы выполнить его один раз после всех locale corrections. Целевые4 существующих locale/admin tests входят в этот состав. Final RU/AZ/EN×6widths lifecycle/rendered matrix и PNG visual review **ещё NOT RUN**; существующие scoped repair matrices и91 raw functional PASS не заменяют этот этап. Полный module02 acceptance, production, реальные внешние integrations и другие modules НЕ приняты.

## 8. Handoff

Два concrete approvals pending: RU fallback plan и ORG-QA-05. После approval исправить ровно их files/IDs; новые fresh locale manifests и только owned runtimes; affected native UI checks, final full matrix и один248 test run. Сохранённые business-transition evidence можно применять через доказанный source provenance, не повторять неизменённые core transitions ради количества. Other findings остаются OPEN до собственного scope. [Next prompt](next-prompt.txt).

## 9. Приоритеты

ORG-QA-01/02 ранее LOCAL scoped accepted; ORG-QA-03 nowrap root repair доказан, полное panel/module closing зависит от QA05. ORG-QA-04 P3 OPEN (RU regression), ORG-QA-05 P2 OPEN. Новый P0/P1 не подтверждён. Verdict INCOMPLETE, не PASS.
