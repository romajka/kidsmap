"""Initial fictional fixtures only; audited transitions use UI/HTTP."""
import sys,json
sys.argv=['run.py','qa-seed'];from run import *
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.utils import timezone
from django.db.migrations.recorder import MigrationRecorder
from datetime import timedelta
from catalog.models import *
from catalog.testcases.utils import create_ready_place
from PIL import Image
U=get_user_model();assert U.objects.count() in [0,9]
pw=(STATE/'credential').read_text();actors={}
for role in ['author','owner','employee','outsider','moderator','staff','admin','empty','invitee']:
 u=U.objects.filter(username='qa09_'+role).first() or U.objects.create_user('qa09_'+role,email=role+'09@example.invalid',password=pw,first_name='Fictional QA09',last_name=role,is_staff=role in ['moderator','staff','admin'],is_superuser=role=='admin')
 if role=='moderator':u.user_permissions.add(*Permission.objects.filter(content_type__app_label='catalog',codename__in=['view_placereview','change_placereview','view_specialistreview','change_specialistreview','view_activityreview','change_activityreview','view_eventreview','change_eventreview','view_sitereview','change_sitereview']))
 UserEmailVerification.objects.update_or_create(user=u,defaults={'email':u.email,'is_verified':True,'verified_at':timezone.now()})
 actors[role]=u
Image.new('RGB',(800,600),'#136F38').save(STATE/'assets/fixture.png')
media=Path(settings.MEDIA_ROOT)/'places/qa09.png';media.parent.mkdir(parents=True,exist_ok=True);media.write_bytes((STATE/'assets/fixture.png').read_bytes())
places={}
for label,status,active in [('live','published',True),('empty','published',True),('hidden','draft',True),('inactive','published',False),('archived','archived',True),('deleted','published',True),('foreign','published',True)]:
 owner=actors['outsider'] if label=='foreign' else actors['owner']
 p=Place.objects.filter(name='Fictional QA09 '+label).first() or create_ready_place(name='Fictional QA09 '+label,name_az='Uydurma QA09 '+label,name_ru='Вымышленное QA09 '+label,name_en='Fictional QA09 '+label,owner=owner,created_by=owner,status=status,is_active=active,photo='places/qa09.png',cover_photo='',description_az='Uydurma məkan. '*30,description_ru='Вымышленное место. '*30,description_en='Fictional place. '*30,deleted_at=timezone.now() if label=='deleted' else None)
 places[label]=p.pk
place=Place.objects.get(pk=places['live'])
OwnerTeamMembership.objects.create(place=place,owner=actors['owner'],member=actors['employee'],role='EDITOR',base_ownership_version=place.ownership_version,is_active=True)
act=Activity.objects.create(place=place,status='published',name_az='Uydurma QA09 fəaliyyət',description_az='Synthetic activity facts')
spec=Specialist.objects.create(owner=actors['owner'],created_by=actors['owner'],name='Fictional QA09 specialist',name_alt='Uydurma QA09 mütəxəssis',status='published',is_active=True,bio_az='Uydurma mütəxəssis. '*25)
event=Event.objects.create(owner=actors['owner'],name='Fictional QA09 event',name_az='Uydurma QA09 tədbir',category=place.category,status='published',event_format='online',start_datetime=timezone.now()+timedelta(days=5),end_datetime=timezone.now()+timedelta(days=5,hours=1),description_az='Uydurma tədbir. '*25)
site=SiteSettings.get_solo();site.events_section_enabled=site.organizations_section_enabled=site.specialists_section_enabled=True;site.save()
from catalog.services.review_versions import submit_review,moderate_candidate
for i in range(27):
 user=U.objects.create_user('qa09_filler'+str(i),email=f'filler{i}09@example.invalid')
 text=('SYNTHETIC '+str(i)+' '+'LongWord'*45+' <script>window.QA09_XSS=1</script> & <b>safe</b>\n'+('Fictional review. '*30)) if i==0 else 'Synthetic QA09 review '+str(i)
 head,rev=submit_review(target=place,user=user,rating=(i%5)+1,text=text,author_name='Synthetic Author '+str(i))
 moderate_candidate(head=head,revision_id=rev.pk,actor=actors['admin'],approve=True)
 SiteReview.objects.create(user=user,rating=(i%5)+1,text=text,author_name='Synthetic Author '+str(i),status='approved',is_approved=True)
for label in ['hidden','inactive','archived','deleted']:PlaceLike.objects.create(place_id=places[label],user=actors['author'])
for i in range(3):WorkflowNotification.objects.create(event_kind='moderation_decision',entity_type='volunteer_revision',entity_id=90000+i,entity_version=1,recipient_key='user:'+str(actors['author'].pk),recipient_user=actors['author'],recipient_email=actors['author'].email)
fixture={'actors':{r:{'id':u.pk,'username':u.username,'email':u.email} for r,u in actors.items()},'places':places,'activity':act.pk,'specialist':spec.pk,'event':event.pk,'synthetic_only':True}
(HERE/'fixtures.json').write_text(json.dumps(fixture,indent=2),encoding='utf-8')
(HERE/'isolation.json').write_text(json.dumps({'python':sys.version.split()[0],'django':django.get_version(),'testing':settings.TESTING,'db':'module09','db_port':'55440','cache':settings.CACHES['default'],'email':settings.EMAIL_BACKEND,'media':str(settings.MEDIA_ROOT),'private_media':str(settings.PRIVATE_MEDIA_ROOT),'migrations':MigrationRecorder.Migration.objects.count(),'external_integrations':False},indent=2))
print('Fresh synthetic initial fixtures created')
