import sys,json,io,hashlib
from pathlib import Path
sys.argv=['runtime.py','seed-own'];from runtime import *
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.core.files.base import ContentFile
from django.utils import timezone,translation
from django.urls import reverse
from datetime import timedelta
from PIL import Image,ImageDraw
from catalog.models import SiteSettings,CatalogContentSettings,Place,Organization,Program,Activity,Specialist,Event,SiteGalleryImage
from catalog.services import organization_ownership
from catalog.testcases.utils import create_ready_place
assert get_user_model().objects.count()==0 and Place.objects.count()==0
actors={}
for role,staff,superuser in [('admin',True,True),('owner',False,False),('viewer',True,False),('denied',True,False)]:
 user=get_user_model().objects.create_user('m12_'+role,email=role+'@example.invalid',password='fictional-only',is_staff=staff,is_superuser=superuser);actors[role]=user
 if role=='viewer':user.user_permissions.add(Permission.objects.get(content_type__app_label='catalog',codename='view_siteanalytics'))
site=SiteSettings.get_solo();site.brand_name='KidsMap SEO QA';site.footer_email='seo-qa@example.invalid';site.events_section_enabled=site.organizations_section_enabled=site.specialists_section_enabled=True
img=Image.new('RGB',(800,600),'#17734e');ImageDraw.Draw(img).text((30,30),'FICTIONAL MODULE11 PHOTO',fill='white');out=io.BytesIO();img.save(out,format='PNG');data=out.getvalue();(QA/'assets/event-photo.png').write_bytes(data);site.logo.save('m11-logo.png',ContentFile(data),save=False);site.save();CatalogContentSettings.get_solo()
texts={f'{field}_{lang}':f'M12 {field} {lang} '+('Own public description. '*12 if field=='description' else '') for field in ['name','description'] for lang in ['az','ru','en']};owner=actors['owner'];now=timezone.now()
place=create_ready_place(owner=owner,created_by=owner,**texts);place.photo.save('m11-place.png',ContentFile(data));org=Organization.objects.create(owner=owner,created_by=owner,status='published',approved_at=now,**texts);organization_ownership.request_join(actor=owner,place_id=place.pk,organization_id=org.pk);place.refresh_from_db();program=Program.objects.create(organization=org,status='published',approved_at=now,**texts);activity=Activity.objects.create(place=place,program=program,status='published')
spec=Specialist.objects.create(name='M12 Fictional Specialist',name_alt='M12 Specialist alternate',owner=owner,created_by=owner,status='published',is_active=True,consultation_format='online',**{'bio_'+l:'M12 biography '+l+' '+('Own specialist public text. '*10) for l in ['az','ru','en']});spec.photo.save('m11-specialist.png',ContentFile(data));event=Event.objects.create(name='M12 Event',owner=owner,status='published',category=place.category,event_format='online',start_datetime=now+timedelta(days=5),end_datetime=now+timedelta(days=5,hours=1),phone='+994501112233',organizer_organization=org,**texts);event.photo.save('m11-event.png',ContentFile(data))
for row in SiteGalleryImage.objects.all():row.is_active=False;row.save(update_fields=['is_active'])
ids={'place':place.pk,'organization':org.pk,'program':program.pk,'activity':activity.pk,'specialist':spec.pk,'event':event.pk};(QA/'fixtures.json').write_text(json.dumps(ids,indent=2));print('Own fresh fictional module12 actors and public fixtures seeded; no production records.')
