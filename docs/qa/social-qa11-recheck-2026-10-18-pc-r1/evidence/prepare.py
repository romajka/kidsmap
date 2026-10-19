import json,hashlib,subprocess,difflib,socket
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/social11-pc-plan-r1';O=R/'docs/qa/social-qa11-recheck-2026-10-18-pc-r1';P=R/'docs/qa/social-qa10-fix-2026-10-18-pc-r1'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not O.exists();O.mkdir();(O/'png').mkdir()
sources=json.loads((P/'source-final.json').read_text())['sources'];assert len(sources)==1025 and all(sha(R/p)==h for p,h in sources.items())
old=json.loads((P/'source-entry.json').read_text());prior=old['prior_packages'];prior[P.name]={p.relative_to(P).as_posix():sha(p) for p in P.rglob('*') if p.is_file()}
containers=subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines()
pg=json.loads(subprocess.check_output(['docker','inspect','m09full-r1-pg']))[0];net=json.loads(subprocess.check_output(['docker','network','inspect','m09full-r1-net']))[0]
safety={'pg_running':pg['State']['Running'],'own_volume':any(x.get('Name')=='m09full-r1-pgdata' for x in pg['Mounts']),'no_pg_published_port':not any(pg['NetworkSettings']['Ports'].values()),'internal_network':net['Internal']};assert all(safety.values())
for port in [33410,33411]:
 with socket.socket() as s:s.bind(('127.0.0.1',port))
entry={'sources':sources,'shared_mo':old['shared_mo'],'prior_packages':prior,'containers':containers,'guide_sha256':sha(R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md'),'cbmignore':sha(R/'.cbmignore'),'git':json.loads((Q/'git-entry.json').read_text(encoding='utf-8-sig'))}
(O/'source-entry.json').write_text(json.dumps(entry,indent=2));(O/'safety-entry.json').write_text(json.dumps(safety,indent=2));(Q/'expected-source.json').write_text(json.dumps({'sources':sources},indent=2))
paths=['src/catalog/templates/catalog/typed_reviews.html','src/catalog/templates/pages/account_notifications.html','static/css/site.css'];diff=[];manifest={}
for p in paths:
 before=(R/p).read_text();after=before
 if 'typed_reviews.html' in p:after=after.replace('<main class="container typed-reviews">','<div class="container typed-reviews km-page-content">').replace('</main>','</div>')
 elif 'account_notifications.html' in p:after=after.replace('<main class="account-main-content" id="main-content">','<div class="account-main-content km-page-content" id="main-content">').replace('</main>','</div>')
 else:
  assert before.count('\nmain {\n')==1;after=after.replace('\nmain {\n','\nmain,\n.km-page-content {\n')
 assert after!=before
 rel=p.removeprefix('src/catalog/') if p.startswith('src/catalog/templates/') else p
 target=Q/'candidate'/rel;target.parent.mkdir(parents=True,exist_ok=True);target.write_text(after)
 saved=O/'candidate'/p;saved.parent.mkdir(parents=True,exist_ok=True);saved.write_text(after)
 manifest[p]={'before_sha256':sha(R/p),'candidate_sha256':sha(saved)}
 diff.extend(difflib.unified_diff(before.splitlines(True),after.splitlines(True),fromfile='a/'+p,tofile='b/'+p))
(O/'proposed.diff').write_text(''.join(diff));(O/'candidate-manifest.json').write_text(json.dumps({'applied':False,'files':manifest,'diff_sha256':sha(O/'proposed.diff')},indent=2))
oldq=R/'.tmp/social10-pc-fix-r1'
for n in ['qa_settings.py','runtime.py','browser_driver.py','playwright.json','proxy.py']:
 text=(oldq/n).read_text().replace('social10-pc-fix-r1','social11-pc-plan-r1').replace('m09s10-fix-r1-app','m09s11-plan-r1-app').replace('test_m09s10_fix_r1','test_m09s11_plan_r1').replace('s10-fix-r1','s11-plan-r1').replace('33400','33410')
 if n=='runtime.py':
  text=text.replace("DJANGO_SETTINGS_MODULE='qa_settings'","DJANGO_SETTINGS_MODULE=('candidate_settings' if sys.argv[1]=='candidate' else 'qa_settings')")
  text=text.replace("elif command == 'serve':","elif command in ('serve','candidate'):").replace("'0.0.0.0:8000'","('0.0.0.0:8001' if command=='candidate' else '0.0.0.0:8000')")
 if n=='proxy.py':text=text.replace("target = subprocess", "import sys\nport=int(sys.argv[1]) if len(sys.argv)>1 else 33410\nremote_port=8001 if port==33411 else 8000\ntarget = subprocess").replace('(target,8000)','(target,remote_port)').replace("('127.0.0.1',33410)","('127.0.0.1',port)")
 (Q/n).write_text(text)
(Q/'candidate_settings.py').write_text("from qa_settings import *\nfrom copy import deepcopy\nTEMPLATES=deepcopy(TEMPLATES)\nTEMPLATES[0]['DIRS']=[QA_ROOT/'candidate/templates']+list(TEMPLATES[0]['DIRS'])\nSTATICFILES_DIRS=[QA_ROOT/'candidate/static']+list(STATICFILES_DIRS)\n")
(Q/'qa_urls.py').write_text("from config.urls import urlpatterns as normal\nfrom django.urls import path\nfrom django.http import HttpResponse\nfrom django.contrib.auth import get_user_model,login\nfrom django.conf import settings\ndef fixture_login(request):\n assert settings.TESTING and settings.DATABASES['default']['NAME']=='m09full_r1'\n u=get_user_model().objects.get(pk=1,email='author09@example.invalid')\n login(request,u,backend='django.contrib.auth.backends.ModelBackend')\n return HttpResponse('SIMULATED fictional author authentication')\nurlpatterns=[path('qa/social11-login/',fixture_login)]+normal\n")
print(json.dumps({'sources':len(sources),'prior_packages':len(prior),'containers':len(containers),'safety':safety,'candidate_files':paths}))
