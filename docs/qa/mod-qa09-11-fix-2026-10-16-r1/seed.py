"""Initial synthetic states only; audited decisions use UI/HTTP."""
import sys,json
from django.conf import settings
STATE=SCRATCH
(STATE/'assets').mkdir(exist_ok=True)
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission,Group
from django.core.files.base import ContentFile
from django.db.migrations.recorder import MigrationRecorder
from django.utils import timezone
from datetime import timedelta
from catalog.models import *
from catalog.services.staff_roles import VOLUNTEER_GROUP,ADMIN_ROLE_PERMISSION_PRESETS
from catalog.services import publication
from catalog.testcases.utils import create_ready_place
from PIL import Image
pw=json.loads((STATE/'credentials.json').read_text())['login_password'];actors={};U=get_user_model();assert U.objects.count()==0
for role in ['owner','outsider','volunteer','volunteer_b','moderator','reviewer','reviewer_b','staff','admin']:
 u=U.objects.create_user('qa0911_'+role,email=role+'08@example.invalid',password=pw,first_name='Fictional QA0911',last_name=role,is_staff=role not in ['owner','outsider'],is_superuser=role=='admin')
 if role.startswith('volunteer'):u.groups.add(Group.objects.get_or_create(name=VOLUNTEER_GROUP)[0])
 if role=='moderator':u.user_permissions.add(*Permission.objects.filter(content_type__app_label='catalog',codename__in=ADMIN_ROLE_PERMISSION_PRESETS['moderator']))
 if role.startswith('reviewer'):u.user_permissions.add(*Permission.objects.filter(content_type__app_label='catalog',codename__in=['view_place','change_place','view_organization','view_event','change_event','view_specialist','change_specialist']))
 UserEmailVerification.objects.update_or_create(user=u,defaults={'email':u.email,'is_verified':True,'verified_at':timezone.now()})
 actors[role]=u
for key,col in [('live','#136F38'),('candidate','#abc4e5'),('gallery','#d4a591')]:
 Image.new('RGB',(800,600),col).save(STATE/f'assets/{key}.png')
 media=Path(settings.MEDIA_ROOT)/f'places/qa0911-{key}.png';media.parent.mkdir(parents=True,exist_ok=True);media.write_bytes((STATE/f'assets/{key}.png').read_bytes())
places={};revs={}
def initial_revision(kind,obj,author,patch,status='pending',version=1,conflict=False):
 base=publication.snapshot(obj,kind)
 if conflict:base['name_az']='Stale synthetic source'
 return VolunteerPlaceRevision.objects.create(**{kind:obj},author=author,payload=patch,base_snapshot=base,dependencies=publication.dependencies(obj,kind),changed_fields=sorted(patch),base_content_version=obj.content_version,status=status,version=version)
for label,role,status in [('live','owner','published'),('batch_ready','owner','draft'),('volunteer','volunteer','published'),('foreign','volunteer_b','draft'),('revoke','volunteer','published'),('delete','volunteer','draft')]:
 p=create_ready_place(name='Fictional QA0911 '+label,name_az='Uydurma QA0911 '+label,name_ru='Вымышленное QA0911 '+label,name_en='Fictional QA0911 '+label,created_by=actors[role],owner=None if role.startswith('volunteer') else actors[role],status=status,is_active=status=='published',photo='places/qa0911-live.png',cover_photo='',city='baku',district='baku_yasamal',description_az='Uydurma məkan. '*30,description_ru='Вымышленное место. '*30,description_en='Fictional place. '*30)
 places[label]=p.pk
 if label in ['live','revoke']:
  rev=initial_revision('place',p,actors[role],{'name_az':'Uydurma QA0911 candidate '+label,'photo':'places/qa0911-candidate.png','gallery':[{'id':None,'image':'places/qa0911-gallery.png','caption':'Fictional gallery','order':0}]});revs[label]=rev.pk
