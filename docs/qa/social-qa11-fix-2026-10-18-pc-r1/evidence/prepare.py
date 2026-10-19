import json,hashlib,subprocess,socket
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/social11-pc-fix-r1';P=R/'docs/qa/social-qa11-recheck-2026-10-18-pc-r1';O=R/'docs/qa/social-qa11-fix-2026-10-18-pc-r1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert not O.exists();O.mkdir();(O/'png').mkdir()
e=json.loads((P/'source-entry.json').read_text());sources=json.loads((P/'source-final.json').read_text())['sources'];m=json.loads((P/'candidate-manifest.json').read_text())
assert len(sources)==1025 and all(sha(R/p)==h for p,h in sources.items())
g=json.loads((Q/'git-entry.json').read_text(encoding='utf-8-sig'));assert all(g[k]==e['git'][k] for k in ['head','branch','index_tree','task33_ref','staged']) and not g['staged']
assert sha(P/'proposed.diff')==m['diff_sha256'] and len(m['files'])==3 and all(sha(R/p)==v['before_sha256'] and sha(P/'candidate'/p)==v['candidate_sha256'] for p,v in m['files'].items())
prior=e['prior_packages'];prior[P.name]={p.relative_to(P).as_posix():sha(p) for p in P.rglob('*') if p.is_file()};assert len(prior)==18 and all(all(sha(O.parent/n/p)==h for p,h in fs.items()) for n,fs in prior.items())
pg=json.loads(subprocess.check_output(['docker','inspect','m09full-r1-pg']))[0];net=json.loads(subprocess.check_output(['docker','network','inspect','m09full-r1-net']))[0];safety={'owned_pg_volume':any(x.get('Name')=='m09full-r1-pgdata' for x in pg['Mounts']),'pg_running':pg['State']['Running'],'no_pg_published_port':not any(pg['NetworkSettings']['Ports'].values()),'internal_network':net['Internal']};assert all(safety.values())
for port in [33420,33421]:
 with socket.socket() as s:s.bind(('127.0.0.1',port))
entry={'sources':sources,'shared_mo':e['shared_mo'],'prior_packages':prior,'git':g,'cbmignore':sha(R/'.cbmignore'),'guide_sha256':sha(R/'docs/qa/continuation-and-repair-prompts-2026-10-11.md'),'containers':subprocess.check_output(['docker','ps','-a','--format','{{.ID}} {{.Names}} {{.State}}'],text=True).splitlines()}
(O/'source-entry.json').write_text(json.dumps(entry,indent=2));(O/'safety-entry.json').write_text(json.dumps(safety,indent=2));(Q/'expected-source.json').write_text(json.dumps({'sources':sources},indent=2))
for n in ['qa_settings.py','runtime.py','browser_driver.py','playwright.json','proxy.py']:
 t=(R/'.tmp/social11-pc-plan-r1'/n).read_text().replace('social11-pc-plan-r1','social11-pc-fix-r1').replace('test_m09s11_plan_r1','test_m09s11_fix_r1').replace('m09s11-plan-r1-app','m09s11-fix-r1-app').replace('s11-plan-r1','s11-fix-r1').replace('33410','33420').replace('33411','33421')
 if n=='runtime.py':t=t.replace("('candidate_settings' if sys.argv[1].startswith('candidate') else 'qa_settings')","'qa_settings'").replace("('serve','candidate')","('serve','green')").replace("command=='candidate'","command=='green'")
 (Q/n).write_text(t)
(Q/'qa_urls.py').write_text('''from config.urls import urlpatterns as normal
from django.urls import path
from django.http import HttpResponse
from django.contrib.auth import get_user_model,login,logout
from django.conf import settings
def fixture_login(request,role):
 assert settings.TESTING and settings.DATABASES['default']['NAME']=='m09full_r1'
 assert role in ['guest','author','moderator','conflict_az','conflict_ru','conflict_en']
 logout(request)
 if role!='guest':
  name=('qa11_'+role if role.startswith('conflict_') else 'qa09_'+role)
  u=get_user_model().objects.get(username=name)
  assert u.email.endswith('@example.invalid')
  login(request,u,backend='django.contrib.auth.backends.ModelBackend')
 return HttpResponse('SIMULATED fictional QA role authentication')
urlpatterns=[path('qa/social11-login/<str:role>/',fixture_login)]+normal
''')
print(json.dumps({'source1025_verified':True,'prior18_verified':True,'candidate_files':list(m['files']),'safety':safety,'entry_containers':len(entry['containers'])}))
