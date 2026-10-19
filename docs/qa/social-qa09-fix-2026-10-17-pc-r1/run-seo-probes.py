import json,subprocess
from pathlib import Path
Q=Path(__file__).resolve().parent
r=subprocess.run(['python3',str(Q/'browser_driver.py'),'seo-probes.js'],capture_output=True,text=True);raw=r.stdout+r.stderr;assert r.returncode==0,raw
assert '### Result\n' in raw,raw
d=json.loads(raw.split('### Result\n',1)[1].split('\n###',1)[0]);(Q/'seo-probes.json').write_text(json.dumps(d,ensure_ascii=False,indent=2))
assert all(all(r['controls'].values()) and all(r['source'].values()) for r in d['rows']),d
assert not d['pageerrors'] and not d['requestfailed'] and not d['consoleErrors'],d
print('rows',len(d['rows']),'controlsPASS',sum(sum(r['controls'].values()) for r in d['rows']),'sourceFAIL',sum(sum(not v for v in r['source'].values()) for r in d['rows']))
