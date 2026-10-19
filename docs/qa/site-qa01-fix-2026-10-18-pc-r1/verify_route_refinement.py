import hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site01-pc-fix-r1';P=R/'docs/qa/site-qa01-recheck-2026-10-18-pc-r1'
target='src/catalog/testcases/test_site_qa01_media_permissions.py'
sources=json.loads((Q/'expected-source.json').read_text());sources['sources'][target]=hashlib.sha256((R/target).read_bytes()).hexdigest();(Q/'expected-source.json').write_text(json.dumps(sources,indent=2))
(Q/'test_site01_route_refined.py').write_bytes((R/target).read_bytes())
runtime=(Q/'runtime.py').read_text()
overlay="""import importlib.abc, importlib.util
class BeforeSiteFinder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname == 'catalog.domain_admin.site':
            return importlib.util.spec_from_file_location(fullname, '/mnt/c/kidsmap/docs/qa/site-qa01-fix-2026-10-18-pc-r1/entry-source/src/catalog/domain_admin/site.py')
sys.meta_path.insert(0, BeforeSiteFinder())
"""
(Q/'red_route_runtime.py').write_text(runtime.replace('django.setup()',overlay+'\ndjango.setup()'))
cmd=['docker','exec','m10s01-fix-r1-app','python',str(Q/'red_route_runtime.py'),'test','test_site01_route_refined.Site01MediaPermissionsTests.test_localized_aliases_deny_no_permission_staff']
r=subprocess.run(cmd,capture_output=True,text=True);raw=r.stdout+r.stderr;(Q/'route-refined-red.log').write_text(raw)
assert r.returncode==1 and '200 != 403' in raw and 'errors=' not in raw
diff=subprocess.run(['git','diff','--no-index','--',str(P/'candidate'/target),str(R/target)],capture_output=True,text=True)
(O/'test-route-refinement.diff').write_text(diff.stdout)
result={'red_command':cmd,'red_exit':r.returncode,'before_site_sha256':hashlib.sha256((O/'entry-source/src/catalog/domain_admin/site.py').read_bytes()).hexdigest(),
 'reason':'Candidate test assumed /az admin aliases bypass the existing canonical301. Current config.urls routes AZ aliases to canonical unprefixed paths. Revised test checks canonical ACL403, legacy301 target/no mutation, and method400 for legacy POST followed by GET.',
 'application_routes_changed':False,'expectations_weakened':False,'refined_method_red_against_original_handler':'FAIL: 200 != 403', 'test_sha256':sources['sources'][target]}
(O/'evidence/route-refinement.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
