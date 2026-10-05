"""One-shot recovery for the identified interrupted browser launcher only."""
import json
import subprocess
from pathlib import Path

NAME = 'kidsmap-task33-qa04-350084c3ae82'
EXPECTED_SOCKET = '/root/kidsmap-task33/.tmp/kidsmap-task33-qa04-socket-71ndoehj/socket'
EXPECTED_CREATED = '2026-10-03T07:41:19.152143154Z'
EVIDENCE = Path('/root/task33-evidence/browser21-final-20261003')
bridge = json.loads((EVIDENCE / 'launcher-interrupted/browser-bridge.json').read_text())
assert bridge['synthetic_only'] is True and bridge['outbound_guard'] == 'UNCHANGED'
def owned():
    info = json.loads(subprocess.check_output(['docker', 'inspect', NAME]))[0]
    nonce = info['Config']['Labels']['kidsmap.task33.owner']
    assert NAME == 'kidsmap-task33-qa04-' + nonce[:12] and len(nonce) == 32
    assert info['Created'] == EXPECTED_CREATED
    assert info['HostConfig']['NetworkMode'] == 'none' and not info['HostConfig']['PortBindings']
    assert '/var/lib/postgresql/data' in info['HostConfig']['Tmpfs']
    binds = [item for item in info['Mounts'] if item['Type'] == 'bind']
    assert len(binds) == 1 and binds[0]['Source'] == EXPECTED_SOCKET and binds[0]['Destination'] == '/qa-socket'
    return info['Id'], nonce
identity, nonce = owned()
assert owned() == (identity, nonce)
result = subprocess.run(['docker', 'rm', '--force', identity], capture_output=True)
record = dict(container=NAME, ownership_checks='IDENTIFIED_BY_NAME_LABEL_MOUNT_CREATED', original_launcher_nonce_record='UNAVAILABLE', container_removed=result.returncode == 0,
              launcher_interrupted=True, untouched_unknown_temp_roots=True)
(EVIDENCE / 'cleanup-recovery.json').write_text(json.dumps(record, indent=2))
print(json.dumps(record))
raise SystemExit(result.returncode)
