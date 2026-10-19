import json,hashlib
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module10-sequential-2026-10-18-pc-r1';S=O/'stages/SITE16';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
n=json.loads((O/'evidence/browser-site16-green.json').read_text());g=json.loads((S/'evidence/green-backend.json').read_text());checks=[v for r in n['rows'] for v in r['checks'].values()]
assert len(n['rows'])==72 and all(checks) and not n['pageerrors'] and not n['local_errors'] and g['exit']==0 and len(g['test_ids'])==16
v={'status':'CLOSED LOCAL','backend_methods':16,'native_rows':72,'checks':len(checks),'PASS':len(checks),'FAIL':0,'readable_text_and_anchor_IDs_preserved':True,'full_module_acceptance':'PENDING'}
(S/'verification.json').write_text(json.dumps(v,indent=2));(S/'REPORT.md').write_text('# SITE16 CLOSED LOCAL\n\nReplaced only inner main with div in legal and listing-rules templates; base main remains unique. Fresh RED9 nested landmarks, GREEN16 backend methods and72 native route/language/width cells, '+str(len(checks))+' checks PASS. Exact original readable text hashes, headings and anchor ID lists preserved. Review-rules control unchanged. No CSS/text/schema/permission change. Full module acceptance pending.\n')
p=json.loads((O/'progress.json').read_text());p['closed'].append('16');p.update(active='23',remaining_OPEN=3);(O/'progress.json').write_text(json.dumps(p,indent=2));docs=json.loads((O/'document-current.json').read_text())
for rel,h in docs.items():
 path=R/rel;assert sha(path)==h;prefix='' if rel.startswith('docs/qa/') else '../qa/';path.write_bytes(path.read_bytes()+('\n\n## Module10 SITE16 CLOSED LOCAL — 2026-10-18 pc-r1\n\n[Report]('+prefix+O.name+'/stages/SITE16/REPORT.md): legal pages now have one main, headings/readable text/anchor IDs preserved;16backend methods and72native cells/'+str(len(checks))+'checks PASS. Remaining3P3, continueSITE23 under ongoing authorization; full acceptancePENDING.\n').encode());docs[rel]=sha(path)
(O/'document-current.json').write_text(json.dumps(docs,indent=2));print(v)
