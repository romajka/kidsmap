"""Fixed synthetic AS-IS fixtures, aggregate results only; no business schema added."""
import io
from datetime import datetime,timedelta,timezone as tz
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import Client
from django.test.utils import CaptureQueriesContext,setup_test_environment,teardown_test_environment
from django.urls import reverse
from django.utils import translation
from PIL import Image
from catalog.models import Place,PricingPlan,PlaceReview,Event,SiteSettings,Specialist
from catalog.testcases.utils import create_quality_place,ensure_quality_subcategory
from catalog.repositories.django_repositories import DjangoPlaceRepository
from commands import dump


def measure():
    User=get_user_model()
    owner=User.objects.create_user(username='qa_owner',password='qa-pass',email='owner@example.test')
    other=User.objects.create_user(username='qa_other',password='qa-pass',email='other@example.test')
    reviewer=User.objects.create_user(username='qa_reviewer',password='qa-pass',email='reviewer@example.test')
    staff=User.objects.create_superuser(username='qa_admin',password='qa-pass',email='admin@example.test')
    volunteer=User.objects.create_user(username='qa_volunteer',password='qa-pass',is_staff=True)
    from django.contrib.auth.models import Group
    from catalog.services.staff_roles import VOLUNTEER_GROUP
    volunteer.groups.add(Group.objects.get_or_create(name=VOLUNTEER_GROUP)[0])
    ensure_quality_subcategory('EDU')
    pixel=io.BytesIO();Image.new('RGB',(320,240),'#CDE7C5').save(pixel,format='JPEG')
    def place(label,**overrides):
        return create_quality_place(name=label,name_az=label,name_ru=label,name_en=label,owner=owner,photo=SimpleUploadedFile(label+'.jpg',pixel.getvalue(),content_type='image/jpeg'),with_subcategory=True,**overrides)
    standalone=place('Standalone centre',address='Bakı, Nizami 10')
    branch_a=place('Network Yasamal',address='Bakı, Yasamal 20',lat=40.40,lng=49.82)
    branch_b=place('Network Narimanov',address='Bakı, Nərimanov 30',lat=40.41,lng=49.87)
    shared_a=place('Shared venue A',address='Bakı, shared hall 40',lat=40.42,lng=49.88)
    shared_b=create_quality_place(name='Shared venue B',name_az='Shared venue B',owner=other,address='Bakı, shared hall 40',lat=40.42,lng=49.88,photo=SimpleUploadedFile('shared-b.jpg',pixel.getvalue(),content_type='image/jpeg'),with_subcategory=True)
    missing=create_quality_place(name='No photo or coordinates',name_az='No photo or coordinates',owner=owner,lat=None,lng=None,photo='',with_subcategory=True)
    # AS-IS price age variants represent group scenarios; true OfferingGroup belongs to later stages.
    for low,high,price in [(4,6,60),(7,10,80)]:
        PricingPlan.objects.create(place=standalone,product_type='membership',billing_mode='recurring',billing_interval='month',billing_interval_count=1,price_kind='exact',price=price,age_from=low,age_to=high,title_az='Yaş qrupu',charge_role='primary')
    fixed=datetime(2026,1,15,12,tzinfo=tz.utc)
    for user,rating in [(reviewer,5),(reviewer,3),(None,4),(None,2)]:
        item=PlaceReview.objects.create(place=standalone,user=user,author_name='Synthetic reviewer',rating=rating,text='Müəllim dərsi diqqətlə izah edir və uşaqların suallarına vaxt ayırır.',status=PlaceReview.STATUS_APPROVED)
        PlaceReview.objects.filter(pk=item.pk).update(created_at=fixed)
    event=Event.objects.create(owner=owner,related_place=standalone,name='Family laboratory',name_az='Ailə laboratoriyası',category='ART',start_datetime=fixed+timedelta(days=365),end_datetime=fixed+timedelta(days=365,hours=2),status=Event.STATUS_PUBLISHED,address='Bakı, original venue')
    specialist=Specialist.objects.create(owner=owner,name='Synthetic specialist',bio_az='Uşaqların inkişafını dəstəkləyən təcrübəli mütəxəssis.',status=Specialist.STATUS_PUBLISHED)
    site=SiteSettings.get_solo();site.events_section_enabled=True;site.specialists_section_enabled=True;site.save()
    dump('fixtures.json',{'source':'synthetic generated only in disposable QA PostgreSQL','places':6,'logical_network_branches':2,'independent_shared_venue_businesses':2,'missing_photo_coords':1,'tariff_age_variants':2,'old_reviews':4,'known_account_repeated_reviews':2,'unknown_user_reviews':2,'events':1,'specialists':1,'limitations':['Organization/Program/Activity/OfferingGroup/confirmed-venue absent in AS-IS; network/shared-address/group cases are logical fixtures using existing Place/PricingPlan fields, not implemented future relationships','No real user records/photos/contact data loaded']})
    metrics=[]
    def orm_probe(label,fn):
        observed=[]
        for repeat in range(2):
            cache.clear();translation.activate('az')
            with CaptureQueriesContext(connection)as captured:result=fn()
            observed.append({'sql_queries':len(captured),'result_count':len(result),'private_result_ids':result})
        same=observed[0]['private_result_ids']==observed[1]['private_result_ids']
        for row in observed:row.pop('private_result_ids')
        metrics.append({'surface':label,'kind':'ORM','runs':observed,'same_result_ids':same,'same_query_count':observed[0]['sql_queries']==observed[1]['sql_queries']})
    repo=DjangoPlaceRepository()
    orm_probe('catalog published',lambda:list(repo.active_queryset().values_list('pk',flat=True)))
    orm_probe('map ready',lambda:list(repo.map_ready_queryset().values_list('pk',flat=True)))
    orm_probe('age matched tariffs',lambda:list(PricingPlan.objects.filter(age_from__lte=8,age_to__gte=8).values_list('pk',flat=True)))
    setup_test_environment()
    try:
        guest=Client();owned=Client();owned.force_login(owner);admin=Client();admin.force_login(staff);vol=Client();vol.force_login(volunteer)
        surfaces=[('public catalog',guest,reverse('place_list')),('place detail',guest,standalone.get_absolute_url()),('owner',owned,reverse('owner_places_dashboard')),('admin',admin,reverse('admin:catalog_place_change',args=[standalone.pk])),('volunteer',vol,reverse('admin:volunteer_index')),('events',guest,reverse('events_landing')),('specialist',guest,specialist.get_absolute_url())]
        for label,client,url in surfaces:
            # Warm session/CSRF and then identical cold application-cache requests.
            client.get(url)
            rows=[]
            for _ in range(2):
                cache.clear();translation.activate('az')
                with CaptureQueriesContext(connection)as captured:
                    response=client.get(url)
                    count=None
                    if response.context:
                        for key in ['places','events','specialists']:
                            try:value=response.context[key]
                            except KeyError:continue
                            if value is not None:
                                try:count=len(value)
                                except TypeError:pass
                                break
                rows.append({'status_code':response.status_code,'sql_queries':len(captured),'result_count':count})
            metrics.append({'surface':label,'kind':'HTTP test client; not rendered browser','runs':rows,'same_status_count':rows[0]==rows[1]})
    finally:teardown_test_environment()
    dump('query-baseline.json',{'repeat_count':2,'query_text_saved':False,'row_payload_saved':False,'metrics':metrics,'place_review_rows':PlaceReview.objects.count(),'known_distinct_reviewers':PlaceReview.objects.exclude(user=None).values('user_id').distinct().count(),'current_rating_formula_not_changed':True})
