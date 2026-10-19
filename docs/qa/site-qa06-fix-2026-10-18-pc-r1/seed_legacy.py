import json,sys
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/site06-pc-fix-r1');sys.argv=['runtime.py','legacy-fixture'];from runtime import *
from catalog.models import SiteSettings
from django.core.files.uploadedfile import SimpleUploadedFile
assert settings.TESTING and settings.DATABASES['default']['NAME']=='m10s06_fix_r1'
s=SiteSettings.get_solo();s.logo=SimpleUploadedFile('legacy-broken.png',b'synthetic legacy invalid PNG',content_type='image/png');s.save()
(QA/'legacy-fixture.json').write_text(json.dumps({'synthetic_only':True,'logo':s.logo.name,'original_new_upload_boundary_intentionally_bypassed_by_fixture_model_write':True}))
print(json.dumps({'owned_legacy_fixture_seeded':True,'not_new_upload_ingress':True}))
