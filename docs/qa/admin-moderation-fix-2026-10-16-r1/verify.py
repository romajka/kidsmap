"""Read-only final gate: evidence, current source, patch and artifact privacy."""
import hashlib,json,re,subprocess
from pathlib import Path
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parents[2];checks=[]
(H/'verification.json').write_text(json.dumps({'verified':False,'status':'verification running'}))
def read(name):return json.loads((H/name).read_text())
def check(name,ok):
 checks.append({'name':name,'pass':bool(ok)})
 if not ok:raise AssertionError(name)
flow=read('flow.json');matrix=read('matrix.json')
check('54 complete native flow checks',flow['complete']and len(flow['rows'])==54 and all(x['status']=='PASS'for x in flow['rows']))
check('flow only expected conflict response',flow['diagnostics']==[{'type':'http','status':409,'path':'/admin/catalog/placereview/4/approve/'}])
check('45 language/responsive states',matrix['complete']and len(matrix['rows'])==45 and len({(x['lang'],x['width'],x['kind'])for x in matrix['rows']})==45 and all(x['status']=='PASS'and x['lang']==x['language']and x['same_admin_host']for x in matrix['rows']))
check('matrix no page or first-party HTTP failures',not matrix['errors']and not matrix['http']and matrix['cleanup_approved'])
check('final public place and consistent reviews',len(matrix['final_state']['public_places'])==2 and all(x['candidate']is None and x['current']is not None and x['public']for x in matrix['final_state']['reviews']))
counts={}
for name,expected in [('reviews-green.log',79),('places-green.log',80),('security-green.log',5)]:
 text=(H/name).read_text();m=re.search(r'Ran (\d+) tests? in ([\d.]+)s',text)
 check(name+' complete OK',m and int(m[1])==expected and re.search(r'^OK$',text,re.M)and not re.search(r'^(FAILED|FAIL:|ERROR:)',text,re.M));counts[name]={'tests':int(m[1]),'seconds':float(m[2])}
manifest=read('final-source-manifest.json');check('runtime source equals current WORKTREE',all((R/p).is_file()and hashlib.sha256((R/p).read_bytes()).hexdigest()==digest for p,digest in manifest.items()))
for name in ('places-source-sha256.json','security-source-hashes.json'):
 check(name+' matches current source',all(hashlib.sha256((R/p).read_bytes()).hexdigest()==v for p,v in read(name).items()))
baseline=read('baseline.json');check('HEAD preserved',subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==baseline['head'])
changes=read('changed-files.json');check('26 files with five additions',len(changes)==26 and sum(x['new']for x in changes)==5)
check('all patch files match final hashes',all(hashlib.sha256((R/x['path']).read_bytes()).hexdigest()==x['after_sha256']for x in changes))
subprocess.run(['git','apply','--check','--reverse',str(H/'application.diff')],cwd=R,check=True,capture_output=True)
check('incremental patch reverse dry-check',True)
for x in changes:
 p=R/x['path']
 if p.suffix=='.py':compile(p.read_text(),str(p),'exec')
for p in H.glob('*.js'):subprocess.run(['node','--check',str(p)],check=True,capture_output=True)
old=R/'.tmp/admin-moderation-audit-2026-10-16-r1/source'
for prefix in ('src/catalog/models','src/catalog/migrations'):
 paths=[p for p in (R/prefix).rglob('*.py')if '__pycache__'not in p.parts]
 check(prefix+' unchanged',all((old/p.relative_to(R)).is_file()and p.read_bytes()==(old/p.relative_to(R)).read_bytes()for p in paths))
mo=[]
for lang in ('az','ru','en'):
 p=R/'locale'/lang/'LC_MESSAGES/django.mo';mo.append(p.read_bytes()==(old/p.relative_to(R)).read_bytes())
check('shared MO assets preserved',all(mo))
subprocess.run([str(R/'.venv/bin/python'),str(R/'scripts/build_isolated_locales.py'),'verify','--manifest',str(R/'.tmp'/H.name/'locales-final/manifest.json'),'--source-locale',str(R/'.tmp'/H.name/'source/locale')],check=True,capture_output=True)
check('isolated final catalogues verified',True)
png=[]
for p in sorted((R/'output/playwright'/H.name).glob('*.png')):
 with Image.open(p)as im:im.verify()
 with Image.open(p)as im:dimensions=list(im.size)
 png.append({'path':str(p.relative_to(R)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'dimensions':dimensions})
check('25 valid screenshots',len(png)==25)
(H/'png-manifest.json').write_text(json.dumps(png,indent=2))
secret_values=[]
for profile,filename in [(H.name,'secrets.json'),('admin-moderation-audit-2026-10-16-r1','secrets.json'),('admin-review-fix-20261016','secrets.json')]:
 p=R/'.tmp'/profile/filename
 if p.exists():secret_values.extend(v for v in json.loads(p.read_text()).values()if isinstance(v,str)and len(v)>15)
check('generated local credentials absent from report artifacts',all(v not in p.read_text(errors='replace')for p in H.iterdir()if p.is_file()for v in secret_values))
for name in ('REPORT.md','REVIEWS.md','PLACES.md','SECURITY.md'):
 for link in re.findall(r'\]\(([^)]+)\)',(H/name).read_text()):
  if '://'in link or link.startswith('#'):continue
  link=re.sub(r':\d+$','',link);p=Path(link)if link.startswith('/')else H/link
  check('report link '+name+' '+link,p.exists())
result={'verified':True,'local_findings_closed':['AM-01','AM-02','AM-03','AM-04','AM-05','AM-06','AM-07','AM-08'],'django_tests':sum(x['tests']for x in counts.values()),'test_runs':counts,'native_flow_checks':54,'rendered_states':45,'png':len(png),'application_files':len(changes),'production_deployed':False,'models_migrations_changed':False,'checks':checks}
(H/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in result.items()if k not in ('checks','test_runs')},ensure_ascii=False))
