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
