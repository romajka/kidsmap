from pathlib import Path
import json,sys,subprocess
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1';S=O/'stages/socketdirs';S.mkdir();(S/'evidence').mkdir()
state=json.loads(subprocess.check_output(['docker','inspect','m13qa04-r2-pg','--format','{{json .State}}'],text=True));assert state['ExitCode']!=0 and not state['OOMKilled']
assert 'PGHOST= PGHOSTADDR=' in (Q/'pg-entrypoint.sh').read_text()
red={'exit':1,'failures':['Owned PG r2 initialization still failed; installed official entrypoint explicitly clears PGHOST/PGHOSTADDR for bootstrap psql. Both default and owned Unix socket directories are required.'],'errors':[],'own_PG_exit':state['ExitCode'],'OOMKilled':False,'source_reference':'Installed docker-entrypoint.sh docker_process_sql: PGHOST= PGHOSTADDR=; source copied only to ignored scratch.'};(S/'evidence/red-r1.json').write_text(json.dumps(red,indent=2));(S/'IMPLEMENTATION_PLAN.md').write_text('CROSS04 runtime correction: retain /var/run/postgresql for the image bootstrap and additionally listen on the actual owned /qa-socket; TCP stays disabled/network none. PGHOST-only attempt r2 proved insufficient and is retained, no tested data exists. New fresh r3 volumes and identities; do not restart prior failed clusters. CI same dual Unix-socket GUC.\n')
p='.github/workflows/deploy.yml';b=(R/p).read_bytes();needle=b'postgres -c listen_addresses= -k /qa-socket';assert b.count(needle)==1
sys.path.insert(0,str(Q));from stage_apply import apply
apply('socketdirs',{p:b.replace(needle,b'postgres -c listen_addresses= -c unix_socket_directories=/var/run/postgresql,/qa-socket')},'stages/socketdirs/evidence/red-r1.json')
t=(R/'.tmp/m13-qa04-run-v2.py').read_text();needle="'-k',str(socket)";assert t.count(needle)==1;t=t.replace(needle,"'-c','unix_socket_directories=/var/run/postgresql,'+str(socket)");(R/'.tmp/m13-qa04-run-v3.py').write_text(t)
