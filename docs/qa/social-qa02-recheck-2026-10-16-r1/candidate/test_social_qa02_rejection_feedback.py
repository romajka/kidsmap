"""SOCIAL-QA-02: author-owned latest rejection feedback and privacy."""
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
class TypedReviewRejectionFeedbackTests(TestCase):
    def setUp(self):
        users = get_user_model()
        self.author = users.objects.create_user('social01-author', first_name='Fictional')
        self.outsider = users.objects.create_user('social01-outsider')
        self.staff = users.objects.create_superuser('social01-reviewer', 'reviewer@example.invalid', 'fixture')
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

    def test_first_rejection_shows_reason_and_retained_text(self):
        for kind in self.targets:
            self.submit(kind, 3, 'First rejected text')
            self.decide(kind, False)
            for lang in ('ru', 'az', 'en'):
                with self.subTest(kind=kind, language=lang):
                    response = self.author_page(kind, lang)
                    self.assertContains(response, 'data-review-rejection')
                    self.assertContains(response, 'Fictional reason')
                    self.assertContains(response, 'First rejected text')
                    self.assertEqual(EditorRatingParser(response.content.decode()).value, '3')

    def test_rejected_edit_feedback_is_author_only_and_keeps_current_projection(self):
        for kind in self.targets:
            self.submit(kind, 4, 'Live four')
            live = self.decide(kind, True)
            self.submit(kind, 2, 'Private rejected edit', live.current_revision_id)
            self.decide(kind, False)
            for lang in ('ru', 'az', 'en'):
                with self.subTest(kind=kind, language=lang):
                    response = self.author_page(kind, lang)
                    self.assertContains(response, 'data-review-rejection')
                    self.assertContains(response, 'Private rejected edit')
                    self.assertContains(response, 'Fictional reason')
                    self.assertEqual(EditorRatingParser(response.content.decode()).value, '4')
            self.assertEqual(rating_summary(self.targets[kind]), {'average': 4.0, 'count': 1})
            for user in (self.outsider, None):
                if user is None:
                    self.client.logout()
                else:
                    self.client.force_login(user)
                response = self.client.get(self.url(kind))
                self.assertEqual(response.status_code, 200)
                self.assertNotContains(response, 'data-review-rejection')
                self.assertNotContains(response, 'Private rejected edit')
                self.assertNotContains(response, 'Fictional reason')
                self.assertContains(response, 'Live four')

    def test_new_pending_and_approved_version_hide_old_rejection_feedback(self):
        for kind in self.targets:
            self.submit(kind, 3, 'Rejected version')
            self.decide(kind, False)
            self.assertContains(self.author_page(kind), 'data-review-rejection')
            pending = self.submit(kind, 4, 'Corrected version')
            response = self.author_page(kind)
            self.assertNotContains(response, 'data-review-rejection')
            self.assertNotContains(response, 'Fictional reason')
            self.assertEqual(EditorRatingParser(response.content.decode()).value, '4')
            self.assertIsNotNone(pending.candidate_revision_id)
            self.decide(kind, True)
            response = self.author_page(kind)
            self.assertNotContains(response, 'data-review-rejection')
            self.assertEqual(rating_summary(self.targets[kind]), {'average': 4.0, 'count': 1})
            self.assertEqual(self.head(kind).revisions.filter(status='rejected').count(), 1)

    def test_rejection_reason_and_text_are_escaped(self):
        payload = '<script>window.SOCIAL_QA02=1</script> & <b>literal</b>'
        escaped = '&lt;script&gt;window.SOCIAL_QA02=1&lt;/script&gt; &amp; &lt;b&gt;literal&lt;/b&gt;'
        for kind in self.targets:
            self.submit(kind, 3, payload)
            self.decide(kind, False, reason=payload)
            response = self.author_page(kind)
            self.assertContains(response, 'data-review-rejection')
            self.assertContains(response, escaped)
            self.assertNotContains(response, payload)
