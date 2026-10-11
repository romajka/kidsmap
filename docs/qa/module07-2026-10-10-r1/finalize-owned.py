"""SIMULATED clock; call canonical processor only for UI-confirmed own fixtures."""
from pathlib import Path
import sys, runpy, json
from datetime import timedelta
P=Path(__file__).resolve().parent
sys.argv=[str(P/'run.py'),'init']
runpy.run_path(str(P/'run.py'),run_name='qa_init')
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction,connection
from catalog.models import AccountDeletionRequest, Place, Specialist, SpecialistDocument, UserProfile, UserEmailVerification, OwnerTeamInvitation, OrganizationTeamInvitation, WorkflowNotification, EmailOutbox
from catalog.services.account_deletion import finalize_account_deletion
assert settings.TESTING and settings.DATABASES['default']['NAME']=='module07'
F=json.loads((P/'fixtures.json').read_text())
rows=[]
for role in ['delete_final','person']:
 uid=F['actors'][role]['id']
 deletion=AccountDeletionRequest.objects.filter(user_id=uid,status='SCHEDULED').latest('pk')
 assert get_user_model().objects.get(pk=uid).email.endswith('@example.invalid')
 assert deletion.scheduled_for is not None
 def snapshot():
  with transaction.atomic():
   with connection.cursor() as cur:
    cur.execute('SET TRANSACTION READ ONLY');cur.execute("SET LOCAL statement_timeout='10s'");cur.execute("SET LOCAL lock_timeout='2s'")
   return {'user_exists':get_user_model().objects.filter(pk=uid).exists(),'profiles':UserProfile.objects.filter(user_id=uid).count(),'verification':UserEmailVerification.objects.filter(user_id=uid).count(),'owned_places':Place.objects.filter(owner_id=uid).count(),'verified_specialists':Specialist.objects.filter(verified_person_user_id=uid).count(),'consented_documents':SpecialistDocument.objects.filter(opted_in_by_id=uid).count(),'documents_total':SpecialistDocument.objects.count(),'private_fixture_files_existing':sum((Path(settings.PRIVATE_MEDIA_ROOT)/d['path']).is_file() for d in F['documents'].values()),'place_invitations_to_fixture':OwnerTeamInvitation.objects.filter(email=F['actors'][role]['email']).count(),'organization_invitations_to_fixture':OrganizationTeamInvitation.objects.filter(email=F['actors'][role]['email']).count(),'notification_emails_retained':WorkflowNotification.objects.filter(recipient_email=F['actors'][role]['email']).count(),'outbox_emails_retained':EmailOutbox.objects.filter(recipient_email=F['actors'][role]['email']).count()}
 before=snapshot();early=finalize_account_deletion(deletion.pk);after_early=snapshot()
 rows.append({'id':'processor-before-deadline-no-change','role':role,'lang':'N/A service','width':'N/A service','status':'PASS' if early.outcome=='skipped' and before==after_early else 'FAIL','classification':'Actual current clock; canonical service','before':before,'after':after_early})
 future=deletion.scheduled_for+timedelta(seconds=1)
 result=finalize_account_deletion(deletion.pk,now=future)
 after=snapshot();deletion.refresh_from_db()
 rows.append({'id':'processor-after-deadline-simulated','role':role,'lang':'N/A service','width':'N/A service','status':'PASS' if result.outcome=='completed' and deletion.status=='COMPLETED' and not after['user_exists'] and after['profiles']==0 and after['verification']==0 and after['owned_places']==0 and after['verified_specialists']==0 and after['consented_documents']==0 else 'FAIL','classification':'SIMULATED future clock and retention policy; canonical service, no ORM transition','before':before,'after':after,'processor_counters':result.counters,'simulated_date':future.isoformat()})
 repeat=finalize_account_deletion(deletion.pk,now=future)
 rows.append({'id':'processor-completed-repeat-idempotent','role':role,'lang':'N/A service','width':'N/A service','status':'PASS' if repeat.outcome=='completed' and after==snapshot() and not repeat.counters else 'FAIL','classification':'SIMULATED future clock'})
(P/'finalize-owned.result.json').write_text(json.dumps({'rows':rows},indent=2),encoding='utf-8')
print('Own canonical processor observations',len(rows),'PASS',sum(x['status']=='PASS' for x in rows))
sys.exit(int(any(x['status']=='FAIL' for x in rows)))
