"""Copy rehearsal helpers into the new completion namespace; never edit audit history."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4]
HERE=Path(__file__).resolve().parent
OLD=ROOT/'docs/task33/qa28'
commands=(OLD/'recovery_commands.py').read_text(encoding='utf-8')
commands=commands.replace("HERE.parent / 'qa04'","HERE.parent.parent / 'qa04'")
commands=commands.replace("HERE.parent / 'qa23'","HERE.parent.parent / 'qa23'")
commands=commands.replace("from recovery_fixtures import","from domain_recovery_fixtures import")
commands=commands.replace("standby / 'docs/task33/qa28/recovery_reader.py'","standby / 'docs/task33/completion/qa/domain_recovery_reader.py'")
commands=commands.replace('qa_stage28_restore','qa_completion_restore')
commands=commands.replace("name_az='Təsdiqlənmiş proqram', description_az=", "category_id=new.category_id, subcategory_id=new.subcategory_id,\n        name_az='Təsdiqlənmiş proqram', description_az=")
(HERE/'domain_recovery_commands.py').write_text(commands,encoding='utf-8')
fixtures=(OLD/'recovery_fixtures.py').read_text(encoding='utf-8')
fixtures=fixtures.replace("    return {'approved_claim':1,", """    add_completion_taxonomy(actor,place,organization)
    return {'standalone_taxonomy':1,'linked_approved_subcategory':1,'detached_taxonomy_copy':1,'approved_claim':1,""")
fixtures += '''

def add_completion_taxonomy(actor,place,organization):
    from catalog.models import Activity,Program,OfferingGroup,PricingPlan
    from catalog.testcases.utils import create_quality_place,ensure_quality_subcategory
    from catalog.services.organization_ownership import request_join,detach
    sub=ensure_quality_subcategory('ART')
    standalone=Activity.objects.create(place=place,name_az='QA completion standalone taxonomy',
        status='published',category_id='ART',subcategory=sub)
    group=OfferingGroup.objects.create(activity=standalone,name_az='Standalone taxonomy group',age_from=4,age_to=8)
    PricingPlan.objects.create(offering_group=group,product_type='lesson',price='31')
    linked=Activity.objects.get(place=place,program__isnull=False)
    other=create_quality_place(owner=actor,created_by=actor,name='QA completion detached taxonomy',
        name_az='QA completion detached taxonomy',with_subcategory=True)
    request_join(actor=actor,place_id=other.pk,organization_id=organization.pk)
    copied=Activity.objects.create(place=other,program=linked.program,status='published',
        program_snapshot=dict(linked.program_snapshot),source_program=linked.source_program,
        source_program_version=linked.source_program_version)
    copy_group=OfferingGroup.objects.create(activity=copied,name_az='Detached taxonomy group',age_from=4,age_to=8)
    PricingPlan.objects.create(offering_group=copy_group,product_type='lesson',price='32')
    detach(actor=actor,place_id=other.pk,organization_id=organization.pk,expected_ownership_version=other.ownership_version)
    copied.refresh_from_db()
    if copied.program_id is not None or copied.category_id!=linked.program_snapshot['category_id'] or copied.subcategory_id!=linked.program_snapshot['subcategory_id']:
        raise RuntimeError('Completion detached taxonomy seed differs from approved copy')
'''
(HERE/'domain_recovery_fixtures.py').write_text(fixtures,encoding='utf-8')
reader=(OLD/'recovery_reader.py').read_text(encoding='utf-8').replace('qa_stage28_restore','qa_completion_restore')
reader=reader.replace("        cursor.execute('ROLLBACK')", """        from catalog.models import Activity
        from catalog.services.catalog_structure import activity_taxonomy_ids
        standalone=Activity.objects.get(name_az='QA completion standalone taxonomy')
        if standalone.category_id!='ART' or standalone.subcategory_id is None:
            raise RuntimeError('Restored standalone taxonomy lost')
        linked=Activity.objects.get(place=place,program__isnull=False)
        if activity_taxonomy_ids(linked)!=('EDU',place.subcategory_id):
            raise RuntimeError('Restored linked approved taxonomy lost')
        detached=Activity.objects.get(place__name='QA completion detached taxonomy')
        if detached.program_id is not None or detached.category_id!='EDU' or detached.subcategory_id!=place.subcategory_id:
            raise RuntimeError('Restored detached taxonomy lost')
        from catalog.services.filtering import PlaceListFilters
        from catalog.repositories.django_repositories import DjangoPlaceRepository
        from django.test import RequestFactory
        filters=PlaceListFilters.from_request(RequestFactory().get('/places/',{'category':'ART','subcategory':standalone.subcategory_id,'age':5}))
        if not filters.apply(DjangoPlaceRepository().active_queryset()).filter(pk=place.pk).exists():
            raise RuntimeError('Restored approved taxonomy search lost')
        cursor.execute('ROLLBACK')""")
reader=reader.replace("'localized_urls': True", "'localized_urls': True,'standalone_taxonomy':True,'linked_approved_subcategory':True,'detached_taxonomy_copy':True,'exact_taxonomy_search':True")
(HERE/'domain_recovery_reader.py').write_text(reader,encoding='utf-8')
print('New completion recovery copies prepared; historical helpers unchanged.')
