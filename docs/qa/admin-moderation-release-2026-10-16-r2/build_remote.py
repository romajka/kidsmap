from pathlib import Path
import os, json, hashlib, subprocess, tarfile, time, shutil
manifest = MANIFEST
preflight = PREFLIGHT
os.umask(0o077)
stage=Path('/opt/kidsmap-releases/admin-moderation-20261016-r2')
package=stage.with_suffix('.tar.gz')
assert hashlib.sha256(package.read_bytes()).hexdigest() == 'PACKAGESHA'
active=json.loads(subprocess.check_output(['docker','inspect','kidsmap-web']))[0]
assert active['Id']==preflight['web_id'] and active['Image']==preflight['image_id']
stage.mkdir(exist_ok=False)
shutil.copytree('/opt/kidsmap-releases/admin-moderation-20261016-r1/build-context',stage/'build-context')
with tarfile.open(package) as bundle:
    assert all(not n.name.startswith('/') and '..' not in Path(n.name).parts for n in bundle.getmembers())
    bundle.extractall(stage,filter='data')
assert json.loads((stage/'manifest.json').read_text()) == manifest
context=stage/'build-context'
assert all(hashlib.sha256((context/n).read_bytes()).hexdigest()==h for n,h in manifest['files'].items())
assert not(context/'.env').exists() and not list(context.glob('locale/*/LC_MESSAGES/*.mo'))
started=time.monotonic()
with(stage/'build.log').open('wb') as out:
    p=subprocess.run(['docker','build','--label','org.opencontainers.image.revision='+manifest['base_commit'],
                     '--label','az.kidsmap.incremental-patch='+manifest['patch_sha256'],
                     '-t',manifest['tag'],str(context)],stdout=out,stderr=subprocess.STDOUT)
assert p.returncode==0, 'Image build failed; restricted server log retained'
image=json.loads(subprocess.check_output(['docker','image','inspect',manifest['tag']]))[0]
result={'built':True,'image_id':image['Id'],'tag':manifest['tag'],'seconds':round(time.monotonic()-started,3),
 'patch_sha256':manifest['patch_sha256'],'base_commit':manifest['base_commit'],'source_files':len(manifest['files']),
 'env_in_context':False,'translation_binaries_forced_fresh':True,'running_web_unchanged':True}
(stage/'build.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
