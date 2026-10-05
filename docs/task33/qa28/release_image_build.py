"""Build exact data-free artifact locally; never run, push or deploy application."""
import json
from pathlib import Path
import subprocess
import artifact
import sys


def main():
    root = Path('/mnt/c/kidsmap')
    metadata = json.loads((root / 'docs/task33/reports/28-artifact.json').read_text())
    revision = sys.argv[1] if len(sys.argv)>1 else 'clean'
    assert revision in {'clean','release3'}
    context = Path('/root/km28-image-context3' if revision=='release3' else '/root/km28-image-context')
    manifest = json.loads((Path(metadata['archive']).parent / 'manifest.json').read_text())
    artifact.verify(context, manifest)
    expected = {e['path'] for e in manifest['files']}
    assert {p.relative_to(context).as_posix() for p in context.rglob('*') if p.is_file()} == expected
    assert not any(p.is_symlink() for p in context.rglob('*'))
    out = Path('/root/task33-evidence/stage28-local-image-'+revision+'-20261003')
    out.mkdir(parents=True, exist_ok=False)
    home = out / 'clean-docker-home'
    home.mkdir()
    tag = 'kidsmap-task33-r2-local:' + metadata['identity'].removeprefix('r2-local-sha256-')
    command = ['docker','build','--iidfile',str(out/'image.id'),'-t',tag,str(context)]
    env = {'PATH':'/usr/bin:/bin','HOME':str(home),'DOCKER_BUILDKIT':'0'}
    with (out / 'build.log').open('w') as log:
        process = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, timeout=900)
    result = {'status':'BUILT' if process.returncode == 0 else 'NOT_BUILT', 'build_exit':process.returncode,
              'command':command,'artifact_identity':metadata['identity'],'context':str(context),
              'context_file_count':len(manifest['files']),'context_verified':True,'tag':tag,
              'clean_client_environment':True,'raw_evidence':str(out),'application_started':False,
              'pushed':False,'production':'NOT_CONTACTED'}
    if process.returncode == 0:
        inspected = json.loads(subprocess.check_output(['docker','image','inspect',tag],env=env,text=True))[0]
        result['image_id'] = inspected['Id']
        result['repo_digests'] = inspected['RepoDigests']
        result['image_id_file_matches'] = (out/'image.id').read_text().strip() == inspected['Id']
        assert result['image_id_file_matches']
        artifact.verify(context, manifest)
        assert {p.relative_to(context).as_posix() for p in context.rglob('*') if p.is_file()} == expected
        assert not any(p.is_symlink() for p in context.rglob('*'))
        result['exhaustive_context_verified_before_and_after'] = True
    else:
        result['failure_reason'] = 'LOCAL_BUILD_FAILED; inspect data-free external build.log, no image inferred'
    report = root/'docs/task33/reports/28-release-image.json'
    prior=root/('docs/task33/reports/28-release-image-'+('v2' if revision=='release3' else 'v1')+'.json')
    assert not prior.exists();prior.write_bytes(report.read_bytes())
    report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__ == '__main__':
    main()
