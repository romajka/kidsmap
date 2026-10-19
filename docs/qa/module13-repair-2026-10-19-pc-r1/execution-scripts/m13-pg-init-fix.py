from pathlib import Path
import json,sys,subprocess
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1';S=O/'stages/socketinit';S.mkdir();(S/'evidence').mkdir()
state=json.loads(subprocess.check_output(['docker','inspect','m13qa04-r1-pg','--format','{{json .State}}'],text=True));assert state['ExitCode']!=0 and not state['OOMKilled']
red={'exit':1,'failures':['Fresh owned PostgreSQL initdb failed: temporary server used custom Unix socket while initialization psql defaulted to /var/run/postgresql. Set actual PGHOST to the mounted socket.'],'errors':[],'owned_pg_id':subprocess.check_output(['docker','inspect','m13qa04-r1-pg','--format','{{.Id}}'],text=True).strip(),'exit_code':state['ExitCode'],'OOMKilled':False,'no_test_body_executed':True};(S/'evidence/red-r1.json').write_text(json.dumps(red,indent=2));(S/'IMPLEMENTATION_PLAN.md').write_text('CROSS04 infrastructure reproduction: custom Unix socket must also be PGHOST during image entrypoint database creation. Add PGHOST=/qa-socket to CI PG container. Keep failed own r1 cluster unchanged, create fresh r2 own PG/app/socket volume for retry. No app/data/schema/guard relaxation.\n')
p='.github/workflows/deploy.yml';b=(R/p).read_bytes();needle=b'-e POSTGRES_USER=qa_stage04 -e POSTGRES_DB=qa_stage04';assert b.count(needle)==1
sys.path.insert(0,str(Q));from stage_apply import apply
apply('socketinit',{p:b.replace(needle,needle+b' -e PGHOST=/qa-socket')},'stages/socketinit/evidence/red-r1.json')
t=(R/'.tmp/m13-qa04-run.py').read_text();t=t.replace("revision=sys.argv[1];", "revision=sys.argv[1];kind=sys.argv[2];assert kind in ['targeted','full'];")
t=t.replace("'-e','POSTGRES_USER=qa_stage04'","'-e','PGHOST='+str(socket),'-e','POSTGRES_USER=qa_stage04'")
t=t.replace("if revision=='r1':","if kind=='targeted':")
t=t.replace(",'--locale-manifest',str(Q/'locales-current/manifest.json')",'')
(R/'.tmp/m13-qa04-run-v2.py').write_text(t)
