"""After root GREEN only, freeze declared Event admin precision application delta."""
import json
from pathlib import Path
import shutil
import artifact


def main():
    root=Path('/mnt/c/kidsmap');report=root/'docs/task33/reports/28-artifact.json'
    previous=json.loads(report.read_text());before=json.loads(Path(previous['archive']).with_name('manifest.json').read_text())
    old_context=Path('/root/km28-image-context');artifact.verify(old_context,before)
    mirror=Path('/root/km28-release3-source');assert not mirror.exists()
    shutil.copytree(old_context,mirror)
    allowed=['src/catalog/domain_admin/place.py','src/catalog/forms.py',
             'src/catalog/testcases/test_task33_event_admin_precision.py']
    approved_sha = ['b36dec7efe5aeff66f5b47dfd09a0e007d2453195ec8bba62c8c5e44a46e5c9e',
                    'deb9c5114d9bd6d7f0d2157c7eb9343c87bb58ff64096b3c28081c72de21cbe9',
                    '26963290982c62a7858e1951855ca5f8d102a73f0564a30ab7feda96da4c966d']
    for name, expected in zip(allowed, approved_sha):
        assert artifact.digest((root/name).read_bytes()) == expected, 'Root GREEN source drift: ' + name
    for name in allowed:
        path=root/name;assert path.is_file() and not path.is_symlink()
        target=mirror/name;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(path,target)
    current=artifact.freeze(mirror,Path('/root/task33-evidence/stage28-artifact-20261003'),Path('/root/km28-release3'))
    after=json.loads(Path(current['archive']).with_name('manifest.json').read_text())
    a={e['path']:e for e in before['files']};b={e['path']:e for e in after['files']}
    added=sorted(set(b)-set(a));deleted=sorted(set(a)-set(b));changed=sorted(p for p in set(a)&set(b) if a[p]!=b[p])
    assert not deleted and set(added+changed)==set(allowed)
    snapshots={e['path']:e['sha256'] for e in previous['workspace_source_snapshot']}
    for name in allowed:snapshots[name]=b[name]['sha256']
    current['workspace_source_snapshot']=[{'path':name,'sha256':sha} for name,sha in sorted(snapshots.items())]
    current['compiled_locale_deltas']=previous['compiled_locale_deltas']
    current['source_equal_except_compiled_locales']=True
    preserved=root/'docs/task33/reports/28-artifact-v2.json';assert not preserved.exists();preserved.write_bytes(report.read_bytes())
    report.write_text(json.dumps(current,indent=2)+'\n')
    result={'status':'PASS','prior_identity':previous['identity'],'current_identity':current['identity'],
            'changed_members':[{'path':p,'prior_sha256':a[p]['sha256'],'current_sha256':b[p]['sha256']} for p in changed],
            'added_members':[{'path':p,'sha256':b[p]['sha256']} for p in added],'deleted_members':deleted,
            'current_file_count':current['file_count'],'current_standby':current['standby'],
            'current_archive':current['archive'],'archive_sha256':current['archive_sha256'],
            'manifest_sha256':current['manifest_sha256'],'prior_archive_preserved':True,'production':'NOT_CONTACTED'}
    (root/'docs/task33/reports/28-artifact-refresh3.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result,indent=2))


if __name__=='__main__':main()
