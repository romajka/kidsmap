"""Use the user's authenticated SSH master; never handle a password."""
from pathlib import Path
import json, subprocess, sys, os
root=Path.cwd()
report=root/'docs/qa/admin-moderation-release-2026-10-16-r2'
scratch=root/'.tmp/admin-moderation-release-2026-10-16-r2'
os.umask(0o077)
name=sys.argv[1]
assert name in ['preflight','build','candidate','activate','running','final']
program=(report/(name+'_remote.py')).read_text()
program=program.replace('manifest = MANIFEST', 'manifest = '+repr(json.loads((report/'manifest.json').read_text())))
if 'PREFLIGHT' in program:
    program=program.replace('PREFLIGHT',repr(json.loads((report/'preflight.json').read_text())))
if 'PACKAGESHA' in program:
    program=program.replace('PACKAGESHA',json.loads((report/'package.json').read_text())['package_sha256'])
command=['ssh','-S',str(root/'.tmp/admin-moderation-release-2026-10-16-r1/ssh-control'),'-oBatchMode=yes','-oConnectTimeout=10','root@157.173.119.227','python3 -']
result=subprocess.run(command,input=program.encode(),capture_output=True)
(scratch/(name+'.stdout')).write_bytes(result.stdout)
(scratch/(name+'.stderr')).write_bytes(result.stderr)
if result.returncode:
    print(json.dumps({'step':name,'exit':result.returncode,'detail':'Restricted scratch output; no raw server logs published'}))
    raise SystemExit(result.returncode)
safe=json.loads(result.stdout)
(report/(name+'.json')).write_text(json.dumps(safe,indent=2))
print(json.dumps(safe,indent=2))