bad=Place.objects.create(name='Fictional QA0911 incomplete',name_az='Uydurma QA0911 incomplete',category_id='EDU',owner=actors['owner'],created_by=actors['owner'],status='draft',is_active=False);places['batch_bad']=bad.pk
orgs={}
for n in range(32):
 label='flow' if n==0 else 'reject' if n==1 else 'conflict' if n==2 else 'filler'+str(n)
 org=Organization.objects.create(created_by=actors['volunteer'],owner=None,name_az='Uydurma QA0911 '+label+(' '+('Uzunad'*18) if n==3 else ''),description_az='Initial synthetic organization',status='draft')
 rev=initial_revision('organization',org,actors['volunteer'],{'name_az':'Uydurma QA0911 candidate '+label,'description_az':'Candidate synthetic '+label},conflict=n==2)
 orgs[label]=org.pk;revs[label]=rev.pk
event=Event.objects.create(name='Fictional QA0911 event',name_az='Uydurma QA0911 event',name_ru='Вымышленное QA0911 событие',name_en='Fictional QA0911 event',category_id='EDU',organizer_organization=Organization.objects.get(pk=orgs['flow']),organizer_resolution='resolved',owner=actors['owner'],status='pending',event_format='online',start_datetime=timezone.now()+timedelta(days=3),end_datetime=timezone.now()+timedelta(days=3,hours=2),description_az='Uydurma tədbir. '*30,photo='places/qa0911-live.png')
spec=Specialist.objects.create(name='Fictional QA0911 Specialist',name_alt='Uydurma QA0911 mütəxəssis',owner=actors['owner'],created_by=actors['owner'],status='pending',bio_az='Uydurma mütəxəssis. '*30,consultation_format='online')
doc=SpecialistDocument.objects.create(specialist=spec,document_type='identity',name='SYNTHETIC QA0911 private',file=ContentFile(b'SYNTHETIC QA0911 FILE',name='qa0911-private.pdf'))
direction=SpecialistSpecialization.objects.first();spec.specializations.add(direction)
spec.photo='places/qa0911-live.png';spec.save(update_fields=['photo'])
site=SiteSettings.get_solo();site.events_section_enabled=site.organizations_section_enabled=site.specialists_section_enabled=True;site.save()

from catalog.services import volunteer_proposals
notes={}
reason='QA <img src=x onerror=alert(1)> & "quoted"\n' + 'LongReason' * 60
for action in ('approve','return','reject'):
 org=Organization.objects.create(created_by=actors['volunteer'],name_az='QA Decision '+action)
 rev=volunteer_proposals.propose(actor=actors['volunteer'],kind='organization',target_id=org.pk,patch={'description_az':'QA candidate'},expected_version=org.content_version,revision_version=0,submit=True)
 if action=='approve':rev=publication.review(actor=actors['admin'],revision_id=rev.pk,version=rev.version,approve=True,note=reason)
 else:rev=volunteer_proposals.review(actor=actors['admin'],revision_id=rev.pk,version=rev.version,action=action,reason=reason)
 notes[action]=rev.pk
for i in (1,2):
 name=f'QA Copy Pair {i}'
 Place.objects.create(name=name,name_az=name,name_ru=name,name_en=name,category_id='EDU',created_by=actors['admin'],status='draft')
 Event.objects.create(name=name,name_az=name,name_ru=name,name_en=name,category_id='EDU',start_datetime=timezone.now()+timedelta(days=3),status='draft')
 Specialist.objects.create(name=name,status='draft')
edge=create_ready_place(name='QA <img src=x onerror=alert(1)> "$&" listing',name_az='QA <img src=x onerror=alert(1)> "$&" listing',name_ru='QA <img src=x onerror=alert(1)> "$&" listing',name_en='QA <img src=x onerror=alert(1)> "$&" listing',created_by=actors['owner'],owner=actors['owner'],status='published',is_active=True,photo='places/qa0911-live.png',cover_photo='',city='baku',district='baku_yasamal',description_az='Uydurma məkan. '*30,description_ru='Вымышленное место. '*30,description_en='Fictional place. '*30)
places['edge']=edge.pk
fixture={'actors':{r:{'id':u.pk,'username':u.username,'email':u.email}for r,u in actors.items()},'places':places,'organizations':orgs,'revisions':revs,'notes':notes,'reason':reason,'event':event.pk,'specialist':spec.pk,'private_document':doc.pk,'synthetic_only':True}
(HERE/'fixtures.json').write_text(json.dumps(fixture,indent=2),encoding='utf-8')
print('Own synthetic actors, publication listings, count pairs and canonical terminal decisions created')
