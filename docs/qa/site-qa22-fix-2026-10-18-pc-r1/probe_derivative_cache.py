import json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site22-pc-fix-r1'
initial=json.loads((O/'evidence/browser-stale-email.json').read_text())['initial']['media']
(Q/'initial-media.json').write_text(json.dumps(initial))
code='''import sys,json,hashlib
from pathlib import Path
Q=Path('/mnt/c/kidsmap/.tmp/site22-pc-fix-r1');sys.path.insert(0,str(Q));sys.argv=['runtime.py','probe'];from runtime import *
from catalog.models import SiteGalleryImage
from catalog.services.responsive_images import _directory
from PIL import Image
initial=json.loads((Q/'initial-media.json').read_text());current={p.relative_to(settings.MEDIA_ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in settings.MEDIA_ROOT.rglob('*') if p.is_file()};assert all(current.get(p)==h for p,h in initial.items())
source=SiteGalleryImage.objects.get(pk=1).image;directory=_directory(source);manifest_path=directory+'/manifest.json';manifest=json.loads((settings.MEDIA_ROOT/manifest_path).read_text());added=set(current)-set(initial);expected={manifest_path}|{v['name'] for v in manifest['variants']};assert added==expected and len(added)==5
with Image.open(source.path) as image:assert (image.width,image.height)==(manifest['width'],manifest['height'])
variants=[]
for v in manifest['variants']:
 with Image.open(settings.MEDIA_ROOT/v['name']) as image:
  assert image.format=='WEBP' and image.width==v['width'];variants.append({'name':v['name'],'width':image.width,'height':image.height})
print(json.dumps({'original_files':len(initial),'original_paths_hashes_unchanged':True,'source_image':source.name,'source_dimensions':[manifest['width'],manifest['height']],'new_cache_files':sorted(added),'variants':variants,'manifest_verified':True,'read_only_probe':True}))
'''
(Q/'derivative_probe.py').write_text(code);cmd=['docker','exec','m10s22-fix-r1-app','python',str(Q/'derivative_probe.py')];r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode==0,r.stderr[-700:];d=json.loads(r.stdout);d.update({'command':cmd,'exit':r.returncode,'source_evidence':['src/catalog/signals.py:prepare_responsive_photos post_save SiteGalleryImage','src/catalog/services/responsive_images.py:generate_variants retains original bytes'],'classification':'Expected existing gallery post_save derivative generation in own QA media; initial inventory-equality guard incorrectly included new cache as original-file mutation','application_refinements':0});(O/'evidence/derivative-cache.json').write_text(json.dumps(d,indent=2));print(json.dumps({'original_media_unchanged':True,'new_verified_responsive_cache_files':len(d['new_cache_files']),'read_only':True},indent=2))
