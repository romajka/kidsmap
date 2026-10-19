import json,re,hashlib
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module13-repair-2026-10-19-pc-r1'
names=['module01-full-2026-10-12-r6','module02-full-2026-10-13-r2','module03-full-2026-10-13-r1','module04-full-2026-10-13-r1','module05-full-2026-10-14-r2','module06-full-2026-10-14-r1','module07-accept-2026-10-15-r2','module08-accept-2026-10-16-r2','social-qa12-fix-2026-10-18-pc-r1','module10-sequential-2026-10-18-pc-r1','module11-repair-2026-10-18-pc-r1','module12-repair-2026-10-18-pc-r1']
rows=[]
for i,name in enumerate(names,1):
 p=R/'docs/qa'/name/'REPORT.md';t=p.read_text() if p.exists() else ''
 lines=[l for l in t.splitlines() if l and not l.startswith(('#','|'))]
 status=[l for l in lines if re.search(r'PASS|CLOSED|INCOMPLETE|FAIL|NOT RUN',l)][:2]
 rows.append({'module':i,'report':str(p.relative_to(R)),'exists':p.exists(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest() if p.exists() else None,'opening':lines[:2],'status_excerpt':status})
(O/'evidence/module01-12-report-index.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
for row in rows:print(json.dumps({'module':row['module'],'report':row['report'],'opening':row['opening']},ensure_ascii=False))
