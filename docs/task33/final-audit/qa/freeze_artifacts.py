"""Freeze final report/evidence/helper bytes after all authors finish."""
import hashlib,json,datetime
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
excluded={'artifact-manifest.json','package.json','KidsMap-28-audit-2026-10-04.zip'}
rows=[]
for p in sorted(ROOT.rglob('*')):
    if p.is_file() and p.name not in excluded and '__pycache__'not in p.parts:
        rows.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()})
data={'frozen_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Final audit deliverables only; original source preservation verified separately','files':rows,'excluded':sorted(excluded)}
(ROOT/'artifact-manifest.json').write_text(json.dumps(data,indent=2)+'\n',encoding='utf8')
print(json.dumps({'files':len(rows),'bytes':sum(x['bytes']for x in rows)}))
