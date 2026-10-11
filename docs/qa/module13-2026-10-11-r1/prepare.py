from pathlib import Path
import subprocess,json,hashlib,secrets,datetime
P=Path(__file__).resolve().parent;R=P.parents[2];OLD=R/'docs/qa/module12-2026-10-11-r1';S=R/'.tmp/module13-20261011-r1'
assert not S.exists(),'Run already exists'
S.mkdir(parents=True);(S/'credential').write_text(secrets.token_hex(20));(P/'screenshots').mkdir(exist_ok=True)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard'],cwd=R,text=True).splitlines()
prior={x:sha(R/x) for x in files if (R/x).is_file() and P not in (R/x).parents and '__pycache__' not in x and not Path(x).name.startswith('.env')}
(P/'preservation-entry.json').write_text(json.dumps(prior,indent=2),encoding='utf-8')
(P/'journal-entry.txt').write_bytes((R/'docs/qa/module-acceptance-prompts.md').read_bytes())
ps="ConvertTo-Json -InputObject @(Get-NetTCPConnection -State Listen | Where-Object { ($_.LocalPort -ge 8810 -and $_.LocalPort -le 8840) -or ($_.LocalPort -ge 55431 -and $_.LocalPort -le 55445) } | Select-Object LocalAddress,LocalPort,OwningProcess) -Compress"
q=subprocess.run(['powershell','-NoProfile','-Command',ps],capture_output=True,text=True)
d=subprocess.run(['wsl.exe','--','docker','ps','--format','{{.Names}} {{.ID}} {{.Ports}}'],capture_output=True,text=True)
assert q.returncode==d.returncode==0
entry={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'http':json.loads(q.stdout),'docker':d.stdout.splitlines(),'http_exit':q.returncode,'docker_exit':d.returncode}
assert not any(x['LocalPort'] in [8831,8832,55444] for x in entry['http'])
(P/'stands-entry.json').write_text(json.dumps(entry,indent=2))
for name in ['run.py','qa_settings.py','drive.py','check-js.cjs','common.js','qa_urls.py']:
 s=(OLD/name).read_text(encoding='utf-8').replace('module12','module13').replace('QA12','QA13').replace('qa12','qa13').replace('55443','55444').replace('8829','8831').replace('8830','8832')
 if name=='qa_settings.py':s=s.replace("MIDDLEWARE = ['qa_adapters.Adapters'] + MIDDLEWARE",'')
 if name=='run.py':s=s.replace("settings.LOCAL_ANALYTICS_STORAGE_ENABLED=False  # Match source defaults; decorated cases explicitly enable collection.","settings.LOCAL_ANALYTICS_STORAGE_ENABLED=False\n    settings.LOCALIZED_PLACE_URLS_ENABLED=False  # Existing source TESTING default; native profile true explicitly.")
 (P/name).write_text(s,encoding='utf-8')
(S/'playwright.json').write_text(json.dumps({'browser':{'browserName':'chromium','launchOptions':{'executablePath':'C:/Users/Ramin/AppData/Local/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-win64/chrome-headless-shell.exe','headless':True},'contextOptions':{'viewport':{'width':1440,'height':950}}},'outputDir':str(S/'playwright')}))
docs=['AGENTS.md','.agents/README.md','.agents/registry.json','.agents/agents/kidsmap-orchestrator/agent.md','.agents/agents/django-reviewer/agent.md','.agents/agents/integration-reviewer/agent.md','.agents/agents/browser-qa/agent.md','.agents/knowledge/architecture.md','.agents/knowledge/source-of-truth.md','.agents/rules/audit-contract.md','docs/qa/content-entry-audit-2026-10-06.md','docs/qa/module-acceptance-prompts.md']
(P/'documents.json').write_text(json.dumps({'checked':docs,'missing':[x for x in docs if not (R/x).is_file()]},indent=2))
print('Preserved foreign files',len(prior),'HTTP',len(entry['http']),'containers',len(entry['docker']))
