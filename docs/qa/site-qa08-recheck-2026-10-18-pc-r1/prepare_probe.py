import json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/site08-pc-plan-r1';O=R/'docs/qa/site-qa08-recheck-2026-10-18-pc-r1';F=R/'docs/qa/site-qa21-fix-2026-10-18-pc-r1'
assert (O/'evidence/setup.json').exists()
def adapt(s):
 for a,b in [('site21-pc-fix-r1','site08-pc-plan-r1'),('site-qa21-fix-2026-10-18-pc-r1','site-qa08-recheck-2026-10-18-pc-r1'),('m10s21_fix_r1','m10s08_plan_r1'),('m10s21-fix-r1','m10s08-plan-r1'),('33560','33570'),('site21_','site08_'),('qa/site21/','qa/site08/')]:s=s.replace(a,b)
 return s
for n in ['start_server.py','browser_driver.py']:(O/n).write_text(adapt((F/n).read_text()))
s=(Q/'seed.py').read_text();s+='''
from io import BytesIO
from PIL import Image
from django.core.files.base import ContentFile
site=SiteSettings.get_solo();bio=BytesIO();Image.new('RGB',(32,32),'#0d8a52').save(bio,format='PNG')
site.logo.save('synthetic_'+('long_filename_'*8)+'.png',ContentFile(bio.getvalue()),save=False)
site.brand_name='KidsMap QA synthetic';site.footer_email='qa@example.invalid'
for lang in ['ru','az','en']:setattr(site,'about_text_'+lang,'QA '+lang+' synthetic paragraph. '*10)
site.save()
print('Own synthetic settings fixture populated; local media only.')
''';(Q/'seed.py').write_text(s)
u=(Q/'qa_urls.py').read_text();u+='''
def all_state(request):
    import hashlib,json
    from catalog.models import SiteSettings,CatalogContentSettings
    from django.contrib.admin.models import LogEntry
    assert settings.TESTING and settings.DATABASES['default']['NAME']=='m10s08_plan_r1'
    with transaction.atomic():
        with connection.cursor() as c:
            c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
        rows=[list(SiteSettings.objects.values()),list(CatalogContentSettings.objects.values())]
        digest=hashlib.sha256(json.dumps(rows,sort_keys=True,default=str).encode()).hexdigest()
        return JsonResponse({'synthetic_settings_sha256':digest,'admin_log_count':LogEntry.objects.count()})
urlpatterns=[path('qa/site08/all-state/',all_state)]+urlpatterns
''';(Q/'qa_urls.py').write_text(u)
for n in ['runtime.py','qa_settings.py','qa_urls.py','seed.py','proxy.py']:(O/n).write_bytes((Q/n).read_bytes())
(O/'prepare_probe.py').write_bytes(Path(__file__).read_bytes())
print('Own probe prepared.')
