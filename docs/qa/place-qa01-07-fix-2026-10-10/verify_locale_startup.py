"""Own stand must refuse damaged locale assets before binding HTTP."""
import json
import socket
import subprocess
import sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2]
build=ROOT/'.tmp/place-qa01-07-fix-20261010/locale-build-02'
manifest=build/'manifest.json';mo=build/'locale/az/LC_MESSAGES/django.mo'
original_manifest=manifest.read_bytes();original_mo=mo.read_bytes()
rows=[]
def port_free():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',8840))
def attempt(name,mode='serve'):
    port_free()
    argv=[sys.executable,str(HERE/'runtime.py'),mode]
    result=subprocess.run(argv,cwd=ROOT,capture_output=True,encoding='utf-8',timeout=15)
    rows.append({'case':name,'argv':argv,'exit_code':result.returncode,'http_port_unbound':True})
    port_free()
    assert result.returncode==(0 if mode=='preflight' else 1),(name,result.returncode)
try:
    mo.write_bytes(b'corrupt');attempt('corrupt MO')
    mo.unlink();attempt('missing MO');mo.write_bytes(original_mo)
    manifest.unlink();attempt('missing manifest');manifest.write_bytes(original_manifest)
    candidate=json.loads(original_manifest);candidate['status']='building'
    manifest.write_text(json.dumps(candidate),encoding='utf-8');attempt('incomplete manifest')
finally:
    manifest.write_bytes(original_manifest);mo.write_bytes(original_mo)
attempt('valid full manifest','preflight')
(HERE/'locale-startup.json').write_text(json.dumps(rows,indent=2)+'\n',encoding='utf-8')
print('Four invalid startups refused before HTTP bind; restored valid manifest accepted.')
