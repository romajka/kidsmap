import json
from pathlib import Path
Q=Path(__file__).resolve().parent;R=Q.parents[1]
old=json.loads((R/'docs/qa/social-qa11-recheck-2026-10-18-pc-r1/evidence/compare.json').read_text())['rows'];current=json.loads((Q/'matrix-author.json').read_text())['rows'];rows=[]
for r in current:
 before=next(x['baseline'] for x in old if (x['lang'],x['width'],x['case'])==(r['lang'],r['width'],r['case']));now=r['state']
 checks={'geometry_preserved':len(before['boxes'])==len(now['boxes']) and all(all(abs(a-b)<=1 for a,b in zip(x,y)) for x,y in zip(before['boxes'],now['boxes'])),'styles_preserved':before['style']==now['style'],'controls_preserved':before['controls']==now['controls'],'heading_preserved':before['h1']==now['h1']}
 rows.append({'lang':r['lang'],'width':r['width'],'case':r['case'],'checks':checks})
(Q/'geometry.json').write_text(json.dumps({'rows':rows,'reference':'immutable PLAN90 baseline before change, same fictional author/targets/viewport','tolerance_css_px':1},indent=2));failed=[r for r in rows if not all(r['checks'].values())];print(json.dumps({'pairs':len(rows),'checks':len(rows)*4,'failed':failed}));assert len(rows)==90 and not failed
