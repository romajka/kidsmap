"""Build QA-only current Program/Activity/Organization bridge from verified R1 transport."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
target=HERE/'browser_targeted_bridge'
target.mkdir(exist_ok=True)
(target/'__init__.py').write_text('',encoding='utf-8')
text=(HERE/'browser_r1_bridge/commands.py').read_text(encoding='utf-8')
text=text.replace('Organization, OrganizationGrant, Place, VolunteerPlaceRevision','Organization, OrganizationGrant, Place, VolunteerPlaceRevision, Program, Activity, OfferingGroup, PricingPlan')
fixture="""
    # Direct synthetic approved display fixtures; not claimed as browser publication.
    for lang in ('az','ru','en'):
        setattr(organization,'name_'+lang,'QA AUDIT ORGANIZATION '+lang.upper())
        setattr(organization,'description_'+lang,'QA AUDIT APPROVED ORGANIZATION DESCRIPTION '+lang.upper())
    organization.phone='+994501234567';organization.save()
    program=Program.objects.create(organization=organization,created_by=users['network_owner'],
        name_az='QA AUDIT PROGRAM AZ',name_ru='QA AUDIT PROGRAM RU',name_en='QA AUDIT PROGRAM EN',
        description_az='QA AUDIT APPROVED DESCRIPTION AZ',description_ru='QA AUDIT APPROVED DESCRIPTION RU',description_en='QA AUDIT APPROVED DESCRIPTION EN',
        category=branch.category,status='published',approved_at=timezone.now())
    activity=Activity.objects.create(place=branch,program=program,status='published',supplement_az='QA AUDIT LOCAL AZ',supplement_ru='QA AUDIT LOCAL RU',supplement_en='QA AUDIT LOCAL EN')
    group=OfferingGroup.objects.create(activity=activity,name_az='QA AUDIT GROUP',name_ru='QA AUDIT GROUP',name_en='QA AUDIT GROUP',age_from=5,age_to=8,language='az',schedule_text='Saturday 10:00',conditions_az='QA AUDIT LOCAL CONDITIONS')
    from decimal import Decimal
    PricingPlan.objects.create(offering_group=group,product_type='lesson',price=Decimal('25'))
    private_activity=Activity.objects.create(place=branch,name_az='QA AUDIT PRIVATE ACTIVITY',status='draft')
    private_org=Organization.objects.create(owner=users['network_owner'],name_az='QA AUDIT PRIVATE ORGANIZATION',status='draft')
"""
text=text.replace('    for lang in (\'az\',\'ru\',\'en\'):\n        with override(lang):',fixture+'\n    for lang in (\'az\',\'ru\',\'en\'):\n        with override(lang):',1)
text=text.replace("'fallback_detail':standalone.get_absolute_url(),","'fallback_detail':standalone.get_absolute_url(),\n                'program':reverse('organization_program_detail',args=[organization.pk,program.pk]),\n                'program_save':reverse('organization_program_save',args=[organization.pk,program.pk]),\n                'activity':reverse('activity_detail',args=[activity.pk]),\n                'organization':reverse('organization_detail',args=[organization.public_id]),\n                'private_activity':reverse('activity_detail',args=[private_activity.pk]),\n                'private_organization':reverse('organization_detail',args=[private_org.public_id]),")
state="""
            if path=='/qa28/targeted-state' and method=='GET':
                program.refresh_from_db();activity.refresh_from_db()
                rev=getattr(program,'content_revision',None)
                self.json({'program_name':program.name_az,'description':program.description_az,'status':program.status,
                    'revision_status':rev.status if rev else None,'revision_version':rev.version if rev else None,
                    'revision_payload':rev.payload if rev else {},'activity_snapshot':activity.program_snapshot,'supplement':activity.supplement_az})
                close_old_connections();return
"""
text=text.replace("            if path=='/qa28/fixtures'",state+"            if path=='/qa28/fixtures'",1)
(target/'commands.py').write_text(text,encoding='utf-8')
print('Targeted synthetic bridge ready; initial publication is fixture setup only')
