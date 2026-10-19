import json,subprocess,time,urllib.request
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module10-sequential-2026-10-18-pc-r1';Q=R/'.tmp/m10-seq-r1'
seed=(Q/'seed.py').read_text()+'''
for lang in ['az','ru','en']:
 setattr(site,'about_text_'+lang,'SITE02 '+lang+' seed about')
 setattr(site,'empty_results_text_'+lang,'SITE02 '+lang+' seed empty')
site.save()
''';(Q/'seed.py').write_text(seed)
url=(Q/'qa_urls.py').read_text()+'''
def public_state(request):
 from catalog.models import SiteSettings
 from django.contrib.admin.models import LogEntry
 from django.urls import reverse
 from django.utils import translation
 assert settings.TESTING and settings.DATABASES['default']['NAME']=='m10seq_r1'
 with transaction.atomic():
  with connection.cursor() as cursor:
   cursor.execute('SET TRANSACTION READ ONLY');cursor.execute("SET LOCAL statement_timeout='5s'");cursor.execute("SET LOCAL lock_timeout='2s'")
  fields=['brand_name']+[prefix+'_'+lang for prefix in ['about_text','empty_results_text','contacts_text','home_search_placeholder','home_cta_text'] for lang in ['az','ru','en']]
  values=SiteSettings.objects.values(*fields).get(pk=1);logs=LogEntry.objects.count()
 urls={}
 for lang in ['az','ru','en']:
  with translation.override(lang):urls[lang]={key:reverse(name) for key,name in [('about','about'),('catalog','place_list'),('contacts','contacts'),('home','home')]}
 return JsonResponse({'values':values,'logs':logs,'urls':urls})
urlpatterns=[path('qa/module10/public-state/',public_state)]+urlpatterns
''';(Q/'qa_urls.py').write_text(url)
assert not (Q/'own-processes.json').exists();setup=json.loads((O/'evidence/setup.json').read_text());assert subprocess.check_output(['docker','inspect','m10seq-r1-app','--format','{{.Id}}'],text=True).strip()==setup['container_id']
proc=subprocess.run(['docker','exec','m10seq-r1-app','python',str(Q/'seed.py')],capture_output=True,text=True);(Q/'seed.log').write_text(proc.stdout+proc.stderr);assert proc.returncode==0,proc.stderr[-600:]
proxy=subprocess.Popen(['python3',str(Q/'proxy.py')],stdout=(Q/'proxy.log').open('w'),stderr=subprocess.STDOUT,start_new_session=True)
server=subprocess.Popen(['docker','exec','m10seq-r1-app','python',str(Q/'runtime.py'),'serve'],stdout=(Q/'server.log').open('w'),stderr=subprocess.STDOUT,start_new_session=True)
(Q/'own-processes.json').write_text(json.dumps({'app':'m10seq-r1-app','container_id':setup['container_id'],'proxy_pid':proxy.pid,'server_exec_pid':server.pid,'port':33640},indent=2))
deadline=time.monotonic()+55
while time.monotonic()<deadline:
 try:
  with urllib.request.urlopen('http://127.0.0.1:33640/qa/module10/public-state/',timeout=2) as response:state=json.load(response)
  break
 except Exception:time.sleep(.5)
else:raise AssertionError('Own readiness failed; do not blindly restart')
(O/'fixture-entry.json').write_text(json.dumps(state,indent=2));(O/'start_server.py').write_bytes(Path(__file__).read_bytes());print('Own33640 source-loaded public/editor QA server ready.')
