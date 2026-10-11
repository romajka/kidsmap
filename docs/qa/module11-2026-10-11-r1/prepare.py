"""QA11 infrastructure only. Fresh synthetic stand; never inherit credentials."""
from pathlib import Path
import subprocess, json, hashlib, secrets, datetime
P=Path(__file__).resolve().parent;R=P.parents[2];OLD=R/'docs/qa/module10-2026-10-10-r1';S=R/'.tmp/module11-20261011-r1'
assert not S.exists(), 'Do not overwrite an existing run'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
S.mkdir(parents=True);(S/'credential').write_text(secrets.token_hex(20));(P/'screenshots').mkdir(exist_ok=True)
files=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard'],cwd=R,text=True).splitlines()
prior={x:sha(R/x) for x in files if (R/x).is_file() and P not in (R/x).parents and '__pycache__' not in x and not Path(x).name.startswith('.env')}
(P/'preservation-entry.json').write_text(json.dumps(prior,indent=2),encoding='utf-8')
(P/'journal-entry.txt').write_bytes((R/'docs/qa/module-acceptance-prompts.md').read_bytes())
ps="ConvertTo-Json -InputObject @(Get-NetTCPConnection -State Listen | Where-Object { ($_.LocalPort -ge 8810 -and $_.LocalPort -le 8835) -or ($_.LocalPort -ge 55431 -and $_.LocalPort -le 55445) } | Select-Object LocalAddress,LocalPort,OwningProcess) -Compress"
q=subprocess.run(['powershell','-NoProfile','-Command',ps],capture_output=True,text=True)
d=subprocess.run(['wsl.exe','--','docker','ps','--format','{{.Names}} {{.ID}} {{.Ports}}'],capture_output=True,text=True)
assert q.returncode==d.returncode==0
entry={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'http':json.loads(q.stdout),'docker':d.stdout.splitlines(),'http_exit':q.returncode,'docker_exit':d.returncode}
assert not any(x['LocalPort'] in [8827,8828,55442] for x in entry['http'])
(P/'stands-entry.json').write_text(json.dumps(entry,indent=2))
for name in ['run.py','qa_settings.py','drive.py','seed.py','check-js.cjs']:
 s=(OLD/name).read_text(encoding='utf-8').replace('module10','module11').replace('QA10','QA11').replace('qa10','qa11').replace('10@example.invalid','11@example.invalid').replace('55441','55442').replace('8823','8827').replace('8824','8828').replace('20261010','20261011').replace('2026-10-10','2026-10-11')
 (P/name).write_text(s,encoding='utf-8')
(S/'playwright.json').write_text(json.dumps({'browser':{'browserName':'chromium','launchOptions':{'executablePath':'C:/Users/Ramin/AppData/Local/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-win64/chrome-headless-shell.exe','headless':True},'contextOptions':{'viewport':{'width':1440,'height':950}}},'outputDir':str(S/'playwright')}))
docs=['AGENTS.md','.agents/README.md','.agents/registry.json','.agents/agents/kidsmap-orchestrator/agent.md','.agents/agents/seo-reviewer/agent.md','.agents/agents/browser-qa/agent.md','.agents/knowledge/architecture.md','.agents/knowledge/source-of-truth.md','.agents/knowledge/seo.md','.agents/rules/audit-contract.md','docs/qa/content-entry-audit-2026-10-06.md','docs/qa/module-acceptance-prompts.md']
(P/'documents.json').write_text(json.dumps({'checked':docs,'missing':[x for x in docs if not (R/x).is_file()]},indent=2))
print('Preserved foreign manifest',len(prior),'HTTP',len(entry['http']),'containers',len(entry['docker']))
