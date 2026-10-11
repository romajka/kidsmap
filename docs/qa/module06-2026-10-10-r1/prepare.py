"""Prepare only own fresh public QA harness; preserve entry bytes."""
from pathlib import Path
import json, hashlib, subprocess, secrets, datetime
P=Path(__file__).resolve().parent; R=P.parents[2]; OLD=R/'docs/qa/module05-2026-10-10-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
prior=[p for top in ('docs/qa','docs/superpowers/plans','.agents') for p in (R/top).rglob('*') if p.is_file() and P not in p.parents and '__pycache__' not in p.parts]+[R/'AGENTS.md',R/'docs/task33/implementation-status.md']
(P/'preservation-entry.json').write_text(json.dumps({p.relative_to(R).as_posix():sha(p) for p in prior},indent=2),encoding='utf-8')
(P/'journal-entry.txt').write_bytes((R/'docs/qa/module-acceptance-prompts.md').read_bytes())
for name in ('run.py','qa_settings.py','qa_urls.py','drive.py','check-js.cjs'):
 s=(OLD/name).read_text(encoding='utf-8').replace('module05','module06').replace('55436','55437').replace('8816','8817')
 if name=='drive.py':s=s.replace("['node',str(cli)","['C:/Program Files/nodejs/node.exe',str(cli)")
 (P/name).write_text(s,encoding='utf-8')
state=R/'.tmp/module06-20261010-r1';assert not state.exists();state.mkdir(parents=True)
(state/'credential').write_text(secrets.token_hex(16))
(P/'screenshots').mkdir()
(state/'playwright.json').write_text(json.dumps({'browser':{'browserName':'chromium','launchOptions':{'executablePath':'C:/Users/Ramin/AppData/Local/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-win64/chrome-headless-shell.exe','headless':True},'contextOptions':{'viewport':{'width':1440,'height':950}}},'outputDir':str(state/'playwright')}),encoding='utf-8')
docs=['AGENTS.md','.agents/README.md','.agents/registry.json','.agents/agents/kidsmap-orchestrator/agent.md','.agents/knowledge/architecture.md','.agents/knowledge/source-of-truth.md','.agents/rules/audit-contract.md','docs/qa/content-entry-audit-2026-10-06.md','docs/qa/module-acceptance-prompts.md']
(P/'documents.json').write_text(json.dumps({'checked':docs,'missing':[x for x in docs if not (R/x).is_file()]},indent=2),encoding='utf-8')
(P/'PLAN.md').write_text('''# Module06 — fresh public acceptance, 2026-10-10 r1

AUDIT ONLY. Execution /root sequential orchestrator/frontend-reviewer/Django/browser QA responsibilities; no independent agents claimed. Application, rules, migrations and existing assertions untouched. Only own QA assets plus row06. No production, commit, push, deploy or external integration.

1. Fresh root/HEAD/branch/WORKTREE/active_run and source SHA; graph hints with direct route/service/template verification. Historical reports only checklist.
2. New local PG55437 and HTTP8817; DJANGO_TESTING=1, no inherited .env/credentials; own DB/test DB/cache/media/private-media/email/cookies/browser. Preserve every prior stand.
3. Synthetic public and unpublished places/organizations/specialists/events; age/category/price groups, confirmed venues, identical coordinates, missing/invalid point, long/fallback text, gallery, pagination. Initial setup by own fixture script; audited publication/edit/cancel/section transitions through native admin UI.
4. Native Chromium RU/AZ/EN × 360/390/768/1024/1280/1440: home/entity lists/details/search, separate/combined/reset/sort/page URL/Back/Forward/reload, same-group matching, list/count/map, private visibility, phone/gallery, keyboard/geometry/console/network. Local adapter simulation separate from actual SDK NOT RUN.
5. Fresh unchanged targeted Django suites. No assertion edits; native commands/counts/exits and baseline/environment classification.
6. Separate PUBLIC-QA defects with fix prompts; nine-section report/matrix/raw results/PNG hashes/limitations. Verify runtime/preservation/secret scan; update row06 only; handoff07.
''',encoding='utf-8')
print('Prepared own module06 harness; prior byte hashes:',len(prior))
