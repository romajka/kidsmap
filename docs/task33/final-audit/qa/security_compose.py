"""Resolve only synthetic Compose inputs; never invoke stack or production operations."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys


def main():
    root = Path('/mnt/c/kidsmap')
    executable = Path('/root/task33-compose-tools/docker-compose')
    expected = 'c57ab918abd5b05ca7e7d0f275875dd1330a695074f309dc9eab1b49efafcd4b'
    assert hashlib.sha256(executable.read_bytes()).hexdigest() == expected
    revision = 'v3'
    assert revision in {'v3', 'v4'}
    context = '/root/km28-image-context3'
    out = Path('/root/task33-evidence/final-audit-compose-20261004')
    out.mkdir(parents=True, exist_ok=False)
    env_file = out / 'synthetic.env'
    env_file.write_text('')
    inputs = {'PATH': '/usr/bin:/bin', 'HOME': str(out), 'COMPOSE_DISABLE_ENV_FILE': '1',
              'DB_NAME': 'synthetic', 'DB_USER': 'synthetic', 'DB_PASSWORD': 'synthetic',
              'DATABASE_URL': 'postgresql://synthetic:synthetic@postgres:5432/synthetic',
              'TASK33_PRIVATE_MEDIA_PATH': str(out / 'private-media'),
              'TASK33_R2_BUILD_CONTEXT': context,
              'TASK33_R2_IMAGE': 'kidsmap-r2@sha256:' + '0' * 64}
    command = [str(executable), '--env-file', str(env_file), '-f', str(root / 'docker-compose.yml'),
               '-f', str(root / 'docs/task33/qa28/release-R2-compose.override.yml'), 'config', '--format', 'json']
    process = subprocess.run(command, cwd=out, env=inputs, capture_output=True, text=True)
    assert process.returncode == 0, 'Compose synthetic merge failed'
    web = json.loads(process.stdout)['services']['web']
    assert web['environment']['TASK33_R1_WRITE_MODE'] == 'off'
    assert web['environment']['TASK33_R1_WRITE_USER_IDS'] == ''
    assert web['build']['context'] == context
    assert web['image'] == inputs['TASK33_R2_IMAGE']
    assert any(m['target'] == '/kidsmap-private-media' and m['type'] == 'bind'
               and m['source'] == inputs['TASK33_PRIVATE_MEDIA_PATH'] for m in web['volumes'])
    negatives = []
    for key in ['TASK33_PRIVATE_MEDIA_PATH', 'TASK33_R2_BUILD_CONTEXT', 'TASK33_R2_IMAGE']:
        missing = inputs.copy()
        del missing[key]
        failed = subprocess.run(command, cwd=out, env=missing, capture_output=True, text=True)
        assert failed.returncode != 0 and key in failed.stderr
        negatives.append({'omitted_variable': key, 'exit': failed.returncode, 'passed': True})
    result = {'status': 'PASS', 'standalone_compose': 'v5.5.0', 'binary_sha256': expected,
              'official_binary_checksum_matched': True, 'positive_merge_exit': process.returncode,
              'required_variable_negative_cases': negatives, 'resolved_default_write_mode': 'off',
              'resolved_selected_user_ids_empty': True, 'resolved_build_context': web['build']['context'],
              'resolved_private_mount_target': '/kidsmap-private-media',
              'synthetic_image_digest_only': True, 'actual_application_image': 'CONFIG_ONLY_BUILD_EVIDENCE_SEPARATE',
              'actual_production_config': 'UNKNOWN', 'production': 'NOT_CONTACTED'}
    report = root / 'docs/task33/final-audit/security-compose.json'
    if revision == 'v4':
        preserved = report.with_name('28-release-compose-v3.json')
        assert not preserved.exists()
        preserved.write_bytes(report.read_bytes())
    report.write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    main()
