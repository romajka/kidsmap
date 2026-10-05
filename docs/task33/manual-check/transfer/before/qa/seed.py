"""One-time synthetic manual acceptance dataset. Restart preserves user edits."""
import io,json
from datetime import timedelta
from pathlib import Path
from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import transaction
from django.urls import reverse
from django.utils import timezone,translation
from PIL import Image,ImageDraw
from catalog.models import (Category,Subcategory,Organization,OrganizationGrant,Program,Activity,OfferingGroup,PricingPlan,
    Specialist,SpecialistPracticeLocation,SiteSettings,UserEmailVerification)
from catalog.services import organization_ownership,specialist_domain,event_domain
from catalog.services.review_versions import submit_review,moderate_candidate
from catalog.testcases.utils import create_ready_place

def seed():
    target=settings.QA_ROOT/'fixtures.json'
    if target.exists():return
    with transaction.atomic():
        users={}
        for role in ('parent','owner','manager','person','moderator','outsider','volunteer'):
            u=get_user_model().objects.create_user('demo_'+role,email=role+'@example.invalid',password='KidsMap-local-2026')
            u.first_name={'parent':'Родитель','owner':'Владелец сети','manager':'Менеджер филиала','person':'Специалист','moderator':'Модератор','outsider':'Другой владелец','volunteer':'Волонтёр'}[role]
            if role in ('moderator','volunteer'):u.is_staff=True
            if role=='moderator':u.is_superuser=True
            u.save()
            UserEmailVerification.objects.update_or_create(user=u,defaults={'email':u.email,'is_verified':True,'verified_at':timezone.now()})
            users[role]=u
        from catalog.services.staff_roles import VOLUNTEER_GROUP
        users['volunteer'].groups.add(Group.objects.get_or_create(name=VOLUNTEER_GROUP)[0])
        categories={}
        for code,az,ru,en,subaz,subru,suben in [('EDU','Təhsil','Образование','Education','Robototexnika','Робототехника','Robotics'),('ART','Yaradıcılıq','Творчество','Arts','Rəsm','Рисование','Drawing')]:
            cat,_=Category.objects.update_or_create(code=code,defaults={'name':ru,'name_az':az,'name_ru':ru,'name_en':en,'is_active':True})
            sub,_=Subcategory.objects.get_or_create(code='manual-'+code.lower(),defaults={'category':cat,'name':subru,'name_az':subaz,'name_ru':subru,'name_en':suben})
            categories[code]=(cat,sub)
        owner=users['owner'];now=timezone.now()
        org=Organization.objects.create(owner=owner,created_by=owner,name_az='Kəşf — sınaq şəbəkəsi',name_ru='Открытие — тестовая сеть',name_en='Discovery — demo network',
            description_az='Uşaqlar üçün yaradıcılıq və elm dərsləri.',description_ru='Тестовая сеть детских центров: робототехника, рисование и открытые мастер-классы.',description_en='A demo network with robotics, arts and family workshops.',phone='+994501234567',status='published',approved_at=now)
        image=Image.new('RGB',(1000,650),'#cde7c5');draw=ImageDraw.Draw(image)
        draw.rounded_rectangle((100,120,430,500),radius=35,fill='#136f38');draw.ellipse((520,150,870,500),fill='#f4c06a')
        stream=io.BytesIO();image.save(stream,format='JPEG')
        places=[]
        for i,(az,ru,en) in enumerate([('Kəşf Yasamal','Открытие — Ясамал','Discovery Yasamal'),('Kəşf Nərimanov','Открытие — Нариманов','Discovery Narimanov'),('Rəng studiyası','Студия Красок','Colour Studio')]):
            actor=owner if i<2 else users['outsider']
            p=create_ready_place(owner=actor,created_by=actor,name=ru,name_az=az,name_ru=ru,name_en=en,
                description_ru='Занятия в небольших группах, понятное расписание и общение с родителями. Все данные на этой странице вымышлены для локальной проверки. '*2,
                description_en='Small group lessons, a clear schedule and communication with parents. All data is synthetic for local review. '*2,
                category=categories['EDU'][0],subcategory=categories['EDU'][1],district='baku_yasamal' if i!=1 else 'baku_narimanov',
                address=['Bakı, Yasamal, sınaq ünvanı 10','Bakı, Nərimanov, sınaq ünvanı 20','Bakı, sınaq ünvanı 30'][i],
                lat=40.40+i*.008,lng=49.82+i*.024,photo=SimpleUploadedFile('manual-centre.jpg',stream.getvalue(),content_type='image/jpeg'))
            if i<2:organization_ownership.request_join(actor=owner,place_id=p.pk,organization_id=org.pk);p.refresh_from_db()
            places.append(p)
        grant=OrganizationGrant.objects.create(organization=org,owner=owner,member=users['manager'],base_ownership_version=org.ownership_version,
            scope='selected_places',actions=['organization.view','place.view','place.edit'])
        grant.selected_places.add(places[0])
        program=Program.objects.create(organization=org,created_by=owner,name_az='Robototexnika 7–10',name_ru='Робототехника 7–10',name_en='Robotics 7–10',
            description_az='Uşaqlar ilk robotlarını hazırlayırlar.',description_ru='Дети собирают первых роботов и учатся работать в команде.',description_en='Build a first robot and learn to work together.',
            category=categories['EDU'][0],subcategory=categories['EDU'][1],status='published',approved_at=now)
        linked=[]
        for i,p in enumerate(places[:2]):
            a=Activity.objects.create(place=p,program=program,status='published')
            g=OfferingGroup.objects.create(activity=a,name_az='Robot qrupu',name_ru='Роботы — группа',name_en='Robot group',age_from=7,age_to=10,language='ru',schedule_text='Saturday 10:00–11:30')
            PricingPlan.objects.create(offering_group=g,product_type='lesson',price=25+i*5)
            linked.append(a)
        art=Activity.objects.create(place=places[0],name_az='Rəsm 4–6',name_ru='Рисование 4–6',name_en='Drawing 4–6',status='published',category=categories['ART'][0],subcategory=categories['ART'][1])
        g=OfferingGroup.objects.create(activity=art,name_az='Kiçik rəssamlar',name_ru='Юные художники',name_en='Young artists',age_from=4,age_to=6,language='az',schedule_text='Sunday 11:00–12:00')
        PricingPlan.objects.create(offering_group=g,product_type='lesson',price=15)
        unclassified=Activity.objects.create(place=places[0],name_az='Açıq görüş',name_ru='Открытая встреча без категории',name_en='Unclassified open session',status='published')
        g=OfferingGroup.objects.create(activity=unclassified,name_az='Açıq qrup',name_ru='Открытая группа',name_en='Open group',age_from=3,age_to=12)
        PricingPlan.objects.create(offering_group=g,product_type='lesson',price=10)
        person=Specialist.objects.create(name='Лейла — тестовый специалист',name_alt='Leyla — demo specialist',slug='leyla-demo',verified_person_user=users['person'],person_verified_at=now,
            status='published',is_active=True,consultation_format='online',bio_az='Uşaqların inkişafına dəstək.',bio_ru='Вымышленный специалист для проверки профиля и согласования работы с сетью.',bio_en='Synthetic practitioner for profile and employment checks.',language_az=True,language_ru=True,language_en=True,phone='+994501234567')
        zero=Specialist.objects.create(name='Новый специалист — стаж 0',slug='zero-experience-demo',status='published',is_active=True,experience_years=0,consultation_format='online')
        unclaimed=Specialist.objects.create(name='Неподтверждённый профиль — демо',slug='unclaimed-demo',status='published',is_active=True,consultation_format='online')
        employment=specialist_domain.propose_employment(actor=owner,specialist_id=person.pk,organization_id=org.pk,role='Педагог',start_date=timezone.localdate())
        employment=specialist_domain.confirm_employment(actor=owner,employment_id=employment.pk,side='organization',expected_version=employment.version)
        SpecialistPracticeLocation.objects.create(specialist=person,place=places[0],address=places[0].address,is_active=True,is_primary=True)
        events={}
        for i,(label,ru) in enumerate([('physical','Семейная робототехника'),('online','Онлайн-встреча с педагогом'),('cancelled','Отменённый мастер-класс'),('moved','Перенесённый мастер-класс'),('draft','Черновик нового события')]):
            start=(now+timedelta(days=i+2)).replace(hour=10,minute=0,second=0,microsecond=0)
            e=event_domain.create_event(actor=owner,values={'name_az':ru+' AZ','name_ru':ru,'name_en':label.title()+' workshop',
                'description_az':'Sınaq tədbiri — bütün məlumatlar uydurmadır.','description_ru':'Синтетическое событие для ручной проверки; бронирования и оплаты не выполняются.','description_en':'Synthetic local workshop for manual review.',
                'category_id':'EDU','organizer_organization_id':org.pk,'event_format':'online' if label=='online' else 'physical',
                'related_place_id':None if label=='online' else places[0].pk,'address':'' if label=='online' else places[0].address,
                'start_datetime':start,'end_datetime':start+timedelta(hours=2),'age_from':6,'age_to':12,'price_text':'15 AZN','phone':'+994501234567'})
            if label!='draft':e=event_domain.publish_event(actor=users['moderator'],event_id=e.pk,expected_updated_at=e.updated_at.isoformat())
            if label=='cancelled':e=event_domain.cancel_event(actor=owner,event_id=e.pk,expected_updated_at=e.updated_at.isoformat(),reason='Учебная отмена')
            if label=='moved':e=event_domain.reschedule_event(actor=owner,event_id=e.pk,start_datetime=start+timedelta(days=3),end_datetime=start+timedelta(days=3,hours=2),expected_updated_at=e.updated_at.isoformat(),reason='Учебный перенос')
            events[label]=e
        head,rev=submit_review(target=places[0],user=users['parent'],rating=5,text='Понятное расписание и небольшие группы. Это тестовый отзыв.',author_name='Тестовый родитель')
        moderate_candidate(head=head,revision_id=rev.pk,actor=users['moderator'],approve=True)
        site=SiteSettings.get_solo();site.events_section_enabled=True;site.specialists_section_enabled=True;site.save()
        links={}
        for lang in ('az','ru','en'):
            with translation.override(lang):
                row={key:reverse(name) for key,name in {'home':'home','catalog':'place_list','events':'events_landing','specialists':'specialist_list','account':'account_dashboard','places':'owner_places_dashboard','organizations':'organization_workspace_index','inbox':'account_notifications','team':'owner_team_dashboard','favorites':'account_favorites','profile':'account_profile','login':'account_login','new_place':'owner_place_create','new_event':'owner_event_create','new_specialist':'owner_specialist_create','about':'about','faq':'faq_page','contacts':'contacts'}.items()}
                row.update(place=places[0].get_absolute_url(),place2=places[1].get_absolute_url(),foreign_place=places[2].get_absolute_url(),place_edit=reverse('owner_place_edit',args=[places[0].pk]),place2_edit=reverse('owner_place_edit',args=[places[1].pk]),foreign_edit=reverse('owner_place_edit',args=[places[2].pk]),
                    organization=reverse('organization_detail',args=[org.public_id]),org_edit=reverse('organization_workspace_detail',args=[org.pk]),program=reverse('organization_program_detail',args=[org.pk,program.pk]),activity=reverse('activity_detail',args=[linked[0].pk]),art=reverse('activity_detail',args=[art.pk]),unclassified=reverse('activity_detail',args=[unclassified.pk]),
                    specialist=person.get_absolute_url(),zero=zero.get_absolute_url(),unclaimed=unclaimed.get_absolute_url(),person_edit=reverse('specialist_workspace_profile',args=[person.pk]),person_certificates=reverse('specialist_workspace_certificates',args=[person.pk]),person_invitations=reverse('specialist_workspace_invitations',args=[person.pk]),claim=reverse('specialist_workspace_claims',args=[unclaimed.pk]),org_specialists=reverse('organization_specialists',args=[org.pk]),
                    review=reverse('typed_reviews',args=['place',places[0].pk]),moderation=reverse('admin:volunteer_review_index'),review_index=reverse('admin:volunteer_review_index'),map_api=reverse('public_map'),event_edit=reverse('owner_event_edit',args=[events['draft'].pk]))
                for key,e in events.items():row['event_'+key]=e.get_absolute_url()
                links[lang]=row
        result={'links':links,'roles':{k:{'username':v.username,'email':v.email} for k,v in users.items()},'password':'KidsMap-local-2026','seeded_at':now.isoformat(),'synthetic_only':True,
            'category_ids':{'education':'EDU','arts':'ART'},'subcategory_ids':{k:v[1].pk for k,v in categories.items()},'event_dates':{k:e.start_datetime.isoformat() for k,e in events.items()}}
    target.write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    (Path(__file__).resolve().parents[1]/'fixtures.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
