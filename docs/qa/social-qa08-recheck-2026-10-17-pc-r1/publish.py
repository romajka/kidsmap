import hashlib,json,re,subprocess,shutil
from datetime import datetime,timezone
from pathlib import Path
from urllib.request import urlopen
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/social08-pc-plan-r1';O=R/'docs/qa/social-qa08-recheck-2026-10-17-pc-r1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def save(n,d):(O/n).write_text(json.dumps(d,ensure_ascii=False,indent=2)+'\n')
e=json.loads((Q/'entry.json').read_text());assert all(sha(R/p)==h for p,h in e['sources'].items()) and len(e['sources'])==1022
assert not (R/'src/catalog/testcases/test_social_qa08_invitation_feedback.py').exists()
assert all(sha(R/p)==h for p,h in e['shared_mo'].items());assert sha(R/'.cbmignore')==e['cbmignore_sha256']
for name,files in e['prior_packages'].items():assert all(sha(O.parent/name/p)==h for p,h in files.items()),name
m=json.loads((Q/'matrix.json').read_text());assert len(m)==36 and len({r['item']['key'] for r in m})==36
assert all(all(r['controls'].values()) and not any(r['source'].values()) and not r['pageerrors'] for r in m)
assert all(r['facts']['response_body_length']==0 for r in m)
assert all(all(f['url'].endswith('/accept/') and f['error']=='net::ERR_HTTP_RESPONSE_CODE_FAILURE' for f in r['request_failed']) for r in m)
assert all(all(h['status']==403 and h['url'].endswith('/accept/') for h in r['http_failures']) for r in m)
log=(Q/'tests.log').read_text();assert (Q/'tests.exit').read_text().strip()=='1' and 'Ran 9 tests in 1.706s' in log and 'FAILED (failures=14)' in log and not re.search(r'^ERROR:',log,re.M)
failed_methods=sorted(set(re.findall(r'^FAIL: (\w+)',log,re.M)));assert len(failed_methods)==5
infos=json.loads(subprocess.check_output(['docker','inspect','m09s08-plan-r1-app','m09s08-plan-r1-pg']));app,pg=infos
assert all(i['State']['Running'] for i in infos) and app['HostConfig']['ReadonlyRootfs'];assert set(app['NetworkSettings']['Networks'])=={'m09s08-plan-r1-net'}
assert any(x['Destination']=='/mnt/c/kidsmap' and not x['RW'] for x in app['Mounts'])
assert all(not x['RW'] or x['Destination']=='/mnt/c/kidsmap/.tmp/social08-pc-plan-r1' for x in app['Mounts'])
assert json.loads(subprocess.check_output(['docker','network','inspect','m09s08-plan-r1-net']))[0]['Internal']
containers=subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines();assert set(e['containers']).issubset(containers) and len(containers)==43
save('ownership.json',{'app_id':app['Id'],'pg_id':pg['Id'],'internal_network':True,'app_readonly_root':True,'mounts':[{'destination':x['Destination'],'RW':x['RW']} for x in app['Mounts']],'profile':'social08-pc-plan-r1','loopback33358':True,'browser_session':'social08-pc-plan-r1'})
git=json.loads((Q/'git-final.json').read_text(encoding='utf-8-sig'));assert all(git[k]==e[k] for k in ['head','branch','index_tree','task33_ref']) and not git['staged']
assert [l for l in (R/'docs/task33/implementation-status.md').read_text().splitlines() if l.startswith('active_run:')]==['active_run: NONE']
info=json.loads(urlopen('http://127.0.0.1:33358/qa/info/').read());assert info['source_files']==1022 and info['testing'];assert all(info['hashes'][p]==sha(R/p) for p in info['hashes'])
final_cases={r['item']['key']:json.loads(urlopen('http://127.0.0.1:33358/qa/state/'+r['item']['key']+'/').read()) for r in m};assert all(x['status']=='CANCELED' and x['memberships']==x['grants']==0 for x in final_cases.values())
for n in ['matrix.json','tests.log','tests.exit','candidate_tests.py','cell-body.js','cell-body-attempt1.js','cell-body-attempt2.js','matrix.py','browser_driver.py','browser-initial-cli.txt','browser-commands.jsonl','console-cli.txt','fixtures.py','qa_urls.py','runtime.py','tests.sh','playwright.json','graph-evidence.json','preparation-attempts.json','failure-place-ru-360.txt','failure-place-ru-1280.txt','inspect-denial-cli.txt','manual-visual-review.md','git-final.json','bootstrap.py','bootstrap-attempt1.py','prepare-helpers.py','build-candidate.py']:
 if n=='candidate_tests.py':continue # normalized exact candidate already present in package
 shutil.copyfile(Q/n,O/n)
