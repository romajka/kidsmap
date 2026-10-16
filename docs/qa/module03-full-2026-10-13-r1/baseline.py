"""Two legacy failures on pre-patch source overlay, preserving actual WORKTREE."""
import hashlib,json,shutil,subprocess
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2];Q=R/'docs/qa/module03-spec-fix-2026-10-13-r1';S=R/'.tmp'/Q.name
baseline=S/'baseline-src';assert not baseline.exists()
shutil.copytree(R/'src',baseline,ignore=shutil.ignore_patterns('__pycache__','*.pyc'))
snapshot=json.loads((R/'docs/qa/module03-plan-2026-10-13-r1/snapshot.json').read_text())['sha256']
paths=['src/catalog/forms.py','src/catalog/services/specialist_documents.py','src/catalog/controllers/specialist_workspace.py']
for name in paths:
 data=subprocess.check_output(['git','show','HEAD:'+name]);assert hashlib.sha256(data).hexdigest()==snapshot[name]
 (baseline/Path(name).relative_to('src')).write_bytes(data)
t=(Q/'runtime.py').read_text().replace("str(ROOT/'src')","str(SCRATCH/'baseline-src')")
t=t.replace("mode=sys.argv[1]","import catalog.forms,catalog.services.specialist_documents\nassert str(SCRATCH/'baseline-src') in catalog.forms.__file__\nassert str(SCRATCH/'baseline-src') in catalog.services.specialist_documents.__file__\nmode=sys.argv[1]")
# Absolute HERE ensures same owned settings/DB/media/locale, never another stand.
t=t.replace("HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];SCRATCH=ROOT/'.tmp'/HERE.name","HERE=Path("+repr(str(Q))+");ROOT=HERE.parents[2];SCRATCH=ROOT/'.tmp'/HERE.name")
(S/'baseline-runtime.py').write_text(t)
args=[str(S/'venv/bin/python'),str(P/'command.py'),'baseline-legacy',str(S/'venv/bin/python'),str(S/'baseline-runtime.py'),'test','catalog.testcases.specialists.TestOwnerSpecialistManagement.test_owner_uploads_documents_as_pending_private_certificates','catalog.testcases.specialists.TestSpecialistsFeatureFlag.test_feature_enabled_by_default']
(P/'baseline-source.json').write_text(json.dumps({'overlay':str(baseline),'prepatch_source_match':paths,'original_worktree_changed':False}))
raise SystemExit(subprocess.run(args).returncode)
