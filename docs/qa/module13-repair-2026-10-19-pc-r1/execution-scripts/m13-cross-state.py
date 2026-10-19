from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1'
t=(Q/'qa_urls.py').read_text();assert 'def cross_state(' not in t
t+='''
def cross_state(request):
    guard()
    from catalog.models import Organization,Program,Place,Event,Activity,VolunteerPlaceRevision
    with transaction.atomic():
        with connection.cursor() as c:
            c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
        org=Organization.objects.get(pk=2);p=Place.objects.get(pk=2);program=Program.objects.get(pk=2)
        assert org.name_az.startswith('M13') and p.name_az.startswith('M13')
        urls={}
        for lang in ['az','ru','en']:
            with translation.override(lang):
                urls[lang]={'organization':reverse('organization_detail',args=[org.public_id]),'place':p.get_absolute_url(),'online':Event.objects.get(pk=3).get_absolute_url()}
        return JsonResponse({'urls':urls,'organization':{'id':org.pk,'status':org.status,'version':org.content_version,'branches':org.places.count(),'candidate_pending':VolunteerPlaceRevision.objects.filter(organization=org,status='pending').exists()},'place':{'id':p.pk,'status':p.status,'organization_id':p.organization_id,'ownership_version':p.organization_ownership_version},'program':{'id':program.pk,'status':program.status,'version':program.content_version,'activities':Activity.objects.filter(program=program,archived_at__isnull=True).count()},'online':{'state':Event.objects.get(pk=3).occurrence_state},'fixture_only':True})
urlpatterns.insert(0,path('qa/m13/cross/',cross_state))
'''
# Actual Place ownership field is verified before writing the helper.
t=t.replace('p.organization_ownership_version','p.ownership_version')
(Q/'qa_urls.py').write_text(t)
t=(O/'browser-network-publication.js').read_text();prefix=t[:t.index(' try{')];body=t[t.index("  phase='program-submit'"):];body=body.replace('form[data-program-form] button[name=submit]','form[action$="/programs/2/save/"] button[name=submit]')
(O/'browser-program-publish.js').write_text(prefix+" try{const p=await make('owner'),a=await make('admin'),other=await make('viewer');\n"+body)
print('Prepared read-only cross-state helper and remaining native program flow')
