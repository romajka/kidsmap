import json
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from catalog.models import Organization, WorkflowNotification
from catalog.services import business_team
from catalog.services.workflow_notifications import emit
from catalog.testcases.utils import create_quality_place

STATES = ('empty', 'unread', 'read', 'invitation', 'revoked', 'expired')

def seed():
    with transaction.atomic():
        U = get_user_model()
        assert not U.objects.exists(), 'Fresh owned DB only'
        owner = U.objects.create_user('s04-owner', email='owner@example.invalid', first_name='Fictional')
        cases = []
        for index, state in enumerate(STATES):
            user = U.objects.create_user('s04-'+state, email=state+'@example.invalid', first_name='Fictional')
            if state in ('unread', 'read'):
                notice = emit(kind='moderation_decision', entity_type='fictional_fixture',
                    entity_id=index+1, version=1, recipient_user=user, email=False)
                if state == 'read':
                    notice.read_at = timezone.now()
                    notice.save(update_fields=['read_at'])
            if state in ('invitation', 'revoked', 'expired'):
                place = create_quality_place(owner=owner, created_by=owner, with_subcategory=True)
                org = Organization.objects.create(owner=owner, created_by=owner, name_az='Fictional organization '+state)
                for kind, target in [('place', place), ('organization', org)]:
                    opts = {'scope':'all_network','place_ids':[]} if kind == 'organization' else {}
                    invite = business_team.invite(actor=owner, target_type=kind, target_id=target.pk, email=user.email, **opts)
                    if state == 'revoked':
                        business_team.decide_invitation(actor=owner, target_type=kind, invitation_id=invite.pk, cancel=True)
                    elif state == 'expired':
                        type(invite).objects.filter(pk=invite.pk).update(expires_at=timezone.now()-timedelta(days=1))
            cases.append({'state':state,'role':'recipient','rows':WorkflowNotification.objects.filter(recipient_user=user).count()})
        (settings.QA_ROOT/'cases.json').write_text(json.dumps(cases,indent=2)+'\n')
    print('Seeded six fictional inbox states; place/org invitations real services; initial expired fixtures explicit')
