import json,sys
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/site15-pc-fix-r1');sys.argv=['runtime.py','catalog-fixture'];from runtime import *
from catalog.models import CatalogContentSettings
assert settings.TESTING and settings.DATABASES['default']['NAME']=='m10s15_fix_r1'
before=CatalogContentSettings.objects.count();obj=CatalogContentSettings.get_solo();assert obj.pk==1
print(json.dumps({'owned_fixture_only':True,'catalog_before_count':before,'catalog_after_count':CatalogContentSettings.objects.count()}))
