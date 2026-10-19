import json,re,subprocess,sys
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module10-sequential-2026-10-18-pc-r1';Q=R/'.tmp/m10-seq-r1'
number,phase,*labels=sys.argv[1:];assert re.fullmatch(r'\d{2}',number) and phase in ['red','green'] and labels and all(re.fullmatch(r'[A-Za-z0-9_.]+',x) for x in labels)
S=O/'stages'/('SITE'+number);(S/'evidence').mkdir(parents=True,exist_ok=True)
name='test_m10seq_'+number+'_'+phase+'_r1';query=['docker','exec','m09full-r1-pg','psql','-U','m09full_r1','-d','postgres','-Atc',"SELECT count(*) FROM pg_database WHERE datname='"+name+"'"];assert subprocess.check_output(query,text=True).strip()=='0';subprocess.run(['docker','exec','m09full-r1-pg','createdb','-U','m09full_r1',name],check=True)
stage=json.loads((Q/'stage.json').read_text());stage['test_db']=name;(Q/'stage.json').write_text(json.dumps(stage))
cmd=['docker','exec','m10seq-r1-app','python',str(Q/'runtime.py'),'test',*labels];proc=subprocess.run(cmd,capture_output=True,text=True);raw=proc.stdout+proc.stderr;(Q/('site'+number+'-'+phase+'.log')).write_text(raw)
ids=re.findall(r'^test_\S+ \(([^)]+)\)',raw,re.M);failures=re.findall(r'^FAIL: (.*)$',raw,re.M);errors=re.findall(r'^ERROR: (.*)$',raw,re.M)
d={'command':cmd,'exit':proc.returncode,'fresh_own_test_db':name,'test_ids':ids,'failures':failures,'errors':errors,'summary':[s for s in raw.splitlines() if s.startswith(('Found ','Ran ','FAILED','OK'))]};(S/'evidence'/(phase+'-backend.json')).write_text(json.dumps(d,indent=2));print(json.dumps({k:v for k,v in d.items() if k!='test_ids'},indent=2))
assert not errors and ((proc.returncode==1 and failures) if phase=='red' else (proc.returncode==0 and not failures and len(ids)==len(set(ids))))
