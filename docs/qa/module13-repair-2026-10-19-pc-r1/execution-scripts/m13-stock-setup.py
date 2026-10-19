from pathlib import Path
import subprocess,socket
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1'
for kind,port,inside,seconds in [('stock',33811,8001,0),('cooldown',33812,8002,3)]:
 with socket.socket() as s:s.bind(('127.0.0.1',port))
 (Q/('qa_'+kind+'_settings.py')).write_text("from qa_settings import *\nPLACE_REVIEW_COOLDOWN_SECONDS="+str(seconds)+"\nCACHES['default']['LOCATION']='m13-"+kind+"-normal'\nPUBLIC_BASE_URL='http://127.0.0.1:"+str(port)+"'\n")
 t=(Q/'runtime.py').read_text().replace("('qa_error_settings' if sys.argv[1]=='errors-serve' else 'qa_settings')",repr('qa_'+kind+'_settings'))
 t=t.replace("'0.0.0.0:8000'",repr('0.0.0.0:'+str(inside))).replace("(QA/'server.pid')","(QA/'"+kind+"-server.pid')")
 runtime=Q/('runtime_'+kind+'.py');runtime.write_text(t)
 subprocess.run(['docker','exec','-d','m13full-r1-app','python',str(runtime),'serve'],check=True)
 proxy=Q/('proxy_'+kind+'.py');proxy.write_text((Q/'proxy.py').read_text().replace('remote_port=8000','remote_port='+str(inside)))
 subprocess.Popen(['python3',str(proxy),str(port)],stdout=(Q/(kind+'-proxy.log')).open('w'),stderr=subprocess.STDOUT,start_new_session=True)
print('Owned secondary stock/cooldown profiles ready: ports33811/33812; own process caches, same synthetic DB, cooldown0/3; external transport disabled.')
