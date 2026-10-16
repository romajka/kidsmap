"""Initial synthetic fixture only; all candidate states via canonical publication service."""
import io,json,hashlib
from PIL import Image,ImageDraw
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group,Permission
from django.core.files.base import ContentFile
from catalog.models import Place,PlacePhoto
from catalog.services import volunteer_proposals,publication
from catalog.testcases.utils import create_ready_place
password=json.loads((SCRATCH/'credentials.json').read_text())['login_password'];User=get_user_model()
admin=User.objects.create_superuser('qa_mod02_admin','qa_mod02_admin@example.invalid',password)
reviewer=User.objects.create_user('qa_mod02_reviewer',email='qa_mod02_reviewer@example.invalid',password=password,is_staff=True)
reviewer.user_permissions.add(Permission.objects.get(content_type__app_label='catalog',codename='change_place'))
vol=User.objects.create_user('qa_mod02_volunteer',email='qa_mod02_volunteer@example.invalid',password=password,is_staff=True);group,_=Group.objects.get_or_create(name='KidsMap Volunteers');vol.groups.add(group)
bare=User.objects.create_user('qa_mod02_bare',email='qa_mod02_bare@example.invalid',password=password,is_staff=True)
media={};storage=Place._meta.get_field('photo').storage
for side in ('live','candidate'):
 for n,role in enumerate(('main','cover','gallery-1','gallery-2')):
  im=Image.new('RGB',(720,480),('#185e41' if side=='live' else '#2866a4'));ImageDraw.Draw(im).text((55,90),f'FICTIONAL QA {side.upper()} {role.upper()}',fill='white',stroke_width=1)
  buf=io.BytesIO();im.save(buf,format='WEBP');name=storage.save(f'places/mod02-{side}-{role}.webp',ContentFile(buf.getvalue()));media[side+'-'+role]=name
place=create_ready_place(created_by=vol,owner=None,name='Fictional QA media review',name_az='QA media review',photo=media['live-main'],cover_photo=media['live-cover'])
for n in (1,2):PlacePhoto.objects.create(place=place,image=media[f'live-gallery-{n}'],caption=f'Fictional current gallery {n}',order=n)
patch={'photo':media['candidate-main'],'cover_photo':media['candidate-cover'],'gallery':[{'id':None,'image':media['candidate-gallery-2'],'caption':'Fictional proposed second','order':2},{'id':None,'image':media['candidate-gallery-1'],'caption':'Fictional proposed first','order':1}]}
revision=volunteer_proposals.propose(actor=vol,kind='place',target_id=place.pk,patch=patch,expected_version=place.content_version,revision_version=0,submit=False)
draft_version=revision.version
revision=volunteer_proposals.propose(actor=vol,kind='place',target_id=place.pk,patch=patch,expected_version=place.content_version,revision_version=revision.version,submit=True)
assert revision.status=='pending' and set(revision.changed_fields)==set(patch)
assert publication.snapshot(place,'place')['photo']==media['live-main']
(HERE/'fixtures.json').write_text(json.dumps({'actors':{'admin':admin.username,'reviewer':reviewer.username,'volunteer':vol.username,'bare':bare.username},'place_id':place.pk,'revision_id':revision.pk,'candidate_version':revision.version,'draft_version':draft_version,'changed_fields':revision.changed_fields,'media':media,'setup':'initial synthetic files/live place, canonical service draft then submit. Native author upload flow NOT RUN in PLAN; required after approved patch.'},indent=2))
print(json.dumps({'users':4,'places':1,'pending':1,'media_files':len(media),'candidate_version':revision.version}))
# Additional initial fixtures; user actions below are reserved for real browser.
from django.utils import timezone
from catalog.models import UserEmailVerification,Organization,Program,Specialist,SpecialistDocument,SiteSettings
owner=User.objects.create_user('qa_mod02_owner',email='qa_mod02_owner@example.invalid',password=password)
for actor in (owner,admin,reviewer,vol,bare):
 UserEmailVerification.objects.update_or_create(user=actor,defaults={'email':actor.email,'is_verified':True,'verified_at':timezone.now()})
