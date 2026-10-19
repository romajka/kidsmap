import sys,json
sys.argv=['runtime.py','extra-fixtures'];from runtime import *
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from catalog.models import Organization,UserEmailVerification,WorkflowNotification,EmailOutbox
from catalog.services import business_team
from catalog.testcases.utils import create_ready_place
U=get_user_model();assert not U.objects.filter(username__startswith='accept09-extra-').exists()
cases=[]
with transaction.atomic():
 owner=U.objects.get(username='qa09_owner')
 for kind in ['place','organization']:
  for lang in ['ru','az','en']:
   key=kind+'-'+lang;u=U.objects.create_user('accept09-extra-'+key,email=key+'-accept09@example.invalid',password='<fictional-local-password>')
   UserEmailVerification.objects.update_or_create(user=u,defaults={'email':u.email,'is_verified':True,'verified_at':timezone.now()})
   target=create_ready_place(owner=owner,created_by=owner,name='Fictional acceptance '+key) if kind=='place' else Organization.objects.create(owner=owner,created_by=owner,name_az='Fictional acceptance '+key)
   inv=business_team.invite(actor=owner,target_type=kind,target_id=target.pk,email=u.email,**({'scope':'all_network'} if kind=='organization' else {}))
   notice=WorkflowNotification.objects.get(event_kind='team_invitation',entity_type=kind+'_team_invitation',entity_id=inv.pk)
   cases.append(dict(key=key,kind=kind,lang=lang,email=u.email,user_id=u.pk,target_id=target.pk,invitation_id=inv.pk,notice_id=notice.pk))
(QA/'extra-cases.json').write_text(json.dumps({'cases':cases,'outbox_before':EmailOutbox.objects.count()},indent=2));print('Six fresh initial fictional invitation cases, UI transitions not executed')

