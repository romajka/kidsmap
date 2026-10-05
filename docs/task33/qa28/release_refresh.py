"""Preserve V1 and freeze only the corrected QA reader into a new R2 identity."""
import json
from pathlib import Path
import shutil
import artifact


def main():
    root = Path('/mnt/c/kidsmap')
    report = root / 'docs/task33/reports/28-artifact.json'
    old = json.loads(report.read_text())
    old_manifest = json.loads((Path(old['archive']).parent / 'manifest.json').read_text())
    artifact.verify(Path(old['standby']), old_manifest)
    name = 'docs/task33/qa28/recovery_reader.py'
    mirror = Path('/root/km28-release2-source')
    assert not mirror.exists()
    shutil.copytree(Path(old['standby']), mirror)
    shutil.copyfile(root / name, mirror / name)
    result = artifact.freeze(mirror, Path('/root/task33-evidence/stage28-artifact-20261003'), Path('/root/km28-release2'))
    new_manifest = json.loads((Path(result['archive']).parent / 'manifest.json').read_text())
    old_files = {e['path']:e for e in old_manifest['files']}
    new_files = {e['path']:e for e in new_manifest['files']}
    assert old_files.keys() == new_files.keys()
    changed = [p for p in old_files if old_files[p] != new_files[p]]
    assert changed == [name], 'Only corrected QA reader may change'
    result['compiled_locale_deltas'] = old['compiled_locale_deltas']
    result['workspace_source_snapshot'] = old['workspace_source_snapshot']
    for entry in result['workspace_source_snapshot']:
        if entry['path'] == name:
            entry['sha256'] = new_files[name]['sha256']
    result['source_equal_except_compiled_locales'] = True
    previous = root / 'docs/task33/reports/28-artifact-v1.json'
    assert not previous.exists()
    previous.write_bytes(report.read_bytes())
    report.write_text(json.dumps(result, indent=2) + '\n')
    refresh = {'status':'PASS', 'prior_identity':old['identity'], 'current_identity':result['identity'],
               'prior_archive_preserved':True,'changed_member_count':1,
               'changed_members':[{'path':name,'prior_sha256':old_files[name]['sha256'],
                                   'current_sha256':new_files[name]['sha256']}],
               'application_changed':False,'prior_standby':old['standby'],'current_standby':result['standby'],
               'current_archive':result['archive'],'current_archive_sha256':result['archive_sha256'],
               'current_manifest_sha256':result['manifest_sha256'],'production':'NOT_CONTACTED'}
    (root / 'docs/task33/reports/28-artifact-refresh.json').write_text(json.dumps(refresh,indent=2)+'\n')
    print(json.dumps(refresh,indent=2))


if __name__ == '__main__':
    main()
