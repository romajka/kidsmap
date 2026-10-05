"""Verify final content-addressed artifact and summarize data-free identities."""
import hashlib
import json
from pathlib import Path
import artifact


def main():
    root = Path('/mnt/c/kidsmap')
    metadata = json.loads((root / 'docs/task33/reports/28-artifact.json').read_text())
    directory = Path(metadata['archive']).parent
    manifest_file = directory / 'manifest.json'
    assert artifact.digest(manifest_file.read_bytes()) == metadata['manifest_sha256']
    assert artifact.digest(Path(metadata['archive']).read_bytes()) == metadata['archive_sha256']
    manifest = json.loads(manifest_file.read_text())
    artifact.verify(Path(metadata['standby']), manifest)
    def grouped(prefix=None, suffix=None):
        entries = [e for e in manifest['files'] if (prefix is None or e['path'].startswith(prefix))
                   and (suffix is None or suffix in e['path'])]
        data = json.dumps([{'path': e['path'], 'sha256': e['sha256']} for e in entries],
                          sort_keys=True, separators=(',', ':')).encode()
        return {'file_count': len(entries), 'path_sha256_inventory_sha256': artifact.digest(data)}
    mismatches = []
    for entry in metadata['workspace_source_snapshot']:
        path = root / entry['path']
        if not path.is_file() or artifact.digest(path.read_bytes()) != entry['sha256']:
            mismatches.append(entry['path'])
    assert not mismatches, 'Captured workspace drift'
    image_file = root / 'docs/task33/reports/28-release-image.json'
    image = json.loads(image_file.read_text()) if image_file.is_file() else {}
    static_file = root / 'docs/task33/reports/28-release-image-static.json'
    static = json.loads(static_file.read_text()) if static_file.is_file() else {}
    image_matches = image.get('artifact_identity') == metadata['identity'] and image.get('status') == 'BUILT'
    static_matches = static.get('artifact_identity') == metadata['identity'] and static.get('status') == 'PASS'
    result = {'status': 'PASS', 'identity': metadata['identity'], 'file_count': len(manifest['files']),
              'archive_sha256': metadata['archive_sha256'], 'manifest_sha256': metadata['manifest_sha256'],
              'python': manifest['python'], 'python_executable_sha256': manifest['python_executable_sha256'],
              'dependencies': manifest['dependencies'], 'dependency_count': len(manifest['dependencies']),
              'static_source_identity': grouped('static/'), 'migration_source_identity': grouped(suffix='/migrations/'),
              'compiled_locale_identity': grouped('locale/', '/LC_MESSAGES/django.mo'),
              'artifact_verified': True, 'workspace_captured_source_mismatches': mismatches,
              'compiled_locale_deltas': metadata['compiled_locale_deltas'],
              'actual_application_image': 'BUILT_LOCAL_SEPARATE_EVIDENCE' if image_matches else 'NOT_BUILT',
              'actual_local_image_id': image.get('image_id') if image_matches else None,
              'collected_static': 'PASS_LOCAL_IMAGE' if static_matches else 'NOT_RUN',
              'runtime_schema': 'database-reviewer and root own fresh PostgreSQL evidence',
              'production': 'NOT_CONTACTED'}
    (root / 'docs/task33/reports/28-artifact-identity.json').write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps({key: value for key, value in result.items() if key != 'dependencies'}, indent=2))


if __name__ == '__main__':
    main()
