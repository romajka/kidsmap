"""Independent source checks and owned, network-none bind persistence rehearsal."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import uuid
import yaml


def main():
    root = Path('/mnt/c/kidsmap')
    out = Path('/root/task33-evidence/stage28-release-20261003')
    out.mkdir(parents=True, exist_ok=False)
    base = yaml.safe_load((root / 'docker-compose.yml').read_text())['services']['web']
    override = yaml.safe_load((root / 'docs/task33/qa28/release-R2-compose.override.yml').read_text())['services']['web']
    red = {'private_bind_missing': not any('/kidsmap-private-media' in value for value in base['volumes']),
           'cohort_environment_missing': 'TASK33_R1_WRITE_MODE' not in base['environment']}
    assert all(red.values())
    bind = override['volumes'][0]
    assert bind['target'] == '/kidsmap-private-media' and bind['type'] == 'bind'
    assert ':?' in bind['source'] and ':?' in override['image'] and ':?' in override['build']['context']
    assert override['environment']['TASK33_R1_WRITE_MODE'] == '${TASK33_R1_WRITE_MODE:-off}'
    assert override['environment']['TASK33_R1_WRITE_USER_IDS'] == '${TASK33_R1_WRITE_USER_IDS:-}'
    clean_env = {'PATH': '/usr/bin:/bin', 'HOME': str(out), 'COMPOSE_DISABLE_ENV_FILE': '1'}
    compose = subprocess.run(['docker', 'compose', 'version'], env=clean_env, capture_output=True, text=True)
    assert compose.returncode != 0, 'Compose now available: execute actual config validation instead'
    private = out / 'private-media'
    private.mkdir(mode=0o700)
    nonce = uuid.uuid4().hex
    name = 'kidsmap-task33-release-' + nonce[:12]
    image = 'postgres:17-alpine'
    docker = ['docker']
    def run(*args):
        return subprocess.check_output(docker + list(args), text=True).strip()
    def verify_owned():
        info = json.loads(run('inspect', name))[0]
        assert info['Config']['Labels']['kidsmap.task33.release.owner'] == nonce
        assert info['HostConfig']['NetworkMode'] == 'none' and not info['HostConfig']['PortBindings']
        assert any(m['Source'] == str(private) and m['Destination'] == '/kidsmap-private-media'
                   for m in info['Mounts'])
    def create():
        run('run', '-d', '--name', name, '--label', 'kidsmap.task33.release.owner=' + nonce,
            '--network', 'none', '--mount', 'type=bind,src=' + str(private) + ',dst=/kidsmap-private-media',
            '--entrypoint', '/bin/sh', image, '-c', 'sleep 300')
        verify_owned()
    try:
        create()
        run('exec', name, '/bin/sh', '-c', 'umask 077; printf synthetic-private-document > /kidsmap-private-media/probe.bin')
        expected = hashlib.sha256((private / 'probe.bin').read_bytes()).hexdigest()
        verify_owned()
        run('rm', '-f', name)
        create()
        actual = run('exec', name, 'sha256sum', '/kidsmap-private-media/probe.bin').split()[0]
        assert actual == expected
        image_id = run('image', 'inspect', image, '--format', '{{.Id}}')
    finally:
        listed = run('ps', '-a', '--filter', 'name=^/' + name + '$', '--format', '{{.Names}}')
        if listed:
            verify_owned()
            run('rm', '-f', name)
    result = {'status': 'PASS_BOUNDED', 'base_source_red': red, 'override_source_checks': 'PASS',
              'compose_config': 'NOT_RUN_PLUGIN_UNAVAILABLE', 'compose_missing_required_path_negative': 'NOT_RUN_PLUGIN_UNAVAILABLE',
              'bind_persistence_across_owned_container_recreation': 'PASS', 'synthetic_file_sha256': expected,
              'cached_probe_image': image, 'cached_probe_image_id': image_id, 'application_image': 'NOT_BUILT',
              'network': 'none', 'ports': [], 'cleanup': 'PASS', 'production': 'NOT_CONTACTED'}
    (root / 'docs/task33/reports/28-release-validation.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
