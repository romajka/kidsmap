"""Fresh module08 bootstrap, immutable entry manifests; no app changes."""
from pathlib import Path
import json,hashlib,secrets,subprocess,datetime
P=Path(__file__).resolve().parent;R=P.parents[2];OLD=R/'docs/qa/module07-2026-10-10-r1'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
scratch=R/'.tmp/module08-20261010-r1';assert not scratch.exists();scratch.mkdir(parents=True)
prior={p.relative_to(R).as_posix():h(p) for top in ['docs/qa','docs/superpowers/plans','.agents'] for p in (R/top).rglob('*') if p.is_file() and P not in p.parents and '__pycache__' not in p.parts}
for x in ['AGENTS.md','docs/task33/implementation-status.md']:prior[x]=h(R/x)
(P/'preservation-entry.json').write_text(json.dumps(prior,indent=2),encoding='utf-8')
(P/'journal-entry.txt').write_bytes((R/'docs/qa/module-acceptance-prompts.md').read_bytes())
(scratch/'credential').write_text(secrets.token_hex(20))
(P/'screenshots').mkdir()
(scratch/'playwright.json').write_text(json.dumps({'browser':{'browserName':'chromium','launchOptions':{'executablePath':'C:/Users/Ramin/AppData/Local/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-win64/chrome-headless-shell.exe','headless':True},'contextOptions':{'viewport':{'width':1440,'height':950}}},'outputDir':str(scratch/'playwright')}))
for name in ['run.py','qa_settings.py','drive.py','check-js.cjs']:
 s=(OLD/name).read_text(encoding='utf-8').replace('module07','module08').replace('55438','55439').replace('8820','8821')
 if name=='qa_settings.py':s=s.split('# SIMULATED existing test retention policy')[0].replace("'qa_mail.EmailBackend'","'django.core.mail.backends.locmem.EmailBackend'")
 if name=='drive.py':s=s.replace("source=source.replace('__EXPIRED_CODE__',(here.parents[2]/'.tmp/module08-20261010-r1/expired-code').read_text())",'')
 (P/name).write_text(s,encoding='utf-8')
ps="ConvertTo-Json -InputObject @(Get-NetTCPConnection -State Listen | Where-Object { ($_.LocalPort -ge 8810 -and $_.LocalPort -le 8830) -or ($_.LocalPort -ge 55431 -and $_.LocalPort -le 55445) } | Select-Object LocalAddress,LocalPort,OwningProcess) -Compress"
q=subprocess.run(['powershell','-NoProfile','-Command',ps],capture_output=True,text=True)
d=subprocess.run(['wsl.exe','--','docker','ps','--format','{{.Names}} {{.ID}} {{.Ports}}'],capture_output=True,text=True)
entry={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'http':json.loads(q.stdout),'docker':d.stdout.splitlines(),'http_exit':q.returncode,'docker_exit':d.returncode}
assert not any(x['LocalPort'] in [8821,55439] for x in entry['http'])
(P/'stands-entry.json').write_text(json.dumps(entry,indent=2))
docs=['AGENTS.md','.agents/README.md','.agents/registry.json','.agents/agents/kidsmap-orchestrator/agent.md','.agents/knowledge/architecture.md','.agents/knowledge/source-of-truth.md','.agents/rules/audit-contract.md','docs/qa/content-entry-audit-2026-10-06.md','docs/qa/module-acceptance-prompts.md']
(P/'documents.json').write_text(json.dumps({'checked':docs,'missing':[x for x in docs if not (R/x).is_file()]},indent=2))
(P/'PLAN.md').write_text('''# Модуль08 — свежий AUDIT ONLY

Один /root выполняет роли orchestrator, frontend-admin, Django/security и browser-qa последовательно. Ownership: собственный run08, ignored scratch/PG/HTTP/browser и строка08 журнала. Приложение/правила/миграции/assertions не менять. Без production, commit/push/deploy. История только checklist.

- [ ] Snapshot/source/runtime/preservation; graph-first architecture и актуальные surfaces/ACL.
- [ ] Новый PG55439/HTTP8821; отдельные DB/testDB/cache/media/private-media/email/cookies; synthetic fixtures.
- [ ] Native очереди/search/filter/pagination/counters; approve/reject/reason/resubmit/withdraw и обработанная заявка; candidate/live/photos/related/readiness.
- [ ] Native два reviewers/tabs/version/repeat/batch partial failure; volunteer assignment/editor/submit/revoke; denial HTTP и state comparison; logs/private docs.
- [ ] RU/AZ/EN×360/390/768/1024/1280/1440 rendered tables/sidebar/filter/modal/error/loading/conflict/keyboard; screenshots/console/network.
- [ ] Unchanged targeted tests, exact commands/exits; nine-section report/findings MOD-QA/prompts, matrix/PNG hashes/NOT RUN; preservation и только row08/handoff09. Модуль13 последним.
''',encoding='utf-8')
print('Fresh QA08 bootstrap; foreign files',len(prior))
