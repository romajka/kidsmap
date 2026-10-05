"""Attach actually executed image/static evidence to current local release metadata."""
import json
from pathlib import Path
import sys

root=Path('/mnt/c/kidsmap/docs/task33/reports')
revision = sys.argv[1] if len(sys.argv) > 1 else 'v2'
assert revision in {'v2', 'release3'}
def read(name):return json.loads((root/name).read_text())
image=read('28-release-image.json');verified=read('28-release-image-verification.json')
static=read('28-release-image-static.json');host=read('28-static.json')
assert image['status']=='BUILT' and verified['status']==static['status']=='PASS'
assert image['image_id']==verified['image_id']==static['image_id']
assert image['artifact_identity']==static['artifact_identity']==host['artifact_identity']
for key in ('file_count','manifest_sha256','file_inventory_sha256'):assert static[key]==host[key]
for name in ('28-artifact-identity.json','28-release-compose.json'):
    report=read(name)
    suffix = '-before-image-release3.json' if revision == 'release3' else '-before-image.json'
    preserved = root/(name.removesuffix('.json')+suffix)
    assert not preserved.exists()
    preserved.write_text(json.dumps(report,indent=2)+'\n')
    report['actual_application_image']='BUILT_LOCAL_SEPARATE_EVIDENCE'
    report['actual_local_image_id']=image['image_id']
    report['image_evidence']='28-release-image.json / 28-release-image-verification.json'
    if name=='28-artifact-identity.json':
        report['collected_static']='PASS_HOST_AND_LOCAL_IMAGE'
        report['static_evidence']='28-static.json / 28-release-image-static.json'
    (root/name).write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'status':'PASS','image_id':image['image_id'],'host_image_static_identity_match':True,
                  'file_count':static['file_count'],'application_started':False,'production':'NOT_CONTACTED'}))
