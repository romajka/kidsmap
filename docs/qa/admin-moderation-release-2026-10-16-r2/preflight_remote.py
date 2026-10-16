"""Read-only server checks. MANIFEST is injected by the local runner."""
from pathlib import Path
import hashlib, json, subprocess, shutil, urllib.request

manifest = MANIFEST
root = Path('/opt/kidsmap')
def inspect(name):
    return json.loads(subprocess.check_output(['docker', 'inspect', name]))[0]
active = inspect('kidsmap-web')
protected = {n: inspect(n)['Id'] for n in ['kidsmap-postgres', 'kidsmap-redis']}
program = '''
import hashlib,json
from pathlib import Path
expected=EXPECTED
bad=[n for n,h in expected.items() if not (Path('/app')/n).is_file() or hashlib.sha256((Path('/app')/n).read_bytes()).hexdigest()!=h]
new=NEW
present=[n for n in new if (Path('/app')/n).exists()]
print(json.dumps({'bad':bad,'new_present':present,'env_absent':not Path('/app/.env').exists()}))
'''.replace('EXPECTED', repr(manifest['base_files'])).replace('NEW', repr([x['path'] for x in manifest['changes'] if x['new']]))
source = json.loads(subprocess.check_output(['docker', 'exec', 'kidsmap-web', 'python', '-c', program]))
assert not source['bad'] and not source['new_present'], 'Current production source differs from the patch base'
assert source['env_absent']
compose = ['docker', 'compose', '-p', 'kidsmap', '-f', str(root/'docker-compose.yml'), '-f', str(root/'.tmp/production-release.override.yml')]
effective = json.loads(subprocess.check_output(compose+['config', '--format', 'json'], cwd=root, stderr=subprocess.PIPE))['services']['web']
env = dict(x.split('=', 1) for x in active['Config']['Env'])
assert all(env.get(k) == str(v) for k,v in effective['environment'].items())
assert {(x['source'],x['target']) for x in effective['volumes']} == {(x['Source'],x['Destination']) for x in active['Mounts']}
health = {}
for host,path in [('kidsmap.az','/healthz'),('kidsmap.az','/ru/'),('admin.kidsmap.az','/ru/admin/login/')]:
    req = urllib.request.Request('http://127.0.0.1:8000'+path, headers={'Host':host,'X-Forwarded-Proto':'https'})
    health[host+path] = urllib.request.urlopen(req, timeout=15).status
assert all(x == 200 for x in health.values())
print(json.dumps({'preflight':True,'image_id':active['Image'],'image_tag':active['Config']['Image'],
 'web_id':active['Id'],'base_source_files_match':len(manifest['base_files']),
 'new_paths_absent':True,'env_values_match_compose':True,'env_file_in_image':False,
 'mounts_match_compose':True,'protected_container_ids':protected,
 'checkout_HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
 'checkout_clean':not subprocess.check_output(['git','status','--porcelain'],cwd=root,text=True).strip(),
 'override_sha256':hashlib.sha256((root/'.tmp/production-release.override.yml').read_bytes()).hexdigest(),
 'disk_free_bytes':shutil.disk_usage(root).free,'health':health},indent=2))
