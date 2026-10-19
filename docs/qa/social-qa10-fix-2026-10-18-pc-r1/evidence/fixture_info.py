import sys,json,hashlib,platform
sys.argv=['runtime.py','fixture-info'];from runtime import *
from django.db import transaction,connection
from django.contrib.auth import get_user_model
from django.template.loader import get_template
from catalog.models import WorkflowNotification,OwnerTeamInvitation,OwnerTeamMembership,OrganizationGrant,EmailOutbox
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'");c.execute('SHOW server_version');pg=c.fetchone()[0]
 cases=[]
 for lang,role in [('az','author'),('ru','owner'),('en','invitee')]:
  u=get_user_model().objects.get(username='qa09_'+role);assert u.is_active and u.email.endswith('@example.invalid')
  foreign=WorkflowNotification.objects.exclude(recipient_user=u).filter(recipient_user__isnull=False).first();assert foreign
  cases.append(dict(lang=lang,role=role,email=u.email,user_id=u.pk,foreign_notice_id=foreign.pk))
 recipient=get_user_model().objects.get(username='qa09_author');invite=OwnerTeamInvitation.objects.filter(email=recipient.email,status='CANCELED').first();assert invite
 revoked=WorkflowNotification.objects.get(event_kind='team_invitation',entity_type='place_team_invitation',entity_id=invite.pk,recipient_user=recipient)
 counts=dict(notifications=WorkflowNotification.objects.count(),unread=WorkflowNotification.objects.filter(read_at__isnull=True).count(),outbox=EmailOutbox.objects.count(),memberships=OwnerTeamMembership.objects.count(),grants=OrganizationGrant.objects.count())
 snapshots=dict(cases=cases,revoked=dict(notice_id=revoked.pk,invitation_id=invite.pk,recipient=recipient.email,status=invite.status),business_counts=counts)
(QA/'fixture-info.json').write_text(json.dumps(snapshots,indent=2))
info=dict(python=platform.python_version(),django=django.get_version(),postgresql=pg,testing=settings.TESTING,normal_db='owned fictional full-audit QA database',test_db=settings.DATABASES['default']['TEST']['NAME'],sole_locales=list(map(str,settings.LOCALE_PATHS)),media=str(settings.MEDIA_ROOT),private_media=str(settings.PRIVATE_MEDIA_ROOT),email_backend=settings.EMAIL_BACKEND,source_files=len(entry['sources']),source_verified=True,template=get_template('auth/login.html').origin.name,controller_sha256=hashlib.sha256((ROOT/'src/catalog/controllers/workflow_notifications.py').read_bytes()).hexdigest())
(QA/'runtime-info.json').write_text(json.dumps(info,indent=2));print('Own synthetic actor/foreign/revoked IDs and aggregate-only baseline recorded; current source1025/MO/runtime verified')
