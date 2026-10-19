import json
from pathlib import Path
O=Path(__file__).resolve().parent;data=json.loads((O/'evidence/browser-root-prototype.json').read_text());assert len(data['rows'])==36 and not data['pageerrors']
rows=[];totals={phase:{'pass':0,'fail':0} for phase in ['baseline','prototype']};hidden=0
for r in data['rows']:
 assert all(r['checks'].values())
 phases={}
 for phase in ['baseline','prototype']:
  g=r[phase];fields=[f for f in g['fields'] if f['width']>0 and f['height']>0];hidden+=len(g['fields'])-len(fields)
  checks={k:v for k,v in g['checks'].items() if k!='fields_inside_cards'}
  checks['visible_fields_within_main']=all(f['left']>=g['main']['left']-.75 and f['right']<=g['main']['right']+.75 for f in fields)
  phases[phase]={'checks':checks,'visible_field_widths':[f['width'] for f in fields]}
  for value in checks.values():totals[phase]['pass' if value else 'fail']+=1
 rows.append({'id':r['id'],'role':r['role'],'lang':r['lang'],'width':r['width'],**phases,'controls':r['checks']})
assert totals=={'baseline':{'pass':120,'fail':60},'prototype':{'pass':180,'fail':0}},totals
result={'rows':rows,'totals':totals,'controls':216,'controls_all_pass':True,'derived_from':'evidence/browser-root-prototype.json original native measurements, no new browser run','hidden_zero_rects_ignored':hidden,'retained_initial_metric':'fields_inside_cards wrongly included hidden collapsed service field with0x0rect,36false values in each phase. Original data/checks retained; corrected metric measures visible fields from same captured rectangles. No application/DOM/test assertion edited for this assessment.','prototype_scope':'in-memory col-12 injection/removal only; not source GREEN; source remains RED','application_changes':0}
(O/'evidence/prototype-assessment.json').write_text(json.dumps(result,indent=2));print(json.dumps({k:v for k,v in result.items() if k!='rows'},indent=2))