shutil.copyfile(Q/'locales/manifest.json',O/'locales-manifest.json')
(O/'png').mkdir(exist_ok=False)
for p in (Q/'png').glob('*.png'):shutil.copyfile(p,O/'png'/p.name)
assert len(list((O/'png').glob('*.png')))==75
save('png-manifest.json',{p.relative_to(O).as_posix():sha(p) for p in (O/'png').glob('*.png')});save('source-final.json',{'sources':e['sources']});save('live-final.json',info);save('containers-final.json',containers);save('business-final.json',final_cases)
summary={'utc':datetime.now(timezone.utc).isoformat(),'status':'PLAN COMPLETE; SOCIAL-QA-08 CONFIRMED OPEN/P2; implementation approval PENDING','snapshot':{'head':git['head'],'branch':git['branch'],'source_files':1022,'application_changes':0},'candidate':{'scope':['src/catalog/controllers/workflow_notifications.py','src/catalog/testcases/test_social_qa08_invitation_feedback.py'],'new_test_methods':9,'apply_check_exit':0,'applied':False,'candidate_live_rendering':'NOT RUN'},'tests_RED':{'unique_methods':9,'failed_methods':5,'passed_methods':4,'assertion_subtest_failures':14,'errors':0,'seconds':1.706,'exit':1,'failed_method_names':failed_methods},'native':{'cells':36,'controlsPASS':sum(sum(r['controls'].values()) for r in m),'sourceFAIL':sum(sum(not v for v in r['source'].values()) for r in m),'expected_empty403':36,'expected_requestfailed':sum(len(r['request_failed']) for r in m),'pageerrors':0,'unexpected_http_failures':0,'unexpected_requestfailed':0,'png':75},'preservation':{'prior_packages':10,'entry_container_ID_name_states':41,'final_containers':43,'sources_all_unchanged':True,'sharedMO_cbmignore_refs_index_activeNONE':True},'not_run':['candidate/live GREEN','implementation08','SOCIAL09','full ACCEPT09','global corpus','production','physical devices','real screenreader/full WCAG','other browsers','external email/integrations','complete per-cell console history']}
save('results.json',summary)
(O/'REPORT.md').write_text('''# SOCIAL-QA-08 — CONFIRMED OPEN/P2, PLAN COMPLETE

Execution /root,2026-10-17 Asia/Baku; django-reviewer lead, frontend/security/browser checks sequentially by same agent. No independent subagent execution. Canonical definitions/registry/architecture/source-of-truth/audit-contract read. Mode PLAN only; application changes0, implementation approval pending. LOCAL HEAD852938d96764ae315b92859e3651e5ea62054a36, branch codex/module09-transfer-2026-10-16-r1; dirty WORKTREE03–07 preserved. PRODUCTION applicability UNKNOWN, no production access.

## Finding and cause

Fresh isolated current1022source reproduces SOCIAL-QA-08 for Place and Organization invitation recipients. Owner creates an invitation through real UI; recipient opens inbox; separate owner browser context cancels through real UI; recipient keyboard focuses/Enter submits stale Accept. Server correctly returns403/body0, CANCELED remains, no membership or grant. Current Chromium155 displays its native Access denied / HTTP ERROR403 document (chrome-error://chromewebdata/), rather than simply a white page. Both lack KidsMap explanation, app shell and recovery link. Historical white-page wording is not copied as current literal browser appearance. SeverityP2/confidenceHIGH/reproducible; no access bypass, permanent data loss or production incident established.

Source src/catalog/controllers/workflow_notifications.py:accept_invitation (~74–83): own notification resolved by _mine before service call; caught ValidationError/TeamConflict/PermissionDenied/missing invitation becomes HttpResponseForbidden() with no body. Actual services/business_team.py:accept and decide_invitation guards correctly reject CANCELED/expired/stale ownership and preserve transactions. Routes in catalog/urls.py bind this controller; legacy place owner repository delegates actual invite/cancel to same service; Organization workspace native forms use business_team_api. Source edges verified, not inferred from graph alone.

Existing _render_inbox and account_notifications.html already provide scoped own items, localized invitation_unavailable text, role=alert, styled account shell and navigation link back to GET inbox. Proposed minimal fix reuses these, preserves HTTP403/service/ACL/CSRF/login/POST behavior, removes only now-unused HttpResponseForbidden import. No template/CSS/JS/PO/services/models/schema/routes edits. Exceptions and foreign invitation details never shown; foreign/missing notification stays404 before handler.

## Fresh proof

36native cases: Place/Organization×RU/AZ/EN×360/390/768/1024/1280/1440.468controlPASS/108sourceFAIL. Each has actual owner invite/cancel, recipient native keyboard submit, denial403, no access/no denial write, GET inbox/reload recovery and revoked action hidden. All36 responses body length0. Expected browser-native HTTP403 request failures are recorded separately, pageerrors0/unexpected HTTP or request failures0.75PNG:72matrix images+3retained attempt screenshots. Console inspection covers final recovered GET only (0errors/0warnings); complete per-cell console history not retained, no claim of full console PASS. Manual visual subset recorded separately; not all75 manually inspected.

Candidate regressions ran outside application as candidate_tests.SocialQA08InvitationFeedbackTests:9unique methods,5failed/4passed,14assertion/subtest failures,0errors,1.706s,exit1. Failing assertions are missing localized feedback on revoked/expired/ownership-stale/missing-own-invite/repeat-accepted cases; status/no-grant/no-write assertions precede them. Foreign/nonexistent404, changed-email404, anonymous/GET/CSRF guards and current invitation success pass. Existing assertions unchanged. Candidate controller and9-method test AST parse and exact diff git apply --check --ignore-space-change exit0; patch not applied, candidate live rendering/GREEN NOTRUN.

## Impact and bounded plan

Only src/catalog/controllers/workflow_notifications.py and new src/catalog/testcases/test_social_qa08_invitation_feedback.py. Existing UI and safe generic copy reused; failed own error path reads current own inbox (up to100items). Service semantics/transaction locks/grants/outbox/permissions unchanged. No migration/SEO/public indexing impact; no dead-code/deletion proposal. Extra render reads may cost more than empty response; appropriate to recovery UX, optimization outside scope. Exact code/hashes and12-method post-approval/native acceptance in IMPLEMENTATION_PLAN.md/proposed.diff/candidate-manifest.json.

## Isolation and preservation

New own social08-pc-plan-r1 profile, m09s08-plan-r1-app/pg/internal network/volume, PostgreSQL17.11, Python3.12.15/Django6.0.2. RO repository bind, own scratch RW, cleared env/DJANGO_TESTING1, isolated cache/media/private-media/locmem email, own normal DB m09s08_plan_r1 and testDB test_m09s08_plan_r1. Fresh native RU/AZ/EN MO built/verified before every setup as sole LOCALE_PATHS; sharedMO untouched. Headless owned Chromium/session social08-pc-plan-r1, loopback33358, browser external requests blocked by localhost allowlist. No external SMTP delivery run in normal fixture DB. Owner native actions mutate only own fictional DB; no denial grants or notifications/outbox/read mutations. Harness retries leave additional CANCELED fictional invitations/outbox rows; retained, no cleanup. Final per-case readback business-final.json.

All1022application source hashes unchanged, future new test absent. HEAD/index/task33-progress/active_run:NONE/sharedMO/.cbmignore and10previous current-PC packages preserved byte-for-byte.41entrycontainer ID/name/state retained,+2own containers=43; only own serving Python restarted once to reload corrected QA state helper. This does not establish whole-machine process continuity. Historical partial PNG packages untouched, no downloads. Guide receives separate PLAN08 note with reverse-hash proof of preserved prior bytes.

## Preparation failures, limitations, next step

preparation-attempts.json retains initial too-broad historical package selector, bounded source path corrections, expected403 URL wait mismatch and error-document navigation timing race. Raw native failures/attemptPNG retained; first4completed native cells reused, only failed cases retried with new actual invitations; assertions/test expectations not relaxed to claim green. Current browser-native error handling distinguishes expected empty403 transport failure from unrelated network errors.

Graph C-kidsmap ready, generation2026-10-16T18:56:53Z,120partial files; relevant coverage metadata_changed/unavailable, so all critical edges source-verified. No cache export/reindex/graph completeness claims.

SOCIAL01–07 retain their scoped LOCAL closures;08OPEN/P2; module09OPEN. Next step is approval of this exact two-file plan, then targeted12methods/native36cells and guards in a new fix-run. No extra approval for this planning work is needed. Implementation08, SOCIAL09/fullACCEPT09/global/production/physical devices/realSR/fullWCAG/otherbrowsers/external integrations NOTRUN. No commit/push/deploy/reset/clean/stash/dirty checkout switch/active_run assignment.
''',encoding='utf-8')
(O/'commands.md').write_text('''# Commands and outcomes

- Native Windows git refs/index/status and source hashes:0. bootstrap.py preserves1022sources/10explicit complete current-PC artifact packages/41containers; first historical-selector guard stopped1 before runtime, corrected0. No remote pull/reset/checkout.
- build_isolated_locales.py build --output /mnt/c/kidsmap/.tmp/social08-pc-plan-r1/locales --locales ru az en --compiler native:0,3catalogues; verify before every Django setup.
- Newly reviewed own start.sh then own prepare.sh:0; isolated create/migrate/fictional fixture seed/serve. Historical prepare scripts not executed.
- browser_driver.py open --config /mnt/c/kidsmap/.tmp/social08-pc-plan-r1/playwright.json:0; browser-initial.js:0. browser_driver uses npx --yes --package node@24 --package @playwright/cli playwright-cli -s=social08-pc-plan-r1; per-command exits browser-commands.jsonl. Native partial failures retained separately, completed cells not repeated.
- docker exec m09s08-plan-r1-app python /mnt/c/kidsmap/.tmp/social08-pc-plan-r1/runtime.py test candidate_tests.SocialQA08InvitationFeedbackTests:1, expected RED9methods/14assertion failures/0errors/1.706s. New tests outside application path, candidate controller not loaded.
- build-candidate.py:0; Python AST for both candidates and git apply --check --ignore-space-change docs/qa/social-qa08-recheck-2026-10-17-pc-r1/proposed.diff:0. No git apply mutation.
- Final matrix.py resumed remaining cases:0,36complete cells/468controlPASS/108sourceFAIL, no unrelated network/pageerrors. Expected empty403 browser-native failures separately captured. Native owner forms create/cancel and recipient real Enter action; no response/DOM stubs.
- browser_driver.py console error:0, captured console-cli.txt; final recovered GET document console0errors/0warnings only; per-cell pageerrors/HTTP/request failures captured separately, complete per-cell console history not retained.
- git-final.ps1:0; publish.py and verify_integrity.py:0 required before PLAN delivery. These verify source/candidate/old artifacts/container/ref/index/MO/guide preservation; this is not application GREEN.
''',encoding='utf-8')
(O/'status-note.md').write_text('''## SOCIAL-QA-08 — свежий PLAN на этом ПК (2026-10-17)

SOCIAL08 CONFIRMED OPEN/P2, PLAN COMPLETE, implementation approval PENDING. Fresh1022source,36native Place/Organization×RU/AZ/EN×6widths:468controlPASS/108sourceFAIL; real owner invite/cancel and stale recipient keyboard Accept →403/body0, Chromium native error screen, no app feedback/recovery.9candidate methods outsideapp:5failed/4passed,14assertion/subtest failures,0errors; guards/current success pass.75новыхPNG. Proposal только workflow_notifications.py + новый test_social_qa08_invitation_feedback.py: existing _render_inbox/error=invitation_unavailable/status403; template/CSS/JS/PO/services/schema unchanged. [REPORT](social-qa08-recheck-2026-10-17-pc-r1/REPORT.md), [точный план](social-qa08-recheck-2026-10-17-pc-r1/IMPLEMENTATION_PLAN.md), [verification](social-qa08-recheck-2026-10-17-pc-r1/verification.json). Appchanges0/candidate liveGREEN NOTRUN. Source1022/dirty03–07/HEAD/index/task33-progress/activeNONE/sharedMO/.cbmignore/10priorpackages/41entrycontainerIDs-states preserved;foreignrestart0,wholemachinecontinuityNOTVERIFIED. SOCIAL01–07 scopedCLOSEDLOCAL/module09OPEN;09/fullACCEPT09/global/production/commit/push/deploy NOTRUN. Следующий шаг — одобрение точного two-file scope08.
''',encoding='utf-8')
(O/'NEXT_PROMPT.txt').write_text('Продолжить KidsMap C:/kidsmap, ветка codex/module09-transfer-2026-10-16-r1 HEAD852938d96764ae315b92859e3651e5ea62054a36. Сначала AGENTS/canonical entry/guide и docs/qa/social-qa08-recheck-2026-10-17-pc-r1/REPORT.md,verification.json,IMPLEMENTATION_PLAN.md,candidate-manifest.json,source-final.json. PLAN08 готов, application changes0, scope controller workflow_notifications.py + новый test_social_qa08_invitation_feedback.py, implementation approval PENDING. После конкретного human approval использовать этот exact diff, не спрашивать повторно; без approval app patch не применять. Source1022 все прежние; RED9methods5failed4pass14assertions/noerrors, native36cells468controlPASS108sourceFAIL,75PNG. Own runtime reuse только fresh source/ownership/internalnet/soleMO proof; старые commands evidence не автоскрипты. Сохранить dirty03–07/priorpackages/containers; без reset/clean/stash/switch/commit/push/deploy/production/active_run assignment. SOCIAL09/fullACCEPT09/global/module10 не начинать автоматически.\n',encoding='utf-8')
g=R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md';b=g.read_bytes();assert sha(g)==e['guide_sha256'];note=(O/'status-note.md').read_bytes().rstrip(b'\n')+b'\n\n';marker='## Сколько задач осталось и как идти'.encode();assert b.count(marker)==1;g.write_bytes(b.replace(marker,note+marker,1));assert hashlib.sha256(g.read_bytes().replace(note,b'',1)).hexdigest()==e['guide_sha256']
shutil.copyfile(Path(__file__),O/'publish.py');print(json.dumps(summary,ensure_ascii=False))

