"""Own fresh QA harness. Does not modify any prior run or application file."""
from pathlib import Path
import json,hashlib
P=Path(__file__).resolve().parent;R=P.parents[2];OLD=R/'docs/qa/module03-2026-10-10-r1'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
prior=[p for p in (R/'docs/qa').rglob('*') if p.is_file() and P not in p.parents and '__pycache__' not in p.parts]+[R/'docs/task33/implementation-status.md']
(P/'preservation-entry.json').write_text(json.dumps({p.relative_to(R).as_posix():h(p) for p in prior},indent=2),encoding='utf-8')
(P/'journal-entry.txt').write_bytes((R/'docs/qa/module-acceptance-prompts.md').read_bytes())
for name in ('run.py','qa_settings.py','qa_urls.py','drive.py'):
    s=(OLD/name).read_text(encoding='utf-8')
    for a,b in [('module03-2026-10-10-r1','module04-2026-10-10-r1'),('module03-20261010-r1','module04-20261010-r1'),('module03-r1','module04-r1'),('module03_r1','module04_r1'),('module03','module04'),('55434','55435'),('8814','8815')]:s=s.replace(a,b)
    if name=='run.py':s=s[:s.index("elif mode == 'seed':")]
    (P/name).write_text(s,encoding='utf-8')
(P/'screenshots').mkdir(exist_ok=True)
state=R/'.tmp/module04-20261010-r1';state.mkdir(parents=True,exist_ok=True)
config={'browser':{'browserName':'chromium','launchOptions':{'executablePath':'C:/Users/Ramin/AppData/Local/ms-playwright/chromium_headless_shell-1243/chrome-headless-shell-win64/chrome-headless-shell.exe','headless':True},'contextOptions':{'viewport':{'width':1440,'height':950}}},'outputDir':str(state/'playwright')}
(state/'playwright.json').write_text(json.dumps(config),encoding='utf-8')
(P/'PLAN.md').write_text('''# Module04 audit plan — fresh2026-10-10r1

AUDIT ONLY. One sequential executor /root using canonical orchestrator/Django/browser directions; no independent agents claimed. Only own QA/report/fixtures and journal row04. No application/rules/migrations/assertions/commit/push/deploy/production changes. Preserve old docs, active_run NONE and stands8811/8812/8813/8814, PG55431..55434.

1. DISCOVER: fresh HEAD/branch/WORKTREE/active_run hashes, graph-first relevant Event symbols/coverage, source actual3-step form/organizer/venue/date/photo/moderation/calendar contracts.
2. Fresh DJANGO_TESTING=1 PG55435,HTTP8815, LocMem cache/email, separate media/private-media/cookies, synthetic actors/org/person/venues. Block external transport; record SIMULATED absence maps/fonts.
3. Real nativeUI create→partial3-stepdraft→reload/newlogin→invalid/correct→send→reject/reason/correct→approve/public→published edits contract. Org and specialist organizer, exclusive organizer, foreign IDs/unavailable/revoked authority, format keyboard/date/price/contact/photo/gallery.
4. Manage cancellation/reschedule/reason/date/public/list/search/oldlink; real two tabs/duplicate-submit/offline/input preservation, organizer/venue concurrent edits and denied rights.
5. RU/AZ/EN×360/390/768/1024/1280/1440 empty/filled/error/conflict/open/focus/management/public rendered screenshots, console/network/geometry and visual inspection. Source/jsdom/200 alone not acceptance. Exact NOT RUN limits.
6. Existing targeted Django Event suites; no assertion changes; classify native/harness/environment errors separately.
7. Nine-section REPORT, separate EVENT-QA findings+repairprompts, exact commands/counts/exits, evidence/PNG hashes, byte-preserved journal row04 and next05 handoff. Fresh final preservation/runtime/secret scans.
''',encoding='utf-8')
print('Own QA harness prepared; prior files preserved by entry hashes:',len(prior))
