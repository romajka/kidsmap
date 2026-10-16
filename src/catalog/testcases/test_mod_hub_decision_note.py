"""Processed moderation decisions retain their escaped reason without mutation."""
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.test import TestCase
from django.utils.html import escape
from catalog.models import Organization, VolunteerPlaceRevision
from catalog.services import publication, volunteer_proposals
from catalog.services.staff_roles import VOLUNTEER_GROUP


class HubDecisionNoteTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        users = get_user_model()
        cls.admin = users.objects.create_superuser('note-admin', 'note@example.invalid', None)
        cls.reviewer = users.objects.create_user('note-reviewer', is_staff=True)
        cls.reviewer.user_permissions.add(Permission.objects.get(content_type__app_label='catalog', codename='change_place'))
        cls.volunteer = users.objects.create_user('note-volunteer', is_staff=True)
        cls.volunteer.groups.add(Group.objects.get_or_create(name=VOLUNTEER_GROUP)[0])
        cls.bare = users.objects.create_user('note-bare', is_staff=True)
        cls.reason = 'QA <img src=x onerror=alert(1)> & "quoted"\n' + 'LongReason' * 60
        cls.rows = []
        for action in ('approve', 'return', 'reject'):
            org = Organization.objects.create(created_by=cls.volunteer, name_az='QA Decision ' + action)
            rev = volunteer_proposals.propose(actor=cls.volunteer, kind='organization', target_id=org.pk,
                patch={'description_az': 'QA candidate'}, expected_version=org.content_version,
                revision_version=0, submit=True)
            if action == 'approve':
                rev = publication.review(actor=cls.admin, revision_id=rev.pk, version=rev.version,
                    approve=True, note=cls.reason)
            else:
                rev = volunteer_proposals.review(actor=cls.admin, revision_id=rev.pk,
                    version=rev.version, action=action, reason=cls.reason)
            cls.rows.append(rev.pk)

    def url(self, lang, pk):
        self.client.cookies['django_language'] = lang
        return ('' if lang == 'az' else '/' + lang) + '/admin/volunteer/moderation/content/' + str(pk) + '/'

    def test_terminal_reasons_visible_escaped_localized_and_read_only(self):
        before = list(Organization.objects.values()), list(VolunteerPlaceRevision.objects.values())
        for actor in (self.admin, self.reviewer):
            self.client.force_login(actor)
            for lang, title in [('ru', 'Причина решения'), ('az', 'Qərarın səbəbi'), ('en', 'Decision reason')]:
                for pk in self.rows:
                    with self.subTest(actor=actor.username, lang=lang, pk=pk):
                        response = self.client.get(self.url(lang, pk))
                        self.assertEqual(response.status_code, 200)
                        self.assertContains(response, 'id="km-hub-decision-note-title"')
                        self.assertContains(response, title)
                        self.assertContains(response, str(escape(self.reason)).replace('\n', '<br>'))
                        self.assertNotContains(response, '<img src=x')
                        self.assertNotContains(response, 'id="hub-reason"')
        self.assertEqual(before, (list(Organization.objects.values()), list(VolunteerPlaceRevision.objects.values())))

    def test_empty_and_pending_reasons_are_not_presented_as_decisions(self):
        self.client.force_login(self.admin)
        for status, note in [('approved', ''), ('pending', self.reason)]:
            rev = VolunteerPlaceRevision.objects.get(pk=self.rows[0])
            VolunteerPlaceRevision.objects.filter(pk=rev.pk).update(status=status, review_note=note)
            response = self.client.get(self.url('en', rev.pk))
            self.assertEqual(response.status_code, 200)
            self.assertNotContains(response, 'id="km-hub-decision-note-title"')
            if status == 'pending':
                self.assertContains(response, 'id="hub-reason"')

    def test_unauthorized_readers_do_not_gain_access(self):
        for actor in (self.volunteer, self.bare):
            self.client.force_login(actor)
            self.assertEqual(self.client.get(self.url('en', self.rows[0])).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(self.url('en', self.rows[0])).status_code, 302)
