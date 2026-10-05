"""Use built image Python for guarded production static backend, without DB/web/network."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import uuid
import sys
sys.dont_write_bytecode = True


def main():
    root=Path('/mnt/c/kidsmap')
    built=json.loads((root/'docs/task33/reports/28-release-image.json').read_text())
    assert built['status']=='BUILT'
    revision=sys.argv[1] if len(sys.argv)>1 else 'clean-final'
    assert revision in {'clean-final','release3'}
    out=Path('/root/task33-evidence/stage28-image-static-'+revision+'-20261003'); out.mkdir(parents=True,exist_ok=False)
    temporary=Path(tempfile.mkdtemp(prefix='kidsmap-task33-qa04-image-static-'))
    for name in ('home','temp','media','socket'):(temporary/name).mkdir()
    spec=importlib.util.spec_from_file_location('qa04_runner',Path('/root/km28-release3/docs/task33/qa04/run.py'
         if revision=='release3' else '/root/km28-release2/docs/task33/qa04/run.py'))
    runner=importlib.util.module_from_spec(spec);spec.loader.exec_module(runner)
    variables=runner.clean_environment(temporary)
    variables['PYTHONPATH']='/app/docs/task33/qa04:/app/src'
    nonce=uuid.uuid4().hex;name='kidsmap-task33-image-static-'+nonce[:12]
    helper=root/'docs/task33/qa28/static_collect.py'
    command=['docker','create','--name',name,'--label','kidsmap.task33.release.owner='+nonce,
             '--network','none','--mount','type=bind,src='+str(helper)+',dst=/qa/static_collect.py,readonly',
             '--mount','type=bind,src='+str(temporary)+',dst='+str(temporary)]
    for key,value in variables.items():command += ['--env',key+'='+value]
    command += ['--workdir','/app','--entrypoint','/usr/local/bin/python',built['image_id'],
                '/qa/static_collect.py','/app','/unused','/unused','--child']
    client_env={'PATH':'/usr/bin:/bin','HOME':str(temporary/'home')}
    def run(args):return subprocess.check_output(['docker',*args],env=client_env,text=True).strip()
    subprocess.run(command,env=client_env,check=True,stdout=subprocess.DEVNULL)
    try:
        info=json.loads(run(['inspect',name]))[0]
        assert info['Config']['Labels']['kidsmap.task33.release.owner']==nonce
        assert info['HostConfig']['NetworkMode']=='none' and not info['HostConfig']['PortBindings']
        assert len(info['Mounts'])==2 and all(m['Type']=='bind' for m in info['Mounts'])
        with (out/'collectstatic.log').open('w') as log:
            subprocess.run(['docker','start','-a',name],env=client_env,stdout=log,stderr=subprocess.STDOUT,check=True)
        info=json.loads(run(['inspect',name]))[0]; exit_code=info['State']['ExitCode']
    finally:
        info=json.loads(run(['inspect',name]))[0]
        assert info['Config']['Labels']['kidsmap.task33.release.owner']==nonce
        run(['rm','-f',name])
    static=temporary/'collected-static'; files=sorted(p for p in static.rglob('*') if p.is_file())
    def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
    manifest=static/'staticfiles.json'
    assert exit_code==0 and manifest.is_file()
    result={'status':'PASS','exit':exit_code,'image_id':built['image_id'],'artifact_identity':built['artifact_identity'],
            'backend':'whitenoise.storage.CompressedManifestStaticFilesStorage','file_count':len(files),
            'manifest_sha256':sha(manifest),'file_inventory_sha256':hashlib.sha256(json.dumps(
                 [(str(p.relative_to(static)),sha(p)) for p in files],separators=(',',':')).encode()).hexdigest(),
            'output_root':str(static),'django_testing':True,'network_guard':True,'libpq_guard':True,
            'external_credentials_present':False,'network':'none','ports':[],
            'application_web_started':False,'static_only_process':True,'owned_container_cleanup':'PASS',
            'collected_output_retained':True,'production':'NOT_CONTACTED'}
    report=root/'docs/task33/reports/28-release-image-static.json'
    prior=root/('docs/task33/reports/28-release-image-static-'+('v2' if revision=='release3' else 'v1')+'.json')
    assert not prior.exists();prior.write_bytes(report.read_bytes())
    report.write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
