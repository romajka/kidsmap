import sys,ast,json,hashlib
from pathlib import Path
sys.argv=['runtime.py','proposal-static'];import runtime
from django.template import engines
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/site01-pc-plan-r1';O=R/'docs/qa/site-qa01-recheck-2026-10-18-pc-r1';C=O/'candidate'
for p in C.rglob('*.py'):ast.parse(p.read_text())
engines['django'].from_string((C/'templates/admin/catalog/sitegalleryimage/change_list.html').read_text())
proto=ast.dump(ast.parse((Q/'test_site01_candidate.py').read_text()));candidate=ast.dump(ast.parse((C/'src/catalog/testcases/test_site_qa01_media_permissions.py').read_text()));assert proto==candidate
print(json.dumps({'candidate_python_ast_valid':True,'candidate_django_template_compiles':True,'candidate_test_ast_matches_red_executed_prototype':True,'ast_sha256':hashlib.sha256(proto.encode()).hexdigest(),'application_patch_applied':False,'candidate_green_execution':'NOT RUN'}))
