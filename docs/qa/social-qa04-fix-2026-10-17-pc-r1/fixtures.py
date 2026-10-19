import json
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from catalog.models import Organization, WorkflowNotification
from catalog.services import business_team, organization_ownership
from catalog.services.workflow_notifications import emit
from catalog.testcases.utils import create_quality_place

STATES=('empty','unread','read','invitation','revoked','expired')
def seed():
    with transaction.atomic():
        U=get_user_model()
        assert not U.objects.exists()
        owner=U.objects.create_user('s04-owner',email='owner@example.invalid',first_name='Fictional')
        cases=[]
        def user(key,staff=False):
            return U.objects.create_user('s04-'+key,email=key+'@example.invalid',first_name='Fictional',is_staff=staff)
        def notice(recipient,index):
            return emit(kind='moderation_decision',entity_type='fictional_fixture',entity_id=index,version=1,recipient_user=recipient,email=False)
        def invite(recipient,key,kind='place',status=None):
            if kind=='place':target=create_quality_place(owner=owner,created_by=owner,with_subcategory=True)
            else:target=Organization.objects.create(owner=owner,created_by=owner,name_az='Fictional organization '+key)
            opts={'scope':'all_network','place_ids':[]} if kind=='organization' else {}
            row=business_team.invite(actor=owner,target_type=kind,target_id=target.pk,email=recipient.email,**opts)
            if status=='revoked':
                business_team.decide_invitation(actor=owner,target_type=kind,invitation_id=row.pk,cancel=True)
            elif status=='expired':
                type(row).objects.filter(pk=row.pk).update(expires_at=timezone.now()-timedelta(days=1))
            n=WorkflowNotification.objects.get(event_kind='team_invitation',entity_type=kind+'_team_invitation',entity_id=row.pk,recipient_user=recipient)
            return row,n
        for index,key in enumerate(STATES):
            recipient=user(key)
            if key in ('unread','read'):
                n=notice(recipient,index+1)
                if key=='read':
                    n.read_at=timezone.now();n.save(update_fields=['read_at'])
            if key in ('invitation','revoked','expired'):
                for kind in ('place','organization'):invite(recipient,key,kind,key)
            cases.append({'key':key,'username':recipient.username,'role':'recipient','state':key})
        for lang in ('ru','az','en'):
            for action in ('mark_read','accept_place','accept_org','decline_place','decline_org','join','invalid400','stale409','loading','transport'):
                key=lang+'-'+action;recipient=user(key)
                case={'key':key,'username':recipient.username,'role':'recipient','lang':lang,'action':action}
                if action in ('mark_read','loading','transport'):
                    case['notice_id']=notice(recipient,100+len(cases)).pk
                elif action=='join':
                    place=create_quality_place(owner=owner,created_by=owner,with_subcategory=True)
                    org=Organization.objects.create(owner=recipient,created_by=recipient,name_az='Fictional join '+lang)
                    join=organization_ownership.request_join(actor=owner,place_id=place.pk,organization_id=org.pk)
                    n=WorkflowNotification.objects.get(event_kind='join_confirmation',entity_id=join.pk,recipient_user=recipient)
                    case.update(notice_id=n.pk,join_id=join.pk,org_id=org.pk)
                else:
                    kind='organization' if action.endswith('_org') else 'place'
                    row,n=invite(recipient,key,kind)
                    case.update(notice_id=n.pk,invitation_id=row.pk,kind=kind)
                cases.append(case)
        recipient=user('role-owner')
        org=Organization.objects.create(owner=recipient,created_by=recipient,name_az='Fictional owner workspace')
        create_quality_place(owner=recipient,created_by=recipient,with_subcategory=True)
        notice(recipient,900)
        cases.append({'key':'role-owner','username':recipient.username,'role':'owner','org_id':org.pk})
        recipient=user('role-staff',staff=True);notice(recipient,901)
        cases.append({'key':'role-staff','username':recipient.username,'role':'staff'})
        recipient=user('outsider')
        cases.append({'key':'outsider','username':recipient.username,'role':'outsider'})
        (settings.QA_ROOT/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
    print('Seeded six matrix states,30independent language/action fixtures and owner/staff/outsider; only fictional DB')
