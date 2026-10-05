"""Verify that native restore commands can touch only the QA04-owned container."""
import json
import subprocess
from pathlib import Path


def validate_owned_container(info, *, nonce, socket):
    labels = info.get('Config', {}).get('Labels') or {}
    host = info.get('HostConfig', {})
    mounts = info.get('Mounts') or []
    if not nonce or labels.get('kidsmap.task33.owner') != nonce:
        raise RuntimeError('QA04 nonce mismatch')
    if host.get('NetworkMode') != 'none' or host.get('PortBindings'):
        raise RuntimeError('QA04 network isolation mismatch')
    if '/var/lib/postgresql/data' not in (host.get('Tmpfs') or {}):
        raise RuntimeError('QA04 PGDATA is not tmpfs')
    binds = [mount for mount in mounts if mount.get('Type') == 'bind']
    if len(binds) != 1 or binds[0].get('Source') != str(socket) or binds[0].get('Destination') != '/qa-socket':
        raise RuntimeError('QA04 socket mount mismatch')


def find_owned_container(socket):
    socket = Path(socket)
    if socket.name != 'socket' or not socket.parent.name.startswith('kidsmap-task33-qa04-socket-'):
        raise RuntimeError('Unexpected QA04 socket')
    listing = subprocess.run(['docker', 'ps', '--filter', 'label=kidsmap.task33.owner', '--format', '{{.ID}}'],
                             check=True, capture_output=True, text=True)
    matches = []
    for container_id in listing.stdout.splitlines():
        inspected = subprocess.run(['docker', 'inspect', container_id, '--format', '{{json .}}'],
                                   check=True, capture_output=True, text=True)
        info = json.loads(inspected.stdout)
        nonce = (info.get('Config', {}).get('Labels') or {}).get('kidsmap.task33.owner', '')
        try:
            validate_owned_container(info, nonce=nonce, socket=socket)
        except RuntimeError:
            continue
        if info.get('Name') != '/kidsmap-task33-qa04-' + nonce[:12] or not info.get('State', {}).get('Running'):
            raise RuntimeError('QA04 name or running state mismatch')
        matches.append(container_id)
    if len(matches) != 1:
        raise RuntimeError('Expected exactly one socket-owned QA04 container')
    return matches[0]