created=[]
def live_place(tag,actor=vol,owned=False):
 p=create_ready_place(created_by=actor,owner=actor if owned else None,name='Fictional QA '+tag,name_az='QA '+tag,photo=media['live-main'],cover_photo=media['live-cover'])
 for n in (1,2):PlacePhoto.objects.create(place=p,image=media[f'live-gallery-{n}'],caption=f'Current {n}',order=n)
 created.append(p.pk);return p
cases=[]
for lang in ('ru','az','en'):
 for width in (390,1440):
  for action in ('approve','reject'):
   p=live_place(f'{action}-{lang}-{width}');r=volunteer_proposals.propose(actor=vol,kind='place',target_id=p.pk,patch=patch,expected_version=p.content_version,revision_version=0,submit=True)
   cases.append({'lang':lang,'width':width,'action':action,'place_id':p.pk,'revision_id':r.pk,'name':p.name_az,'public_path':p.get_absolute_url()})
edges=[]
for kind in ('empty','missing','corrupt','caption'):
 p=live_place('edge-'+kind);v=dict(patch)
 if kind=='empty':v={'photo':'','cover_photo':'','gallery':[]}
 if kind in ('missing','corrupt'):
  value=storage.save(f'places/mod02-{kind}.webp',ContentFile((SCRATCH/'media'/media['candidate-main']).read_bytes()));v['photo']=value
 if kind=='caption':
  v['gallery']=[dict(row,caption=('QA long caption <img src=x onerror=alert(1)> & AZ RU EN '*4)[:240])for row in patch['gallery']]
 r=volunteer_proposals.propose(actor=vol,kind='place',target_id=p.pk,patch=v,expected_version=p.content_version,revision_version=0,submit=True)
 if kind=='missing':storage.delete(v['photo'])
 if kind=='corrupt':(SCRATCH/'media'/v['photo']).write_bytes(b'SIMULATED damaged raster, not an image')
 edges.append({'kind':kind,'place_id':p.pk,'revision_id':r.pk,'media_name':v.get('photo','')})
flows={}
for role,actor,owned in [('owner',owner,True),('volunteer',vol,False)]:
 p=live_place('native-'+role,actor,owned);flows[role]={'place_id':p.pk,'editor_path':f'/ru/account/places/{p.pk}/edit/'if owned else f'/ru/admin/volunteer/{p.pk}/edit/','name':p.name_az,'public_path':p.get_absolute_url()}
# Native text-only comparison consumers.
org=Organization.objects.create(created_by=vol,owner=None,name_az='QA shared text organization')
orgrev=volunteer_proposals.propose(actor=vol,kind='organization',target_id=org.pk,patch={'description_az':'QA plain organization text <b>must stay escaped</b>'},expected_version=org.content_version,revision_version=0,submit=True)
program=Program.objects.create(created_by=vol,organization=org,name_az='QA shared text program')
programrev=volunteer_proposals.propose(actor=vol,kind='program',target_id=program.pk,patch={'description_az':'QA plain program text'},expected_version=program.content_version,revision_version=0,submit=True)
link=volunteer_proposals.submit_informational_link(actor=vol,place_id=place.pk,organization_id=org.pk)
profile=Specialist.objects.create(name='QA fictional private document owner',owner=owner,created_by=owner,verified_person_user=owner,person_verified_at=timezone.now(),status='published',is_active=True)
doc=SpecialistDocument(specialist=profile,document_type='identity',name='QA PRIVATE ONLY',is_published=False);doc.file.save('qa-private.png',ContentFile((SCRATCH/'media'/media['live-main']).read_bytes()),save=True)
site=SiteSettings.get_solo();site.specialists_section_enabled=True;site.save()
f=json.loads((HERE/'fixtures.json').read_text());f.update(actors={**f['actors'],'owner':owner.username},decision_cases=cases,edge_cases=edges,author_flows=flows,private_document_id=doc.pk,shared_details=[{'source':'content','id':orgrev.pk,'text':'QA plain organization text'},{'source':'content','id':programrev.pk,'text':'QA plain program text'},{'source':'affiliation','id':link.pk,'text':'QA shared text organization'}],setup='Own initial fictional verified accounts; canonical seeded revisions and deliberately damaged own edge media. Native author uploads/decisions still required.')
(HERE/'fixtures.json').write_text(json.dumps(f,indent=2))
print(json.dumps({'own_decision_cases':len(cases),'own_edge_cases':len(edges),'native_author_fixtures':list(flows),'shared_cases':3,'private_document':1}))
