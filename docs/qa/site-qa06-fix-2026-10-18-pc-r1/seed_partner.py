import sys,json
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/site06-pc-fix-r1');sys.argv=['runtime.py','partner-fixture'];from runtime import *
from catalog.models import SiteGalleryImage
from django.core.files.uploadedfile import SimpleUploadedFile
assert settings.TESTING and settings.DATABASES['default']['NAME']=='m10s06_fix_r1'
before=SiteGalleryImage.objects.filter(placement='HOME_PARTNERS').count();assert before==0
SiteGalleryImage.objects.create(placement='HOME_PARTNERS',image=SimpleUploadedFile('before-partner.svg',(QA/'safe.svg').read_bytes(),content_type='image/svg+xml'),title_ru='Fictional SITE06 partner')
print(json.dumps({'owned_partner_fixture':1,'previous_partners':before}))
