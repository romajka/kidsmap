"""Own initial moderation queue, never touches existing stand data."""
import json
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group,Permission
from django.utils import timezone
from catalog.models import Organization
from catalog.services import volunteer_proposals
password=json.loads((SCRATCH/'credentials.json').read_text())['login_password'];User=get_user_model()
admin=User.objects.create_superuser('qa_mod01_admin','qa_mod01_admin@example.invalid',password)
reviewer=User.objects.create_user('qa_mod01_reviewer',email='qa_mod01_reviewer@example.invalid',password=password,is_staff=True)
reviewer.user_permissions.add(Permission.objects.get(content_type__app_label='catalog',codename='change_place'))
vol=User.objects.create_user('qa_mod01_volunteer',email='qa_mod01_volunteer@example.invalid',password=None,is_staff=True);group,_=Group.objects.get_or_create(name='KidsMap Volunteers');vol.groups.add(group)
empty_staff=User.objects.create_user('qa_mod01_bare_staff',email='qa_mod01_bare_staff@example.invalid',password=None,is_staff=True)
ids=[]
for i in range(1,36):
 org=Organization.objects.create(created_by=vol,owner=None,name_az=f'QA Moderation {i:02d}',name_ru=f'QA очередь {i:02d}',name_en=f'QA Queue {i:02d}')
 revision=volunteer_proposals.propose(actor=vol,kind='organization',target_id=org.pk,patch={'description_az':f'Fictional local candidate {i:02d}'},expected_version=org.content_version,revision_version=0,submit=i<=32)
 ids.append(revision.pk)
(HERE/'fixtures.json').write_text(json.dumps({'actors':{'admin':admin.username,'reviewer':reviewer.username},'author_id':vol.pk,'pending':32,'draft':3,'date':timezone.now().date().isoformat(),'revision_ids':ids,'setup':'initial fictional queue; native login and read-only UI navigation are checked separately'},indent=2))
print(json.dumps({'pending':32,'draft':3,'own_users':4}))
