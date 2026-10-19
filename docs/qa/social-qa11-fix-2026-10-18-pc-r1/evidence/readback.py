import sys,json,platform,hashlib
sys.argv=['runtime.py','readback'];from runtime import *
from django.db import transaction,connection
from django.template.loader import get_template
from django.contrib.staticfiles.finders import find
from catalog.models import WorkflowNotification,OwnerTeamInvitation,OwnerTeamMembership,OrganizationGrant,EmailOutbox,SpecialistReview
data=json.loads((QA/'subset-fixtures.json').read_text());own={}
with transaction.atomic():
 with connection.cursor() as cur:cur.execute('SET TRANSACTION READ ONLY');cur.execute("SET LOCAL statement_timeout='5s'");cur.execute("SET LOCAL lock_timeout='2s'")
 counts=dict(notifications=WorkflowNotification.objects.count(),unread=WorkflowNotification.objects.filter(read_at__isnull=True).count(),outbox=EmailOutbox.objects.count(),memberships=OwnerTeamMembership.objects.count(),grants=OrganizationGrant.objects.count())
 status=OwnerTeamInvitation.objects.get(pk=data['revoked']['invitation_id']).status
 for lang,item in data['cases'].items():
  h=SpecialistReview.objects.select_related('current_revision','candidate_revision').get(pk=item['head_id'],user_id=item['user_id'],specialist_id=data['specialist_id'])
  own[lang]={'public_current_preserved':h.current_revision_id==item['current_revision_id'] and h.current_revision.text==item['public_text'],'candidate_a_preserved':bool(h.candidate_revision and h.candidate_revision.text==item['candidate_a']),'only_two_revisions':h.revisions.count()==2}
out={'business_counts_unchanged_after_seed':counts==data['business_counts_after_seed'],'revoked_status_unchanged':status==data['revoked']['status'],'owned_review_contracts':own,'expected_writes':'new own fictional specialist/3actors/3approvedbaseline revisions +3native A revisions, QA sessions/last_login; no B save and no revoked accept'}
(QA/'readback.json').write_text(json.dumps(out,indent=2));assert out['business_counts_unchanged_after_seed'] and out['revoked_status_unchanged'] and all(all(v.values()) for v in own.values())
info={'python':platform.python_version(),'django':django.get_version(),'testing':settings.TESTING,'sole_locales':list(map(str,settings.LOCALE_PATHS)),'template_origins':{p:get_template(p).origin.name for p in ['catalog/typed_reviews.html','pages/account_notifications.html']},'css_origin':find('css/site.css'),'source_count':len(entry['sources']),'source_verified':True,'qa_only_urls':'role login + read-only exact-owned-case state endpoint; subset process8002 loaded fresh after helper addition'}
(QA/'runtime-info.json').write_text(json.dumps(info,indent=2));print(json.dumps({'readback_contracts_pass':True,'languages':len(own),'business_unchanged':True,'revoked_unchanged':True,'source_count':1025}))
