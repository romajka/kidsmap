import json,subprocess
from pathlib import Path
Q=Path(__file__).resolve().parent
label='catalog.testcases.public.TestPublicPagesSmoke.test_collectstatic_builds_manifest_for_public_assets_in_production_mode'
r=subprocess.run(['docker','exec','m10full-pc-r1-app','python',str(Q/'runtime.py'),'test',label],capture_output=True,text=True);(Q/'test-static-retry.log').write_text(r.stdout+r.stderr);(Q/'test-static-retry.exit').write_text(str(r.returncode)+'\n');print(json.dumps({'methods':1,'exit':r.returncode,'tail':(r.stdout+r.stderr)[-900:]}))
