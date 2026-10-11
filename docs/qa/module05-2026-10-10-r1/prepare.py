"""Own isolated module05 QA. Preserve all prior application and QA bytes."""
from pathlib import Path
import json, hashlib
P=Path(__file__).resolve().parent; R=P.parents[2]; OLD=R/'docs/qa/module04-2026-10-10-r1'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
prior=[p for top in ('docs/qa','docs/superpowers/plans') for p in (R/top).rglob('*') if p.is_file() and P not in p.parents and '__pycache__' not in p.parts]+[R/'docs/task33/implementation-status.md']
(P/'preservation-entry.json').write_text(json.dumps({p.relative_to(R).as_posix():h(p) for p in prior},indent=2),encoding='utf-8')
(P/'journal-entry.txt').write_bytes((R/'docs/qa/module-acceptance-prompts.md').read_bytes())
for name in ('run.py','qa_settings.py','qa_urls.py','drive.py'):
 s=(OLD/name).read_text(encoding='utf-8')
 for a,b in [('module04','module05'),('55435','55436'),('8815','8816')]:s=s.replace(a,b)
 if name=='run.py':
  s=s.replace("('src', 'static', 'config', 'locale')","('src', 'static', 'config', 'locale', 'templates')")
  s=s.replace("'active_run': 'NONE'", "'active_run': next(line.split(':',1)[1].strip() for line in (ROOT/'docs/task33/implementation-status.md').read_text(encoding='utf-8').splitlines() if line.startswith('active_run:'))")
 (P/name).write_text(s,encoding='utf-8')
(P/'screenshots').mkdir(exist_ok=True)
state=R/'.tmp/module05-20261010-r1';assert not state.exists();state.mkdir(parents=True)
(state/'playwright.json').write_text(json.dumps({'browser':{'browserName':'chromium','launchOptions':{'executablePath':'C:/Users/Ramin/AppData/Local/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-win64/chrome-headless-shell.exe','headless':True},'contextOptions':{'viewport':{'width':1440,'height':950}}},'outputDir':str(state/'playwright')}),encoding='utf-8')
(P/'PLAN.md').write_text('''# Module05 — fresh audit 2026-10-10 r1

AUDIT ONLY; /root sequential canonical orchestrator/Django/browser/database roles, no independent agents claimed. Only own QA fixtures/scripts/report and journal row05. Preserve application, prior QA/plans, active_run and all foreign stands. No production/commit/push/deploy.

1. Fresh snapshot including root templates, graph discovery then actual Program/Activity/OfferingGroup/PricingPlan/publication/schedule/permissions source. Historical audit is checklist only.
2. New loopback PostgreSQL55436, HTTP8816, DJANGO_TESTING=1, separate cache/media/private-media/email/cookies. Synthetic initial owner/employee/outsider/admin, organization and venues; audited program/activity/group/pricing transitions through native UI.
3. Program submit/review/edit/archive; place standalone/linked offerings and multiple group-specific age/pricing/conditions; hours separate from lesson schedule; validation and atomic failures; native reload/two tabs/duplicate/network/foreign IDs; branch detach and employee access; public same-group filter; supported JSON round-trip.
4. Real Chromium RU/AZ/EN×360/390/768/1024/1280/1440 relevant empty/filled/error/conflict/loading/open/keyboard states, screenshots and console/network/geometry. Block external transport and label SDK/font absence SIMULATED. Record exact NOT RUN scope.
5. Fresh targeted existing Django suites, no assertion edits; classify baseline/environment/harness failures explicitly.
6. Nine-section report, OFFER-QA separate findings and copyable repair prompts; exact commands/counts/exits, PNG hashes, preservation/runtime/secret verification; update row05 only, next06 handoff.
''',encoding='utf-8')
print('Own harness prepared; prior hashes',len(prior))
