"""Fresh bounded local provenance; no build/up/push/deploy or secret inspection."""
import hashlib
import json
from pathlib import Path
import subprocess
import uuid

root=Path('/mnt/c/kidsmap/docs/task33');out=Path('/root/task33-evidence/final-audit-image-20261004')
out.mkdir(parents=True,exist_ok=False);home=out/'clean-home';home.mkdir()
env={'PATH':'/usr/bin:/bin','HOME':str(home)}
candidate=json.loads((root/'reports/28-artifact.json').read_text())
built=json.loads((root/'reports/28-release-image.json').read_text())
assert candidate['identity']==built['artifact_identity']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
archive=Path(candidate['archive']);manifest_path=archive.with_name('manifest.json')
assert sha(archive)==candidate['archive_sha256'] and sha(manifest_path)==candidate['manifest_sha256']
expected={e['path']:e['sha256'] for e in json.loads(manifest_path.read_text())['files']}
context=Path('/root/km28-image-context3')
def inventory(path):
    symlinks=[str(p.relative_to(path)) for p in path.rglob('*') if p.is_symlink()]
    actual={p.relative_to(path).as_posix():sha(p) for p in path.rglob('*') if p.is_file() and not p.is_symlink()}
    assert not symlinks and actual==expected
    return len(actual)
context_count=inventory(context)
def docker(*args):return subprocess.check_output(['docker',*args],env=env,text=True).strip()
inspected=json.loads(docker('image','inspect',built['image_id']))[0]
assert inspected['Id']==built['image_id']
nonce=uuid.uuid4().hex;name='kidsmap-final-audit-image-'+nonce[:12]
docker('create','--name',name,'--label','kidsmap.final-audit.owner='+nonce,'--network','none',
       '--entrypoint','/usr/local/bin/python',built['image_id'],'-c',
       'import json,platform,importlib.metadata as m;print(json.dumps(dict(python=platform.python_version(),dependencies=sorted((d.metadata["Name"],d.version) for d in m.distributions()))))')
try:
    info=json.loads(docker('inspect',name))[0]
    assert info['Config']['Labels']['kidsmap.final-audit.owner']==nonce
    assert info['HostConfig']['NetworkMode']=='none' and not info['HostConfig']['PortBindings']
    docker('cp',name+':/app',str(out/'app'))
    image_count=inventory(out/'app')
    interpreter=json.loads(docker('start','-a',name))
    assert json.loads(docker('inspect',name))[0]['State']['ExitCode']==0
finally:
    assert json.loads(docker('inspect',name))[0]['Config']['Labels']['kidsmap.final-audit.owner']==nonce
    docker('rm','-f',name)
result={'status':'PASS','artifact_identity':candidate['identity'],'image_config_id':inspected['Id'],
        'archive_sha256':candidate['archive_sha256'],'manifest_sha256':candidate['manifest_sha256'],
        'actual_context_file_count':context_count,'actual_image_file_count':image_count,
        'all_files_sha_match':True,'extras_or_symlinks':False,'metadata_runtime':interpreter,
        'local_daemon_repo_digests':inspected['RepoDigests'],
        'registry_manifest_or_availability':'NOT_VERIFIED','registry_publish':'NOT_RUN',
        'process':'Python package metadata only','network':'none','ports':[],
        'application_web_started':False,'cleanup':'PASS','production':'NOT_CONTACTED'}
(root/'final-audit/security-image.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='metadata_runtime'},indent=2))
