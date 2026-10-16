import json,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];scripts=['auth-recovery-az.js','auth-recovery-en.js','post-profile-images.js','post-team-long.js','post-contract-suspended.js','post-media-positive.js'];done=[]
for script in scripts:
 p=subprocess.run([str(R/'.venv/bin/python'),str(H/'browser_run.py'),script],cwd=R)
 f=H/(script+'.result.json');d=json.loads(f.read_text())if f.exists()else{};rows=d.get('rows',[]);entry={'script':script,'exit':p.returncode,'rows':len(rows),'nonpass':sum(r.get('status')!='PASS'for r in rows),'error':d.get('error')};done.append(entry);(H/'recovery-queue-status.json').write_text(json.dumps(done,indent=2));print(json.dumps(entry),flush=True)
 if p.returncode or not rows or entry['nonpass']or d.get('error'):sys.exit(1)
for script in ['auth-console-ru.js','auth-recovery-az.js','auth-recovery-en.js']:
 d=json.loads((H/(script+'.result.json')).read_text());assert len(d['rows'])==24 and all(r['status']=='PASS'for r in d['rows'])
 assert not [r for r in d.get('diagnostics',[])if r['kind']=='pageerror'or(r['kind']=='requestfailed'and r['local'])]
(H/'auth-recovery-ready.json').write_text(json.dumps({'status':'PASS','scenarios':['registration/OTP/profile/logout/reset/new-password/token replay/duplicate email/safe next'],'family':{'ru':'qa07r3','az':'qa07r2','en':'qa07r2'},'rows':72,'console_capture':True},indent=2))
