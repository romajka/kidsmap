"""Read local built image source/version identity; no Django/Gunicorn application startup."""
import hashlib
import json
from pathlib import Path
import subprocess
import uuid
import sys


def main():
    root = Path('/mnt/c/kidsmap')
    built = json.loads((root/'docs/task33/reports/28-release-image.json').read_text())
    assert built['status'] == 'BUILT'
    metadata = json.loads((root/'docs/task33/reports/28-artifact.json').read_text())
    assert metadata['identity'] == built['artifact_identity']
    manifest = json.loads((Path(metadata['archive']).parent/'manifest.json').read_text())
    revision=sys.argv[1] if len(sys.argv)>1 else 'final'
    assert revision in {'final','release3'}
    out = Path('/root/task33-evidence/stage28-local-image-verify-'+revision+'-20261003')
    out.mkdir(parents=True,exist_ok=False)
    home = out/'clean-home'; home.mkdir()
    env = {'PATH':'/usr/bin:/bin','HOME':str(home)}
    nonce = uuid.uuid4().hex; name = 'kidsmap-task33-image-review-' + nonce[:12]
    def run(*args):
        return subprocess.check_output(['docker',*args],env=env,text=True).strip()
    run('create','--name',name,'--label','kidsmap.task33.release.owner='+nonce,
        '--network','none','--entrypoint','python',built['image_id'], '-c',
        'import json,platform,importlib.metadata as m;print(json.dumps(dict(python=platform.python_version(),dependencies=sorted((d.metadata["Name"],d.version) for d in m.distributions()))))')
    try:
        info = json.loads(run('inspect',name))[0]
        assert info['Config']['Labels']['kidsmap.task33.release.owner']==nonce
        assert info['HostConfig']['NetworkMode']=='none' and not info['HostConfig']['PortBindings']
        run('cp',name+':/app',str(out/'app'))
        copied = out/'app'
        diffs=[]
        for entry in manifest['files']:
            path = copied/entry['path']
            actual=hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None
            if actual!=entry['sha256']:
                diffs.append({'path':entry['path'],'artifact_sha256':entry['sha256'],'image_sha256':actual})
        allowed = {'.dockerignore','Dockerfile'}
        assert all(d['path'] in allowed and d['image_sha256'] is None for d in diffs), 'Built image application source drift'
        for forbidden in ['.env','.git','media','db.sqlite3','scratch','backups']:
            assert not (copied/forbidden).exists(), 'Unexpected data in allowlisted image'
        version=json.loads(run('start','-a',name))
        info=json.loads(run('inspect',name))[0]
        assert info['State']['ExitCode']==0
    finally:
        info=json.loads(run('inspect',name))[0]
        assert info['Config']['Labels']['kidsmap.task33.release.owner']==nonce
        run('rm','-f',name)
    result={'status':'PASS','artifact_identity':metadata['identity'],'image_id':built['image_id'],
            'manifest_member_count':len(manifest['files']),'application_source_mismatches':[],
            'build_control_file_exclusions':diffs,'image_interpreter_dependencies':version,
            'data_paths_absent':True,'network':'none','ports':[],'application_started':False,
            'metadata_process_only':True,'cleanup':'PASS','production':'NOT_CONTACTED'}
    report=root/'docs/task33/reports/28-release-image-verification.json'
    prior=root/('docs/task33/reports/28-release-image-verification-'+('v2' if revision=='release3' else 'v1')+'.json')
    assert not prior.exists();prior.write_bytes(report.read_bytes())
    report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps({k:v for k,v in result.items() if k!='image_interpreter_dependencies'},indent=2))


if __name__ == '__main__':
    main()
