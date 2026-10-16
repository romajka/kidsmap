import hashlib,json,subprocess,time,urllib.request
from pathlib import Path
H=Path(__file__).resolve().parent;R=H.parents[2];S=R/'.tmp'/H.name
baseline=json.loads((H/'runtime-source-green-tests.json').read_text())
for name,digest in baseline.items():assert hashlib.sha256((R/name).read_bytes()).hexdigest()==digest,name
old=json.loads((H/'server.json').read_text());assert not Path('/proc',str(old['pid']),'cmdline').exists()
(H/'server-before-interruption.json').write_text(json.dumps(old,indent=2))
incident={'classification':'ENVIRONMENT/process discontinuity detected after model/tool session change; causal origin unverified','own_previous_pid':old['pid'],'foreign_entry_http':[{'pid':p['pid'],'alive':Path('/proc',str(p['pid']),'cmdline').exists()}for p in json.loads((H/'entry.json').read_text())['foreign_processes']],'foreign_restarts':0,'db_container_preserved':True,'completed_phases_preserved':['initial-0-ru','initial-1-ru','initial-2-az','initial-3-az'],'incomplete_phase':'initial-4-en; no final semantic result; partial PNG retained'}
(H/'process-interruption.json').write_text(json.dumps(incident,indent=2))
with(S/'server-resumed.log').open('ab')as log:p=subprocess.Popen(old['argv'],cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
old['pid']=p.pid;(H/'server.json').write_text(json.dumps(old,indent=2))
for _ in range(100):
 try:
  source=json.load(urllib.request.urlopen(old['url']+'/qa/source/',timeout=2));assert source['pid']==p.pid and source['source']==baseline and source['startup_matches_disk'];break
 except Exception:time.sleep(.2)
else:raise RuntimeError('Own HTTP not ready')
(H/'runtime-source-resumed.json').write_text(json.dumps(source,indent=2))
s=json.load(urllib.request.urlopen(old['url']+'/qa/state/4/'));(H/'interrupted-case4-state.json').write_text(json.dumps(s,indent=2));print({'pid':p.pid,'source':len(baseline),'case4':{k:[{'author':x['author_id'],'current':x['current_id'],'candidate':x['candidate_id'],'status':x['status']}for x in v['heads']]for k,v in s['reviews'].items()}})
