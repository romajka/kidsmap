from pathlib import Path
import hashlib,json,tarfile,difflib,shutil,re
root=Path.cwd();report=root/'docs/qa/admin-moderation-release-2026-10-16-r2';scratch=root/'.tmp/admin-moderation-release-2026-10-16-r2'
previous=root/'docs/qa/admin-moderation-release-2026-10-16-r1'
base=json.loads((previous/'manifest.json').read_text())
assert json.loads((previous/'final.json').read_text())['production_deployed']
log=(report/'places-green.log').read_text()
assert re.search(r'Ran 81 tests in [0-9.]+s',log) and '\nOK\n' in log
changes=[];diff=''
for name in ['src/catalog/domain_admin/place.py','src/catalog/testcases/test_admin_place_moderation_fix.py']:
 before=(scratch/'before'/name).read_bytes();after=(root/name).read_bytes()
 assert hashlib.sha256(before).hexdigest()==base['files'][name]
 changes.append({'path':name,'new':False,'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(after).hexdigest()})
 diff+=''.join(difflib.unified_diff(before.decode().splitlines(True),after.decode().splitlines(True),fromfile='a/'+name,tofile='b/'+name))
(report/'application.diff').write_text(diff)
patch_hash=hashlib.sha256(diff.encode()).hexdigest()
expected=dict(base['files'])
for row in changes:expected[row['path']]=row['after_sha256']
manifest={'base_commit':base['base_commit'],'parent_patch_sha256':base['patch_sha256'],
 'patch_sha256':patch_hash,'tag':'kidsmap:admin-moderation-r2-'+patch_hash[:12],
 'base_files':base['files'],'base_MO':json.loads((previous/'candidate.json').read_text())['MO'],
 'files':expected,'changes':changes,'models_migrations_changed':False}
(report/'manifest.json').write_text(json.dumps(manifest,indent=2))
package=scratch/'release.tar.gz'
with tarfile.open(package,'w:gz')as out:
 for row in changes:out.add(root/row['path'],arcname='build-context/'+row['path'])
 out.add(report/'manifest.json',arcname='manifest.json')
receipt={'prepared':True,'files_changed':len(changes),'source_files':len(expected),
 'base_commit':base['base_commit'],'parent_patch_sha256':base['patch_sha256'],'patch_sha256':patch_hash,
 'image_tag':manifest['tag'],'package_sha256':hashlib.sha256(package.read_bytes()).hexdigest(),
 'package_bytes':package.stat().st_size,'base_context_reused_server_side':True,'production_deployed':False}
(report/'package.json').write_text(json.dumps(receipt,indent=2));print(json.dumps(receipt))
