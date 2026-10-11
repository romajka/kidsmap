"""Own module07 bootstrap and entry byte manifests. No app edits."""
from pathlib import Path
import json,hashlib,secrets,subprocess,datetime
P=Path(__file__).resolve().parent;R=P.parents[2];OLD=R/'docs/qa/module06-2026-10-10-r1'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
scratch=R/'.tmp/module07-20261010-r1';assert not scratch.exists();scratch.mkdir(parents=True)
prior={p.relative_to(R).as_posix():h(p) for top in ['docs/qa','docs/superpowers/plans','.agents'] for p in (R/top).rglob('*') if p.is_file() and P not in p.parents and '__pycache__' not in p.parts}
for x in ['AGENTS.md','docs/task33/implementation-status.md']:prior[x]=h(R/x)
(P/'preservation-entry.json').write_text(json.dumps(prior,indent=2),encoding='utf-8')
(P/'journal-entry.txt').write_bytes((R/'docs/qa/module-acceptance-prompts.md').read_bytes())
(scratch/'credential').write_text(secrets.token_hex(20),encoding='utf-8')
(P/'screenshots').mkdir()
(scratch/'playwright.json').write_text(json.dumps({'browser':{'browserName':'chromium','launchOptions':{'executablePath':'C:/Users/Ramin/AppData/Local/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-win64/chrome-headless-shell.exe','headless':True},'contextOptions':{'viewport':{'width':1440,'height':950}}},'outputDir':str(scratch/'playwright')}),encoding='utf-8')
for name in ['run.py','qa_settings.py','qa_urls.py','drive.py','check-js.cjs']:
 s=(OLD/name).read_text(encoding='utf-8').replace('module06','module07').replace('55437','55438').replace('8817','8820')
 if name=='qa_settings.py':s=s.replace("'django.core.mail.backends.locmem.EmailBackend'","'qa_mail.EmailBackend'")
 if name=='drive.py':s=s.replace("session in ['module07-r1','module07-proof']","session in ['module07-r1']").replace("print(clean[:6500]);print('CLI exit',result.returncode)","print(clean[:6500]);print('CLI exit',result.returncode)\nsys.exit(result.returncode)")
 (P/name).write_text(s,encoding='utf-8')
docs=['AGENTS.md','.agents/README.md','.agents/registry.json','.agents/agents/kidsmap-orchestrator/agent.md','.agents/knowledge/architecture.md','.agents/knowledge/source-of-truth.md','.agents/rules/audit-contract.md','docs/qa/content-entry-audit-2026-10-06.md','docs/qa/module-acceptance-prompts.md']
(P/'documents.json').write_text(json.dumps({'checked':docs,'missing':[x for x in docs if not (R/x).is_file()]},indent=2),encoding='utf-8')
ps="ConvertTo-Json -InputObject @(Get-NetTCPConnection -State Listen | Where-Object { $_.LocalPort -ge 8810 -and $_.LocalPort -le 8830 } | Select-Object LocalAddress,LocalPort,OwningProcess) -Compress"
q=subprocess.run(['powershell','-NoProfile','-Command',ps],capture_output=True,text=True)
d=subprocess.run(['wsl.exe','--','docker','ps','--format','{{.Names}} {{.Ports}}'],capture_output=True,text=True)
(P/'stands-entry.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'http':json.loads(q.stdout),'docker':d.stdout.splitlines(),'http_exit':q.returncode,'docker_exit':d.returncode},indent=2),encoding='utf-8')
(P/'PLAN.md').write_text('''# Модуль07 — план свежего аудита

AUDIT ONLY. Один /root последовательно выполняет orchestrator/security/frontend/browser обязанности. Ownership: только docs/qa/module07-2026-10-10-r1, свой ignored scratch/контейнер/HTTP/browser и строка07. Без application/rules/migration/assertion edits, production/commit/push/deploy. Исторические отчёты только checklist.

- [ ] Snapshot HEAD/WORKTREE/active_run/source hashes; canonical docs и graph/source auth/access map.
- [ ] Новый PG55438/HTTP8820; DJANGO_TESTING=1, отдельные DB/testDB/cache/media/private-media/email/cookies и вымышленные роли/объекты.
- [ ] Native registration/confirmation/login/logout/reset/profile; invalid/duplicate/normalized data, replay/expired tokens, CSRF/redirect/session, локальные OAuth ошибки. Email и tokens только ignored scratch/in-memory, без внешней интеграции.
- [ ] Native Place team invite/accept/reject/cancel/role/remove и открытая вкладка; Organization API contract отдельно от наличия UI. Матрица роль×действие×сущность и denial HTTP/no-side-effects.
- [ ] Account deletion native request/confirm/cancel; собственный delete fixture lifecycle по implemented flow. Private docs/consent/download/media/cache, IDs/owner/role scopes.
- [ ] Native RU/AZ/EN ×360/390/768/1024/1280/1440, empty/filled/error/loading/modal/keyboard/long text/geometry/console/network и PNG.
- [ ] Unchanged targeted tests/native exits; findings ACCESS-QA с отдельными repair prompts, nine-section report, matrix/evidence/PNG hashes/limitations. Final source/runtime/foreign preservation; строка07 и handoff08. Модуль13 последним.
''',encoding='utf-8')
print('Own prepare complete; entry hashes',len(prior))
