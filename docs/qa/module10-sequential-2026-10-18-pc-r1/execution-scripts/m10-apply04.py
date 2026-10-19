import difflib,hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module10-sequential-2026-10-18-pc-r1';Q=R/'.tmp/m10-seq-r1';S=O/'stages/SITE04';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
red=json.loads((S/'evidence/red-backend.json').read_text());assert red['exit']==1 and len(red['failures'])==9 and not red['errors'] and red['fresh_own_test_db'].endswith('r3')
(S/'IMPLEMENTATION_PLAN.md').write_text('# SITE04 plan — existing sequential immediate-fix authorization\n\nUse existing HomeController hero_search_placeholder/hero_cta_text context in home template input placeholder and visible/accessible submit label. Preserve form method/action, query cleanup policy, data hooks, icon and map behavior. Scope home.html plus new4method regression. Fresh RED has9 expected text observations and passing form/query-policy control. Fresh cumulative backend test, native branding admin saves then home3languages6widths configured/blank/safe attributes and actual typed form submission. Restore settings. Known SITE18 header remains OPEN. No schema/controller/JS/PO/production change.\n')
for name in ['candidate','entry-source']:(S/name).mkdir(exist_ok=True)
path='src/catalog/templates/pages/home.html';raw=(R/path).read_bytes();t=raw.decode()
old="{% if request.LANGUAGE_CODE == 'az' %}Məkan və ya fəaliyyət axtarın{% elif request.LANGUAGE_CODE == 'en' %}Search places or activities{% else %}Название места или занятие{% endif %}";assert t.count(old)==1;t=t.replace(old,'{{ hero_search_placeholder }}')
old="{% if request.LANGUAGE_CODE == 'az' %}Xəritədə göstər{% elif request.LANGUAGE_CODE == 'en' %}Show on map{% else %}Показать на карте{% endif %}";assert t.count(old)==2;t=t.replace(old,'{{ hero_cta_text }}')
files={path:(raw,t.encode()),'src/catalog/testcases/test_site_qa04_home_search_copy.py':(None,(Q/'test_site04_candidate.py').read_bytes())};sources=json.loads((Q/'expected-source.json').read_text())['sources'];metadata={};diff=''
for rel,(before,after) in files.items():
 assert before is not None or not (R/rel).exists()
 for name,data in [('candidate',after),('entry-source',before)]:
  if data is not None:p=S/name/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data)
 diff+=''.join(difflib.unified_diff((before or b'').decode().splitlines(True),after.decode().splitlines(True),fromfile='a/'+rel if before else '/dev/null',tofile='b/'+rel));metadata[rel]={'before':hashlib.sha256(before).hexdigest() if before else None,'after':hashlib.sha256(after).hexdigest()}
(S/'implemented.diff').write_text(diff,newline='');p=subprocess.run(['git','-C',str(R),'apply','--check',str(S/'implemented.diff')],capture_output=True,text=True);assert p.returncode==0,p.stderr
for rel,(_,after) in files.items():(R/rel).write_bytes(after);sources[rel]=sha(R/rel)
(Q/'expected-source.json').write_text(json.dumps({'sources':sources},indent=2));(S/'source-applied.json').write_text(json.dumps({'sources':sources},indent=2));(S/'applied.json').write_text(json.dumps({'files':metadata,'source_count':len(sources),'apply_check_exit':0},indent=2))
# Own synthetic normal fixture; source guard, environment and DB isolation reuse the owned runtime.
seed="""from catalog.testcases.utils import create_quality_place
from catalog.models import SiteSettings,Place
site=SiteSettings.get_solo()
assert not Place.objects.exists()
p=create_quality_place(name='Musiqi və şahmat mərkəzi',name_az='Musiqi və şahmat mərkəzi',name_ru='Центр музыки и шахмат',name_en='Music and chess centre',photo=site.logo.name)
print('One fictional published map fixture created in owned normal QA DB')
"""
(Q/'seed04.py').write_text(seed);runner="import sys,runpy\nsys.argv=['runtime.py','fixture04']\nrunpy.run_path('/mnt/c/kidsmap/.tmp/m10-seq-r1/runtime.py')\nrunpy.run_path('/mnt/c/kidsmap/.tmp/m10-seq-r1/seed04.py')\n";(Q/'run_seed04.py').write_text(runner)
p=subprocess.run(['docker','exec','m10seq-r1-app','python',str(Q/'run_seed04.py')],capture_output=True,text=True);assert p.returncode==0,p.stderr;(S/'evidence/fixture.txt').write_text(p.stdout)
print('SITE04 minimal template +4method regression applied; own visible fixture created.')
