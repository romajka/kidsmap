import subprocess,json
from pathlib import Path
Q=Path(__file__).resolve().parent;R=Q.parents[1];S='/mnt/c/kidsmap/.tmp/kidsmap-task33-qa04-socket-full-r1'
(Q/'socket_settings.py').write_text('''from qa_settings import *
DATABASES={'default':{'ENGINE':'django.db.backends.postgresql','NAME':'qa_stage04','USER':'module09_only','PASSWORD':'','HOST':"'''+S+'''",'PORT':'5432','TEST':{'NAME':'test_qa_stage04'}}}
MEDIA_ROOT=Path('/tmp/kidsmap-task33-qa04-full-r1/media')
PRIVATE_MEDIA_ROOT=Path('/tmp/kidsmap-task33-qa04-full-r1/private-media')
'''.replace('from qa_settings import *','from pathlib import Path\nfrom qa_settings import *'))
t=(Q/'runtime.py').read_text();t=t.replace("DJANGO_SETTINGS_MODULE='qa_settings'","DJANGO_SETTINGS_MODULE='socket_settings', TASK33_QA_ROOT='/tmp/kidsmap-task33-qa04-full-r1', TASK33_QA_SOCKET='"+S+"'")
t=t.replace("import django\ndjango.setup()","sys.path.insert(0,str(ROOT/'docs/task33/qa04'))\nPath(os.environ['TASK33_QA_ROOT']).mkdir(exist_ok=True)\nimport django\ndjango.setup()")
a=t.index('assert settings.TESTING');b=t.index('from django.core.management',a);t=t[:a]+'''from guard import validate_settings,install_network_guard,install_libpq_guard
validate_settings(settings)
install_network_guard();install_libpq_guard()
'''+t[b:];(Q/'socket_runtime.py').write_text(t)
for v in ['m09full-r1-socket','m09full-r1-socket-pgdata']:subprocess.run(['docker','volume','create',v],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['docker','run','-d','--name','m09full-r1-socket-pg','--network','m09full-r1-net','-e','POSTGRES_DB=qa_stage04','-e','POSTGRES_USER=module09_only','-e','POSTGRES_HOST_AUTH_METHOD=trust','-v','m09full-r1-socket-pgdata:/var/lib/postgresql/data','-v','m09full-r1-socket:'+S,'postgres:17-alpine','-c','unix_socket_directories='+S,'-c','listen_addresses='],check=True,stdout=subprocess.DEVNULL)
subprocess.run(['docker','run','-d','--name','m09full-r1-socket-app','--network','m09full-r1-net','--read-only','--tmpfs','/tmp','-v',str(R)+':'+str(R)+':ro','-v',str(Q)+':'+str(Q)+':rw','-v','m09full-r1-socket:'+S+':ro','-w',str(Q),'--entrypoint','python','bb90c815dc2b','-c','import time; time.sleep(86400)'],check=True,stdout=subprocess.DEVNULL)
(Q/'socket-tests.sh').write_text('''#!/bin/sh
qa=/mnt/c/kidsmap/.tmp/module09-full-pc-r1
docker exec m09full-r1-socket-app python "$qa/socket_runtime.py" test catalog.testcases.test_task33_notification_crashes catalog.testcases.test_task33_review_migration > "$qa/socket-tests.log" 2>&1
result=$?
printf '%s\\n' "$result" > "$qa/socket-tests.exit"
tail -n 12 "$qa/socket-tests.log"
exit "$result"
''')
print('Owned real Unix-socket isolation prepared; original guard and assertions unchanged')
