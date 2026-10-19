import json
from pathlib import Path
O=Path(__file__).resolve().parent
data=json.loads((O/'evidence/browser-layout.json').read_text());assert len(data['rows'])==6 and all(data['restore_checks'].values())
rows=[]
for r in data['rows']:
 g=r['geometry'];assert g['card_aside_overlap'] and 70<g['field']['width']<100
 rows.append({'id':r['id'],'lang':r['lang'],'width':r['width'],'geometry':g,'checks':{'visible_card_not_overlapping_actions':not g['card_aside_overlap'],'visible_card_within_main_column':g['card']['right']<=g['main']['right']},'classification':'SITE21 expected RED from actual native rectangles; original grid-main-only nonoverlap metric does not measure overflowing card content'})
(O/'evidence/desktop-layout-assessment.json').write_text(json.dumps({'derived_from':'evidence/browser-layout.json native measurements and full-page PNGs','rows':rows,'failure_observations':12,'application_or_assertion_changes':0,'scope':'Derived stronger visible-card checks, not a new browser run or change to original diagnostic'},indent=2));print('6native desktop cells:12derived visible-card layout failures, unchanged application CSS/template')
