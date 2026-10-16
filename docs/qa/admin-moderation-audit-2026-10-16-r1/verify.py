"""Verify bounded audit evidence, artifact links, images and preservation."""
import hashlib,json,re,subprocess
from pathlib import Path
from PIL import Image
H=Path(__file__).resolve().parent;R=H.parents[2];checks=[]
def check(name,value):
 checks.append({'name':name,'pass':bool(value)})
 if not value:raise AssertionError(name)
def read(name):return json.loads((H/name).read_text())
b=read('browser.json');p=read('probe.json');c=read('controls.json');pub=read('publish.json');rb=read('readback.json')
check('45 local rendered GET cases, three languages and five widths',len(b['rows'])==45 and len({(x['lang'],x['width'],x['kind'])for x in b['rows']})==45 and all(x['status']==200 for x in b['rows']))
check('bounded GET matrix: no page errors, first-party HTTP failure or document overflow',not b['errors'] and not b['failures'] and all(x['scrollWidth']<=x['width']+1 for x in b['rows']))
check('AM03: four candidates but only two queue rows',len(p['pending_candidates'])==4 and all(x['rows']==2 for x in b['rows']if x['kind']=='queue'))
bulk=p['after_browser_bulk'];check('AM04: bulk published an undecided candidate',bulk['public']and bulk['current']is None and bulk['candidate_status']=='pending')
hide=p['single_hide'];check('AM05: hidden review still public, candidate replaced',hide['after']['public']and hide['before']['candidate']!=hide['after']['candidate']and c['hiddenTextStillPublished'])
check('typed approval and repeat-decision control',p['typed_approval_control']['after']['candidate']is None and p['typed_approval_control']['after']['current']==p['typed_approval_control']['before']['candidate']and p['repeat_decision_control']==409)
check('AM08: successful publication followed by false object-not-found message',pub['postStatus']==302 and pub['publicStatus']==200 and any('не существует' in s for s in pub['errors'])and rb['place']=={'status':'published','active':True,'public':True})
check('readback was isolated and read-only',rb['transaction_read_only']and rb['synthetic_only'])
manifest=read('source-manifest.json');changed=[path for path,digest in manifest.items()if not(R/path).is_file()or hashlib.sha256((R/path).read_bytes()).hexdigest()!=digest]
check('2837 application/source assets preserved',len(manifest)==2837 and not changed)
check('HEAD unchanged',subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()==read('environment.json')['head'])
png=read('png-manifest.json')
for row in png:
 path=R/row['path'];check('PNG '+path.name,hashlib.sha256(path.read_bytes()).hexdigest()==row['sha256'])
 with Image.open(path)as im:im.verify()
for name in ('REPORT.md','BUG_REPORT.md'):
 for link in re.findall(r'\]\(([^)]+)\)',(H/name).read_text()):
  if '://' in link or link.startswith('#'):continue
  path=Path(link)if link.startswith('/')else H/link
  check('link '+name+' '+link,path.exists())
for path in H.glob('*.py'):compile(path.read_text(),str(path),'exec')
for path in H.glob('*.js'):subprocess.run(['node','--check',str(path)],check=True,capture_output=True)
secrets=json.loads((R/'.tmp'/H.name/'secrets.json').read_text())
check('own credential values absent from published text artifacts',all(value not in path.read_text()for path in H.iterdir()if path.is_file()for value in secrets.values()))
check('eight findings documented',len(re.findall(r'^## AM-\d+', (H/'BUG_REPORT.md').read_text(),re.M))==8)
result={'evidence_verified':True,'product_verdict':'FAIL: eight open findings','checks':len(checks),'png':len(png),'rendered_states':45,'production_decision_submits':0,'application_source_changes':changed,'production_mutations_tested':False,'checks_detail':checks}
(H/'verification.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({k:v for k,v in result.items()if k!='checks_detail'},ensure_ascii=False))
