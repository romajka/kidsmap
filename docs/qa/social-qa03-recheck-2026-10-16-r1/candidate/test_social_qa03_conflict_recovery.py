"""SOCIAL-QA-03: stale editing preserves draft, version protection and public current."""
from datetime import timedelta
from html.parser import HTMLParser

from django.contrib.auth import get_user_model
from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import override

from catalog.models import Activity, Event, SiteSettings, Specialist
from catalog.services.review_versions import rating_summary, review_types
from catalog.testcases.utils import create_ready_place


class EditorRatingParser(HTMLParser):
    def __init__(self, html):
        super().__init__()
        self.inside = False
        self.options = []
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == 'select':
            self.inside = attrs.get('id') == 'review-rating'
        elif self.inside and tag == 'option':
            self.options.append((attrs.get('value', ''), 'selected' in attrs))

    def handle_endtag(self, tag):
        if tag == 'select':
            self.inside = False

    @property
    def value(self):
        return next((value for value, selected in self.options if selected), self.options[0][0])


@override_settings(PLACE_REVIEW_COOLDOWN_SECONDS=0)
class TypedReviewConflictRecoveryTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.author = users.objects.create_user('social03-author', first_name='Fictional')
        self.outsider = users.objects.create_user('social03-outsider')
        self.staff = users.objects.create_superuser('social03-reviewer', 'reviewer@example.invalid', 'fixture')
        place = create_ready_place()
        self.targets = {
            'place': place,
            'activity': Activity.objects.create(place=place, status='published', name_az='Fictional activity'),
            'specialist': Specialist.objects.create(name='Fictional specialist', status='published', is_active=True),
            'event': Event.objects.create(name='Fictional event', name_az='Fictional event', category=place.category,
                status='published', event_format='online', start_datetime=timezone.now()+timedelta(days=5),
                end_datetime=timezone.now()+timedelta(days=5, hours=1)),
        }
        site = SiteSettings.get_solo()
        site.events_section_enabled = site.specialists_section_enabled = True
        site.save()

    def url(self, kind):
        return reverse('typed_reviews', args=[kind, self.targets[kind].pk])

    def head(self, kind):
        return review_types()[kind][1].objects.get(**{kind: self.targets[kind], 'user': self.author, 'is_current': True})

    def submit(self, kind, rating, text, expected=None):
        self.client.force_login(self.author)
        response = self.client.post(self.url(kind), {'rating': rating, 'text': text, 'expected_revision_id': expected or ''})
        self.assertEqual(response.status_code, 302, response.content[:200])
        return self.head(kind)

    def decide(self, kind, approve, reason='Fictional reason'):
        head = self.head(kind)
        self.client.force_login(self.staff)
        url = reverse('typed_review_action', args=[kind, head.pk, 'approve' if approve else 'reject'])
        response = self.client.post(url, {'revision_id': head.candidate_revision_id, 'reason': reason})
        self.assertEqual(response.status_code, 302)
        return self.head(kind)

    def author_page(self, kind, language='ru'):
        self.client.force_login(self.author)
        with override(language):
            response = self.client.get(self.url(kind))
        self.assertEqual(response.status_code, 200)
        return response

    def stale_pair(self, kind):
        self.submit(kind, 4, 'Public current four')
        live = self.decide(kind, True)
        current_id = live.current_revision_id
        self.submit(kind, 5, 'Latest private candidate A', current_id)
        return current_id, self.head(kind)

    def conflict(self, kind, expected, text='Unsaved draft B', rating=2):
        self.client.force_login(self.author)
        return self.client.post(self.url(kind), {'rating': rating, 'text': text, 'expected_revision_id': expected})

    def test_stale_draft_renders_with_latest_version_and_no_write(self):
        for kind in self.targets:
            stale, latest = self.stale_pair(kind)
            count = latest.revisions.count()
            for lang in ('ru', 'az', 'en'):
                with self.subTest(kind=kind, language=lang), override(lang):
                    response = self.conflict(kind, stale)
                    self.assertEqual(response.status_code, 409)
                    for marker in ('data-review-conflict', 'data-review-edit', 'data-review-latest', 'Latest private candidate A', 'Unsaved draft B', 'Public current four'):
                        self.assertContains(response, marker, status_code=409)
                    self.assertEqual(EditorRatingParser(response.content.decode()).value, '2')
                    self.assertContains(response, f'name="expected_revision_id" value="{latest.candidate_revision_id}"', status_code=409)
                    self.assertContains(response, 'data-review-reload', status_code=409)
                    self.assertEqual(self.head(kind).candidate_revision_id, latest.candidate_revision_id)
                    self.assertEqual(self.head(kind).current_revision_id, stale)
                    self.assertEqual(self.head(kind).revisions.count(), count)
                    self.assertEqual(rating_summary(self.targets[kind]), {'average': 4.0, 'count': 1})

    def test_explicit_retry_saves_draft_and_a_new_race_conflicts_again(self):
        for kind in self.targets:
            stale, latest = self.stale_pair(kind)
            self.assertEqual(self.conflict(kind, stale).status_code, 409)
            newest = self.submit(kind, 1, 'Newer private candidate C', latest.candidate_revision_id)
            response = self.conflict(kind, latest.candidate_revision_id)
            self.assertEqual(response.status_code, 409)
            self.assertContains(response, 'Unsaved draft B', status_code=409)
            self.assertContains(response, 'Newer private candidate C', status_code=409)
            self.assertEqual(self.head(kind).candidate_revision_id, newest.candidate_revision_id)
            response = self.conflict(kind, newest.candidate_revision_id)
            self.assertEqual(response.status_code, 302)
            head = self.head(kind)
            self.assertEqual(head.candidate_revision.rating, 2)
            self.assertEqual(head.candidate_revision.text, 'Unsaved draft B')
            self.assertEqual(EditorRatingParser(self.author_page(kind).content.decode()).value, '2')
            self.assertEqual(head.current_revision_id, stale)
            self.assertEqual(rating_summary(self.targets[kind]), {'average': 4.0, 'count': 1})

    def test_conflicting_script_text_is_escaped_and_preserved(self):
        payload = '<script>window.SOCIAL_QA03=1</script> & <b>literal</b>'
        escaped = '&lt;script&gt;window.SOCIAL_QA03=1&lt;/script&gt; &amp; &lt;b&gt;literal&lt;/b&gt;'
        for kind in self.targets:
            stale, latest = self.stale_pair(kind)
            response = self.conflict(kind, stale, payload)
            self.assertEqual(response.status_code, 409)
            self.assertContains(response, escaped, status_code=409)
            self.assertNotContains(response, payload, status_code=409)
            self.assertEqual(self.head(kind).candidate_revision_id, latest.candidate_revision_id)
            self.assertFalse(self.head(kind).revisions.filter(text=payload).exists())

    def test_draft_is_not_shared_with_other_users_or_persisted(self):
        for kind in self.targets:
            stale, latest = self.stale_pair(kind)
            self.assertEqual(self.conflict(kind, stale).status_code, 409)
            self.assertFalse(self.head(kind).revisions.filter(text='Unsaved draft B').exists())
            for user in (self.outsider, None):
                if user is None:
                    self.client.logout()
                else:
                    self.client.force_login(user)
                response = self.client.get(self.url(kind))
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, 'Unsaved draft B')
                self.assertNotContains(response, 'Latest private candidate A')
                self.assertNotContains(response, 'data-review-conflict')
                self.assertContains(response, 'Public current four')
            response = self.client.post(self.url(kind), {'rating': 2, 'text': 'Guest draft', 'expected_revision_id': stale})
            self.assertEqual(response.status_code, 403)
            self.assertEqual(self.head(kind).candidate_revision_id, latest.candidate_revision_id)

    def test_invalid_input_keeps_400_and_does_not_overwrite_candidate(self):
        for kind in self.targets:
            stale, latest = self.stale_pair(kind)
            for data in ({'rating': 0, 'text': 'Invalid rating', 'expected_revision_id': stale}, {'rating': 2, 'text': 'Invalid token', 'expected_revision_id': 'bad-token'}):
                self.client.force_login(self.author)
                response = self.client.post(self.url(kind), data)
                self.assertEqual(response.status_code, 400)
                self.assertNotContains(response, 'data-review-conflict', status_code=400)
                self.assertEqual(self.head(kind).candidate_revision_id, latest.candidate_revision_id)

    @override_settings(PLACE_REVIEW_COOLDOWN_SECONDS=120)
    def test_current_token_early_repeat_keeps_429_and_retry_after(self):
        for kind in ('place', 'activity', 'event'):
            first = self.submit(kind, 4, 'Initial cooldown version')
            response = self.conflict(kind, first.candidate_revision_id)
            self.assertEqual(response.status_code, 429)
            self.assertGreater(int(response['Retry-After']), 0)
            self.assertNotContains(response, 'data-review-conflict', status_code=429)
            self.assertEqual(self.head(kind).candidate_revision_id, first.candidate_revision_id)
            self.assertEqual(self.head(kind).revisions.count(), 1)
