"""Current source identity for explicit auth/upload negatives, not live-provider proof."""
import hashlib
import json
from pathlib import Path
root=Path('/mnt/c/kidsmap');mirror=Path('/root/km28-security');artifact=Path('/root/km28-release3')
paths=['src/catalog/google_auth.py','src/catalog/services/auth_redirects.py',
       'src/catalog/services/email_verification.py','src/catalog/photo_views.py',
       'src/catalog/testcases/test_google_auth.py','src/catalog/testcases/auth_flow.py',
       'src/catalog/testcases/photo_workflow.py','src/catalog/testcases/image_uploads.py']
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
files=[{'path':p,'workspace_sha256':sha(root/p),'mirror_sha256':sha(mirror/p),
        'artifact_sha256':sha(artifact/p)} for p in paths]
for item in files:item['matches']=item['workspace_sha256']==item['mirror_sha256']==item['artifact_sha256']
result={'file_count':len(files),'all_matches':all(e['matches'] for e in files),'files':files,'production':'NOT_CONTACTED'}
(root/'docs/task33/final-audit/security-supplement-source.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'files':len(files),'all_matches':result['all_matches']}))
assert result['all_matches']
