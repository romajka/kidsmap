from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/site-qa22-fix-2026-10-18-pc-r1';Q=R/'.tmp/site22-pc-fix-r1';F=R/'docs/qa/site-qa08-followup-fix-2026-10-18-pc-r1'
def adapt(s):
 for a,b in [('site08-pc-followup-r1','site22-pc-fix-r1'),('site-qa08-followup-fix-2026-10-18-pc-r1','site-qa22-fix-2026-10-18-pc-r1'),('m10s08_followup_r1','m10s22_fix_r1'),('m10s08-followup-r1','m10s22-fix-r1'),('33590','33610')]:s=s.replace(a,b)
 return s
for n in ['browser-sentinels.js','browser-readonly-green.js','browser-json-error-snapshots.js','browser-file-error-central.js','static_probe.py']:(O/n).write_text(adapt((F/n).read_text()))
urls=(Q/'qa_urls.py').read_text().replace("('super','editor','viewer','denied')","('super','editor','viewer','denied','section_editor','section_viewer')")
urls+='''
def section_values(request):
    from catalog.models import SiteSettings
    from django.contrib.admin.models import LogEntry
    assert settings.TESTING and settings.DATABASES['default']['NAME']=='m10s22_fix_r1'
    with transaction.atomic():
        with connection.cursor() as c:
            c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
        values=SiteSettings.objects.values('brand_name','about_text_ru','contacts_text_ru','footer_email','empty_results_text_ru','public_favorites_minimum').get(pk=1)
        return JsonResponse({'values':values,'admin_log_count':LogEntry.objects.count()})
urlpatterns=[path('qa/site22/values/',section_values)]+urlpatterns
'''
(Q/'qa_urls.py').write_text(urls)
s=(Q/'seed.py').read_text()+'''
for role,codename in [('section_editor','change_sitefootersettings'),('section_viewer','view_sitefootersettings')]:
 user=get_user_model().objects.create_user('site08_'+role,'site08_'+role+'@example.invalid','fictional',is_staff=True)
 user.user_permissions.add(Permission.objects.get(content_type__app_label='catalog',codename=codename))
 assert not user.has_perm('catalog.view_sitesettings') and not user.has_perm('catalog.change_sitesettings')
print('Own two section-only actors seeded; no SiteSettings grant.')
'''
(Q/'seed.py').write_text(s)
(O/'browser-sentinels-red.js').write_text((O/'browser-sentinels.js').read_text().replace('__PHASE__','red').replace('__SENTINEL_BASELINE__','null'))
print('Native support scripts/read-only section helper ready; only own scratch changed.')
