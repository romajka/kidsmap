"""No database, cache, network or project settings; focused text-only RED/GREEN."""
import json
from pathlib import Path
import sys
import unittest
import ast
sys.path.insert(0,str(Path(__file__).resolve().parents[4]/'src'))
from django.conf import settings
settings.configure(USE_I18N=False,LANGUAGE_CODE='az',DATABASES={'default':{'ENGINE':'django.db.backends.dummy'}})
import django
django.setup()
from catalog.services.locations import localize_address_text
source=Path(__file__).resolve().parents[4]/'src/catalog/testcases/public.py'
tree=ast.parse(source.read_text(encoding='utf-8'))
method=next(node for node in ast.walk(tree) if isinstance(node,ast.FunctionDef)
    and node.name=='test_localized_address_removes_duplicate_city_and_district_segments')
cases=next(ast.literal_eval(node.value) for node in method.body if isinstance(node,ast.Assign)
    and any(isinstance(target,ast.Name) and target.id=='cases' for target in node.targets))
for language,value,expected in cases:
    assert localize_address_text(value,language)==expected, (language,value,localize_address_text(value,language),expected)
suite=unittest.defaultTestLoader.loadTestsFromName('catalog.testcases.test_task33_completion_localization')
result=unittest.TextTestRunner(verbosity=2).run(suite)
summary={'tests':result.testsRun,'failures':len(result.failures),'errors':len(result.errors),'settings':'synthetic dummy DB; no project settings'}
if len(sys.argv)>1:Path(sys.argv[1]).write_text(json.dumps(summary,indent=2)+'\n')
raise SystemExit(not result.wasSuccessful())
