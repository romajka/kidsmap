import json
from pathlib import Path
O=Path(__file__).resolve().parent
for name in ['browser-sentinels.js','browser-sentinels-red.js']:
 p=O/name;before=p.read_bytes();(O/('initial-'+name)).write_bytes(before)
 p.write_text(before.decode().replace("model+'/add/'","model+'/add/'+(model==='place'?'?type=permanent':'')"))
(O/'evidence/sentinel-harness-initial.json').write_text(json.dumps({'classification':'QA-harness route assumption','initial_exit':1,'error':'Place add without type redirects to add-choice, which has no #content-main','source':'src/catalog/domain_admin/place.py:add_view checks request.GET type','diagnostic':'browser-sentinel-diagnostic.json','correction':'Use actual permanent Place add ?type=permanent in identical RED/GREEN sentinel; no application/assertion change; original code/CLI error retained'},indent=2))
print('Sentinel route corrected to real permanent Place editor; initial evidence retained.')
