"""SOCIAL08 regression candidate; run from ignored scratch before approval."""
from datetime import timedelta
from django.contrib.auth import get_user_model
from django.db.models import F
from django.test import Client,TestCase
from django.urls import reverse
from django.utils import timezone
from catalog.models import Organization,WorkflowNotification,OwnerTeamMembership,OrganizationGrant,EmailOutbox
from catalog.services import business_team
from catalog.testcases.utils import create_ready_place

class SocialQA08InvitationFeedbackTests(TestCase):
    def setUp(self):
        U=get_user_model()
        self.owner=U.objects.create_user('s08-owner',email='owner@example.invalid')
        self.recipient=U.objects.create_user('s08-recipient',email='recipient@example.invalid')
        self.other=U.objects.create_user('s08-other',email='other@example.invalid')
        self.place=create_ready_place(owner=self.owner,created_by=self.owner,name='Fictional place')
        self.organization=Organization.objects.create(owner=self.owner,created_by=self.owner,name_az='Fictional org')
        self.client.force_login(self.recipient)

    def invite(self,kind):
        target=self.place if kind=='place' else self.organization
        opts={'scope':'all_network'} if kind=='organization' else {}
        invitation=business_team.invite(actor=self.owner,target_type=kind,target_id=target.pk,email=self.recipient.email,**opts)
        notice=WorkflowNotification.objects.get(event_kind='team_invitation',entity_type=kind+'_team_invitation',entity_id=invitation.pk)
        return invitation,notice

    def counts(self):
        return (OwnerTeamMembership.objects.filter(member=self.recipient,is_active=True).count(),OrganizationGrant.objects.filter(member=self.recipient,is_active=True).count(),WorkflowNotification.objects.count(),EmailOutbox.objects.count())

    def url(self,notice,lang='az'):
        return ('' if lang=='az' else '/'+lang)+f'/account/notifications/{notice.pk}/accept/'

    def feedback(self,notice,lang='az'):
        before=self.counts();response=self.client.post(self.url(notice,lang))
        self.assertEqual(response.status_code,403)
        self.assertEqual(self.counts(),before)
        expected={'az':'Dəvət artıq əlçatan deyil. Siyahını yeniləyin.','ru':'Приглашение больше недоступно. Обновите список.','en':'The invitation is no longer available. Refresh the list.'}[lang]
        self.assertContains(response,expected,status_code=403)
        self.assertTemplateUsed(response,'pages/account_notifications.html')
        self.assertContains(response,'role="alert"',status_code=403)
        inbox=('' if lang=='az' else '/'+lang)+'/account/notifications/'
        self.assertContains(response,'href="'+inbox+'"',status_code=403)
        self.assertNotContains(response,'action="'+self.url(notice,lang)+'"',status_code=403)
        return response

    def test_revoked_invitation_explains_denial_for_both_kinds_and_locales(self):
        for kind in ['place','organization']:
            inv,n=self.invite(kind)
            business_team.decide_invitation(actor=self.owner,target_type=kind,invitation_id=inv.pk,cancel=True)
            for lang in ['az','ru','en']:
                with self.subTest(kind=kind,lang=lang):self.feedback(n,lang)
            inv.refresh_from_db();self.assertEqual(inv.status,'CANCELED')
        self.assertEqual(self.counts()[:2],(0,0))

    def test_expired_invitation_keeps_403_with_feedback_and_no_grant(self):
        for kind in ['place','organization']:
            with self.subTest(kind=kind):
                inv,n=self.invite(kind);type(inv).objects.filter(pk=inv.pk).update(expires_at=timezone.now()-timedelta(days=1))
                self.feedback(n)
        self.assertEqual(self.counts()[:2],(0,0))

    def test_stale_ownership_keeps_403_with_feedback_and_no_grant(self):
        for kind in ['place','organization']:
            with self.subTest(kind=kind):
                inv,n=self.invite(kind);target=self.place if kind=='place' else self.organization
                type(target).objects.filter(pk=target.pk).update(ownership_version=F('ownership_version')+1)
                self.feedback(n)
        self.assertEqual(self.counts()[:2],(0,0))

    def test_missing_invitation_for_own_notice_has_safe_feedback(self):
        for kind in ['place','organization']:
            with self.subTest(kind=kind):
                inv,n=self.invite(kind);inv.delete();self.feedback(n)
        self.assertEqual(self.counts()[:2],(0,0))

    def test_repeat_accepted_invitation_does_not_regrant_and_has_feedback(self):
        for kind in ['place','organization']:
            with self.subTest(kind=kind):
                inv,n=self.invite(kind)
                self.assertEqual(self.client.post(self.url(n)).status_code,302)
                self.feedback(n)
        self.assertEqual(self.counts()[:2],(1,1))

    def test_foreign_and_nonexistent_notice_remain_404(self):
        inv,n=self.invite('place');self.client.force_login(self.other)
        before=self.counts()
        for pk in [n.pk,n.pk+999999]:
            response=self.client.post(f'/account/notifications/{pk}/accept/')
            self.assertEqual(response.status_code,404)
            self.assertNotContains(response,'Dəvət artıq əlçatan deyil.',status_code=404)
        self.assertEqual(self.counts(),before)

    def test_changed_email_cannot_read_or_accept_old_notice(self):
        inv,n=self.invite('place');self.recipient.email='new@example.invalid';self.recipient.save(update_fields=['email'])
        self.assertEqual(self.client.post(self.url(n)).status_code,404)
        self.assertEqual(self.counts()[:2],(0,0))

    def test_auth_get_and_csrf_guards_are_unchanged(self):
        inv,n=self.invite('place')
        self.assertEqual(self.client.get(self.url(n)).status_code,405)
        csrf=Client(enforce_csrf_checks=True);csrf.force_login(self.recipient)
        self.assertEqual(csrf.post(self.url(n)).status_code,403)
        self.assertEqual(Client().post(self.url(n)).status_code,302)
        inv.refresh_from_db();self.assertEqual(inv.status,'PENDING')
        self.assertEqual(self.counts()[:2],(0,0))

    def test_current_invitation_success_keeps_redirect_and_single_grant(self):
        for kind in ['place','organization']:
            inv,n=self.invite(kind);response=self.client.post(self.url(n))
            self.assertRedirects(response,reverse('account_notifications'),fetch_redirect_response=False)
            inv.refresh_from_db();self.assertEqual(inv.status,'ACCEPTED')
        self.assertEqual(self.counts()[:2],(1,1))
