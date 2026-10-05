"""Make image-vs-host interpreter/dependency drift explicit without application claims."""
import json
from pathlib import Path
import sys
root=Path('/mnt/c/kidsmap/docs/task33/reports')
host=json.loads((root/'28-artifact-identity.json').read_text())
image=json.loads((root/'28-release-image-verification.json').read_text())['image_interpreter_dependencies']
def normalized(values):return {name.lower().replace('_','-'):version for name,version in values}
a=normalized(host['dependencies']);b=normalized(image['dependencies'])
changed=[{'package':name,'host_version':a.get(name),'image_version':b.get(name)}
         for name in sorted(set(a)|set(b)) if a.get(name)!=b.get(name)]
result={'host_python':host['python'],'image_python':image['python'],
        'host_dependency_count':len(a),'image_dependency_count':len(b),'changed_dependencies':changed,
        'changed_dependency_count':len(changed),'full_suite_inside_image':'NOT_RUN',
        'image_static':'PASS','production':'NOT_CONTACTED'}
report = root/'28-release-runtime-delta.json'
if len(sys.argv)>1:
    assert sys.argv[1] == 'release3'
    preserved = root/'28-release-runtime-delta-v2.json'
    assert not preserved.exists()
    preserved.write_bytes(report.read_bytes())
report.write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
