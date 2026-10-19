import json
from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/site08-pc-fix-r1';O=R/'docs/qa/site-qa08-fix-2026-10-18-pc-r1';P=R/'docs/qa/site-qa08-recheck-2026-10-18-pc-r1';F=R/'docs/qa/site-qa21-fix-2026-10-18-pc-r1'
assert (O/'evidence/setup.json').exists()
def adapt(s):
 for a,b in [('site08-pc-plan-r1','site08-pc-fix-r1'),('site-qa08-recheck-2026-10-18-pc-r1','site-qa08-fix-2026-10-18-pc-r1'),('m10s08_plan_r1','m10s08_fix_r1'),('m10s08-plan-r1','m10s08-fix-r1'),('33570','33580')]:s=s.replace(a,b)
 return s
for n in ['start_server.py','browser_driver.py']:(O/n).write_text(adapt((P/n).read_text()))
s=adapt((P/'browser-acceptance.js').read_text());(O/'browser-acceptance.js').write_text(s)
for phase in ['red','green']:(O/('browser-acceptance-'+phase+'.js')).write_text(s.replace("'/png/acceptance-'","'/png/"+phase+"-acceptance-'"))
v=s.replace('login/super/','login/viewer/').replace("['sitebrandingsettings','siteaboutsettings','sitecontactssettings','sitefootersettings','siteemptystatesettings','sitevisibilitysettings','siteanalytics','catalogcontentsettings','sitegalleryimage']","['catalogcontentsettings']").replace('.filter(visible).length===2','.filter(visible).length===(innerWidth<=760?0:2)')
for phase in ['red','green']:(O/('browser-readonly-'+phase+'.js')).write_text(v.replace("'/png/acceptance-'","'/png/"+phase+"-readonly-'"))
(O/'native-code-provenance.json').write_text(json.dumps({'PLAN_no_injection_script_retained':True,'phase_difference':'PNG prefix only','readonly_difference':'viewer fixture, catalogue only, retained hidden mobile actions expected; desktop SITE20 state retained','app_overrides':False},indent=2))
extra='''
def form_state(request):
    import hashlib
    from catalog.models import SiteSettings,SiteGalleryImage
    from django.contrib.admin.models import LogEntry
    from PIL import Image
    assert settings.TESTING and settings.DATABASES['default']['NAME']=='m10s08_fix_r1'
    with transaction.atomic():
        with connection.cursor() as c:
            c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
        site=SiteSettings.objects.get(pk=1)
        media={p.relative_to(settings.MEDIA_ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in settings.MEDIA_ROOT.rglob('*') if p.is_file()}
        logo_size=None
        if site.logo:
            with Image.open(site.logo.path) as img:logo_size=list(img.size)
        return JsonResponse({'brand_name':site.brand_name,'footer_email':site.footer_email,'logo':site.logo.name,'logo_size':logo_size,'updated_at':site.updated_at,'media':media,'gallery':list(SiteGalleryImage.objects.order_by('pk').values('pk','placement','order','is_active','title_ru','title_az','title_en','image')),'admin_log_count':LogEntry.objects.count(),'last_log_repr':LogEntry.objects.order_by('-pk').values_list('object_repr',flat=True).first()})
urlpatterns=[path('qa/site08/form-state/',form_state)]+urlpatterns
'''
(Q/'qa_urls.py').write_text((Q/'qa_urls.py').read_text()+extra)
seed=(Q/'seed.py').read_text()+'''\nfrom pathlib import Path\nassets=QA/'assets';assets.mkdir(exist_ok=True)\nfor n,size,color in [('valid_'+('long_name_'*8)+'.png',128,'#0d8a52'),('restore.png',32,'#0d8a52')]:\n Image.new('RGB',(size,size),color).save(assets/n,format='PNG')\n(assets/'broken.png').write_bytes(b'not-a-png')\n''';(Q/'seed.py').write_text(seed)
for n in ['runtime.py','qa_settings.py','qa_urls.py','seed.py','proxy.py','playwright.json']:(O/n).write_bytes((Q/n).read_bytes())
(O/'prepare_runtime.py').write_bytes(Path(__file__).read_bytes())
b=(F/'run_backend.py').read_text()
for a,c in [('site21-pc-fix-r1','site08-pc-fix-r1'),('m10s21-fix-r1','m10s08-fix-r1')]:b=b.replace(a,c)
(O/'run_backend.py').write_text(b)
print('Fix runtime and identical source RED/GREEN acceptance prepared.')
