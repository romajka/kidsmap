"""Synthetic R2 records and bounded query comparison, never production fixtures."""
from datetime import timedelta
from pathlib import Path
import statistics
import time


def add_r2_records(actor, place, organization):
    from django.conf import settings
    from django.contrib.auth import get_user_model
    from django.core.files.uploadedfile import SimpleUploadedFile
    from django.utils import timezone
    from catalog.models import (Specialist, SpecialistPracticeLocation, SpecialistClaim,
        SpecialistDocument, Event, EventReview, SiteSettings, WorkflowNotification, EmailOutbox)
    from catalog.services import specialist_domain as sd, specialist_documents as docs, event_domain as ed
    from catalog.services.workflow_notifications import emit
    settings.PRIVATE_MEDIA_ROOT = Path(settings.MEDIA_ROOT).parent / 'private-media'
    reviewer=get_user_model().objects.create_superuser('qa28-reviewer','qa28-reviewer@example.invalid','isolated')
    person_user=get_user_model().objects.create_user('qa28-person',email='qa28-person@example.invalid')
    person=sd.propose_person(actor=person_user,name='QA28 post-switch person',consultation_format='online')
    claim=sd.request_claim(actor=person_user,specialist_id=person.pk)
    sd.review_claim(actor=reviewer,claim_id=claim.pk,expected_version=claim.version,approve=True)
    person.refresh_from_db();person.status='published';person.save()
    employment=sd.propose_employment(actor=actor,specialist_id=person.pk,organization_id=organization.pk,
        role='Synthetic practitioner',start_date=timezone.localdate())
    employment=sd.confirm_employment(actor=person_user,employment_id=employment.pk,side='person',expected_version=employment.version)
    employment=sd.confirm_employment(actor=actor,employment_id=employment.pk,side='organization',expected_version=employment.version)
    SpecialistPracticeLocation.objects.create(specialist=person,place=place,address='Historical synthetic practice',is_active=False)
    SpecialistPracticeLocation.objects.create(specialist=person,address='New synthetic practice',is_active=True)
    for kind in ('identity','certificate'):
        doc=docs.upload_document(actor=person_user,specialist_id=person.pk,
            uploaded_file=SimpleUploadedFile(kind+'.pdf',b'%PDF-1.4 synthetic QA28 '+kind.encode()),document_type=kind,name='Synthetic '+kind)
        docs.review_document(actor=reviewer,document_id=doc.pk,approve=True)
        if kind=='certificate': docs.set_document_public_choice(actor=person_user,document_id=doc.pk,publish=True)
    event=ed.create_event(actor=actor,values=dict(name_az='QA28 post-switch event',category_id=place.category_id,
        organizer_organization_id=organization.pk,event_format='physical',related_place_id=place.pk,
        address=place.address,age_from=3,age_to=12,price_text='Free',phone='+994501234567',
        description_az='Synthetic recovered event',start_datetime=timezone.now()+timedelta(days=5),end_datetime=timezone.now()+timedelta(days=5,hours=2)))
    event=ed.publish_event(actor=reviewer,event_id=event.pk,expected_updated_at=event.updated_at.isoformat())
    event=ed.reschedule_event(actor=actor,event_id=event.pk,start_datetime=event.start_datetime+timedelta(days=1),
        end_datetime=event.end_datetime+timedelta(days=1),expected_updated_at=event.updated_at.isoformat(),reason='Synthetic move')
    event=ed.cancel_event(actor=actor,event_id=event.pk,expected_updated_at=event.updated_at.isoformat(),reason='Synthetic cancel')
    review=EventReview.objects.create(event=event,user=person_user,rating=5,text='Synthetic typed Event review',status='approved')
    emit(kind='qa28_recovery',entity_type='event',entity_id=event.pk,version=3,recipient_user=person_user)
    site=SiteSettings.get_solo();site.events_section_enabled=True;site.specialists_section_enabled=True;site.save()
    assert claim.pk and employment.history.count()==3 and review.current_revision_id
    add_completion_taxonomy(actor,place,organization)
    return {'standalone_taxonomy':1,'linked_approved_subcategory':1,'detached_taxonomy_copy':1,'approved_claim':1,'active_bilateral_employment':1,'employment_history':3,'practice_history':2,
        'private_identity':1,'opted_in_approved_certificate':1,'published_cancelled_event':1,'occurrence_history':2,
        'typed_event_review':1,'durable_pending_notification':1}


def performance():
    """Compare literal naive per-event organizer fetch to same current select_related query."""
    from django.db import connection
    from django.test.utils import CaptureQueriesContext
    from catalog.models import Event
    event=Event.objects.get(name_az='QA28 post-switch event')
    for index in range(200):
        Event.objects.create(name_az='QA28 perf '+str(index),category_id=event.category_id,
            organizer_organization_id=event.organizer_organization_id,event_format='online',
            start_datetime=event.start_datetime,end_datetime=event.end_datetime)
    measurements=[]
    for size in (20,200):
        for mode in ('naive_current_orm','select_related_current_orm'):
            samples=[];counts=[]
            for repeat in range(3):
                qs=Event.objects.filter(name_az__startswith='QA28 perf').order_by('pk')[:size]
                if mode.startswith('select_related'): qs=qs.select_related('organizer_organization')
                with CaptureQueriesContext(connection) as captured:
                    started=time.perf_counter(); names=[row.organizer_organization.name_az for row in qs]
                    samples.append(round((time.perf_counter()-started)*1000,3))
                counts.append(len(captured));assert len(names)==size
            measurements.append({'size':size,'mode':mode,'query_counts':counts,'elapsed_ms':samples,'median_ms':statistics.median(samples)})
    return {'meaning':'Same final source/fixtures; naive N+1 control versus eager ORM, not historical release or production load',
        'sizes':[20,200],'repetitions':3,'measurements':measurements}


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
