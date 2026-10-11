"""Read explicitly handed-off parent artifacts; never executes app transitions."""
import hashlib,json
from datetime import datetime,timezone
from pathlib import Path
ROOT=Path('C:/kidsmap');OUT=Path(__file__).resolve().parent;P=OUT.parent
snapshot=json.loads((P/'snapshot.json').read_text(encoding='utf-8'))
selected={
 'acl-native.result.txt':{'historical_ids':{'SITE-QA-01','ANALYTICS-QA-01'},'new_ids':set()},
 'cross-effects.result.txt':{'historical_ids':{'ORG-QA-02','ACCESS-QA-03'},'new_ids':set()},
 'event-cross.result.txt':{'historical_ids':set(),'new_ids':{'CROSS-QA-01'}}}
rows=[];files=[]
for name,allowed in selected.items():
    path=P/name;data=json.loads(path.read_text(encoding='utf-8'));files.append({'evidence':'docs/qa/'+P.name+'/'+name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    for index,r in enumerate(data['rows'],1):
        ids=set(r.get('historical_ids',[]))|({r['historical_id']} if r.get('historical_id') else set())
        new={r['new_id']} if r.get('new_id') else set()
        if not (ids&allowed['historical_ids'] or new&allowed['new_ids'] or r.get('scenario')=='network-employee-native-revocation'):continue
        record={k:r.get(k,'UNRECORDED') for k in ['scenario','status','role','lang','width','url','shot','http','reason']}
        record.update({'historical_ids':sorted(ids&allowed['historical_ids']),'new_ids':sorted(new&allowed['new_ids']),
            'evidence':'docs/qa/'+P.name+'/'+name,'evidence_row':index,
            'snapshot':'docs/qa/'+P.name+'/snapshot.json','snapshot_head':snapshot['head'],'snapshot_digest':snapshot['source_digest'],
            'execution_attribution':'Parent /root lead native module13; imported/read by /root/cross_reconcile, not independently executed here.'})
        if r.get('beforeLinks') is not None:record['observed_counts']={k:r[k] for k in ['beforeLinks','afterLinks','generalListLinks'] if k in r}
        if record['shot']!='UNRECORDED' and record['shot']:record['screenshot']='docs/qa/'+P.name+'/'+record['shot']
        rows.append(record)
payload={'utc':datetime.now(timezone.utc).isoformat(),'scope':'Only parent-explicit fresh handoff: SITE-QA-01/ANALYTICS-QA-01/ORG-QA-02/ACCESS-QA-03 and new parent CROSS-QA-01. No other old status imported.',
    'attribution':'Fresh native browser proof produced by /root lead; this role inspected artifact rows only.',
    'files':files,'rows':rows,'new_finding_severity':{'CROSS-QA-01':'P2 (parent assigned)'},
    'snapshot':{'head':snapshot['head'],'branch':snapshot['branch'],'source_digest':snapshot['source_digest'],'active_run':snapshot['active_run']}}
(OUT/'fresh-root-evidence.json').write_text(json.dumps(payload,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'imported_rows':len(rows),'historical_fail_ids':sorted(set(fid for r in rows if r['status']=='FAIL' for fid in r['historical_ids'])),'parent_new_ids':['CROSS-QA-01'],'attribution':'parent native proof'},ensure_ascii=False))
