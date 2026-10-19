import sys,json
sys.argv=['runtime.py','subset-seed'];from runtime import *
from django.contrib.auth import get_user_model
from django.db import transaction,connection
from catalog.models import Specialist,SpecialistReview,WorkflowNotification,OwnerTeamInvitation,OwnerTeamMembership,OrganizationGrant,EmailOutbox
from catalog.services.review_versions import submit_review,moderate_candidate
assert settings.TESTING and settings.DATABASES['default']['NAME']=='m09full_r1'
U=get_user_model();assert not U.objects.filter(username__startswith='qa11_conflict_').exists()
def counts():return dict(notifications=WorkflowNotification.objects.count(),unread=WorkflowNotification.objects.filter(read_at__isnull=True).count(),outbox=EmailOutbox.objects.count(),memberships=OwnerTeamMembership.objects.count(),grants=OrganizationGrant.objects.count())
before=counts();target=Specialist.objects.create(name='Fictional QA11 conflict only',status='published',is_active=True)
moderator=U.objects.get(username='qa09_admin');cases={}
for lang in ['az','ru','en']:
 u=U.objects.create_user('qa11_conflict_'+lang,email='conflict11'+lang+'@example.invalid',first_name='Fictional QA11')
 h,r=submit_review(target=target,user=u,rating=4,text='QA11 PUBLIC C '+lang,author_name='Fictional QA11')
 moderate_candidate(head=h,revision_id=r.pk,actor=moderator,approve=True)
 cases[lang]={'user_id':u.pk,'head_id':h.pk,'current_revision_id':r.pk,'public_text':'QA11 PUBLIC C '+lang,'candidate_a':'QA11 CANDIDATE A '+lang,'draft_b':'QA11 DRAFT B '+lang}
recipient=U.objects.get(username='qa09_author');inv=OwnerTeamInvitation.objects.filter(email=recipient.email,status='CANCELED').first();assert inv
notice=WorkflowNotification.objects.get(event_kind='team_invitation',entity_type='place_team_invitation',entity_id=inv.pk,recipient_user=recipient)
data={'synthetic_only':True,'specialist_id':target.pk,'cases':cases,'revoked':{'notice_id':notice.pk,'invitation_id':inv.pk,'status':inv.status},'business_counts_before_seed':before,'business_counts_after_seed':counts()}
(QA/'subset-fixtures.json').write_text(json.dumps(data,indent=2));print(json.dumps({'seeded_owned_specialist':target.pk,'fictional_actors':3,'approved_public_heads':3,'revoked_notice':notice.pk,'business_counts_changed_by_seed':before!=counts()}))
