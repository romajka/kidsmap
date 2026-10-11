"""Prepare this run's QA harness only; preserve earlier runs."""
import hashlib,json
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2];OLD=R/'docs/qa/module01-2026-10-09-r2'
def h(p):return hashlib.sha256(p.read_bytes()).hexdigest()
files=[p for p in (R/'docs/qa').rglob('*') if p.is_file() and P not in p.parents and '__pycache__' not in p.parts]
files += [R/'docs/task33/implementation-status.md']
(P/'preservation-entry.json').write_text(json.dumps({p.relative_to(R).as_posix():h(p) for p in files},indent=2),encoding='utf-8')
(P/'journal-entry.txt').write_bytes((R/'docs/qa/module-acceptance-prompts.md').read_bytes())
for name in ('qa_settings.py','qa_urls.py','run.py','drive.py'):
 s=(OLD/name).read_text(encoding='utf-8')
 for a,b in [('module01-2026-10-09-r2','module03-2026-10-10-r1'),('module01-20261009-r2','module03-20261010-r1'),('module01-r2','module03-r1'),('module01_r2','module03_r1'),('module01-r2','module03-r1'),('module01','module03'),('55433','55434'),('8813','8814')]:s=s.replace(a,b)
 if name=='drive.py':
  start=s.index("if sys.argv[1]=='branch-lifecycle.js':");end=s.index("(here/(Path(sys.argv[1]).stem+'.effective.js')).write_text")
  s=s[:start]+s[end:]
 (P/name).write_text(s,encoding='utf-8')
(P/'screenshots').mkdir(exist_ok=True)
(P/'PLAN.md').write_text('''# Module03 fresh audit plan

AUDIT ONLY; one sequential lead /root (canonical .agents/agents/kidsmap-orchestrator/agent.md), Django/security/browser directions. No app/rules/migrations/assertion edits, commit/push/deploy/production. Prior stands8811/8812/8813 preserved; own8814 and PostgreSQL55434.

- [ ] Snapshot and preserve prior files/journal/active_run; verify source hashes, ignored compiled locale assets separately.
- [ ] Fresh DJANGO_TESTING=1 database/cache/mail/media/private-media/cookies, synthetic role identities, file/image fixtures, blocked external transport.
- [ ] Graph-first specialist discovery, then actual services/controller/admin/forms/routes/media ACL. Record coverage gaps; do not save graph cache.
- [ ] Real UI proposal draft every available step, reload/login, validation, directions search/dedupe/removal, multiple practice locations, send/review/rejection/claim/person edit/publication.
- [ ] Cooperation invitation accept/reject/cancel/repeat and permissions via UI; author/person/network role separation.
- [ ] Identity/certificate upload/consent/review/download access matrix (guest/author/person/network staff/owner/moderator/admin), foreign IDs and revocation.
- [ ] Real two-tab/double-send/file/offline errors and retained input.
- [ ] RU/AZ/EN × 360/390/768/1024/1280/1440 rendered empty/filled/error/open/modal/state/public screenshots, geometry, keyboard and network.
- [ ] Existing targeted Django suites; record native exits, separate harness/environment failures and NOT RUN limits.
- [ ] Nine-section REPORT, per-finding repair prompts SPEC-QA-xx, evidence manifest, journal row03 only and next-chat. Final source/prior preservation verification.
''',encoding='utf-8')
print('QA-only harness prepared; prior files hashed',len(files))
