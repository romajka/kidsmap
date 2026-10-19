import json,subprocess,sys
from pathlib import Path
Q=Path(__file__).resolve().parent;n=sys.argv[1]
if n=='roundtrip':(Q/'roundtrip.js').write_text((Q/'roundtrip-template.js').read_text(encoding='utf-8-sig').replace('__FIXTURES__',(Q/'fixture-info.json').read_text()))
r=subprocess.run(['python3',str(Q/'browser_driver.py'),n+'.js'],capture_output=True,text=True);assert r.returncode==0,r.stdout+r.stderr
d=json.loads(r.stdout.split('### Result\n',1)[1].split('\n###',1)[0]);(Q/(n+'.json')).write_text(json.dumps(d,ensure_ascii=False,indent=2));print(json.dumps({'name':n,'rows':len(d['rows']),'pass':sum(sum(r['checks'].values()) for r in d['rows']),'fail':sum(sum(not x for x in r['checks'].values()) for r in d['rows']),'guards':len(d.get('guards',[])),'guard_fail':sum(not r['passed'] for r in d.get('guards',[])),'console':len(d['consoleErrors']),'pageerrors':len(d['pageerrors']),'http':len(d['http']),'local_failed':len(d['failed']),'external_blocked':len(d['blocked'])}));assert all(all(r['checks'].values()) for r in d['rows']) and all(r['passed'] for r in d.get('guards',[]))
