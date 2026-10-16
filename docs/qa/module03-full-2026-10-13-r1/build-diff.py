"""Reviewable batch diff against exact pre-patch entry, excluding earlier fixes."""
import difflib,hashlib,json,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2]
snapshot=json.loads((P.parent/'module03-plan-2026-10-13-r1/snapshot.json').read_text())['sha256']
paths=['requirements.txt','src/catalog/services/specialist_documents.py','src/catalog/services/specialist_document_validation.py','src/catalog/services/specialist_document_probe.py','src/catalog/controllers/specialist_workspace.py','src/catalog/forms.py','src/catalog/testcases/specialist_document_fixtures.py','src/catalog/testcases/test_spec_qa01_document_validation.py','src/catalog/testcases/test_spec_qa02_photo_conflict.py','src/catalog/testcases/test_task33_specialist_screens_security.py','src/catalog/testcases/test_task33_specialist_workspace.py','src/catalog/testcases/specialists.py','src/catalog/testcases/test_task33_specialist_db_review.py','static/css/pages/specialists.css',*[f'locale/{lang}/LC_MESSAGES/django.po' for lang in ['ru','az','en']]]
patch=''
for name in paths:
 current=(R/name).read_text()
 if name not in snapshot:before=''
 elif name.startswith('locale/'):
  before=current[:current.index('\n#: src/catalog/services/specialist_document_validation.py')]
 else:before=subprocess.check_output(['git','show','HEAD:'+name],text=True)
 if name in snapshot:assert hashlib.sha256(before.encode()).hexdigest()==snapshot[name],name
 patch+=''.join(difflib.unified_diff(before.splitlines(keepends=True),current.splitlines(keepends=True),fromfile='a/'+name if before else '/dev/null',tofile='b/'+name))
(P/'APPLICATION_DIFF.patch').write_text(patch);(P/'changed-files.json').write_text(json.dumps(paths,indent=2));print('Reviewable diff:',len(paths),'scoped source/test/config/PO files')
