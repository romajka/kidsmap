import io,json,sys
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/site06-pc-plan-r1');sys.argv=['runtime.py','media-fixtures'];from runtime import *
from PIL import Image
from catalog.models import SiteSettings
from django.core.files.uploadedfile import SimpleUploadedFile
assert settings.TESTING and settings.DATABASES['default']['NAME']=='m10s06_plan_r1'
b=io.BytesIO()
with Image.new('RGBA',(40,40),(0,150,70,180)) as img:img.save(b,'PNG')
raw=b.getvalue();(QA/'valid.png').write_bytes(raw);(QA/'broken.png').write_bytes(b'not a png; own SITE06 fixture')
(QA/'safe.svg').write_text('<svg xmlns="http://www.w3.org/2000/svg" width="40" height="40" viewBox="0 0 40 40"><rect width="40" height="40" fill="#009646"/></svg>')
s=SiteSettings.get_solo();s.logo=SimpleUploadedFile('before.png',raw,content_type='image/png');s.save()
print(json.dumps({'synthetic_media_fixtures':3,'owned_normal_db':True,'baseline_logo_seeded':True}))
