"""Owner feedback must survive sessions while remaining escaped and private."""
from html.parser import HTMLParser
from django.test import TestCase
from django.urls import reverse
from django.utils.html import escape
from django.utils.translation import override
from catalog.models import VolunteerPlaceRevision
from catalog.testcases.test_task33_publication import PublicationFixture


class ReviewNoteHTML(HTMLParser):
    """Read the displayed note, including visual line breaks, from its own block."""
    def __init__(self, html):
        super().__init__()
        self.inside = False
        self.text = ''
        self.scripts = 0
        self.feed(html)

    def handle_starttag(self, tag, attrs):
        if tag == 'section' and 'data-place-review-note' in dict(attrs):
            self.inside = True
        if self.inside and tag == 'br':
            self.text += '\n'
        if self.inside and tag == 'script':
            self.scripts += 1

    def handle_endtag(self, tag):
        if tag == 'section':
            self.inside = False

    def handle_data(self, text):
        if self.inside:
            self.text += text


class PlaceRejectionFeedbackTests(PublicationFixture, TestCase):
    note = 'QA refusal <script>window.qaUnexpected=1</script>\nSecond line & detail'

    def reject(self, final=False):
        revision = self.propose({'description_az':'QA corrected candidate description'})
        self.s.review(actor=self.staff,revision_id=revision.pk,version=revision.version,
                      approve=False,note=self.note,final_reject=final)
        revision.refresh_from_db()
        return revision

    def page(self, language='ru'):
        with override(language):
            return self.client.get(reverse('owner_place_edit',args=[self.place.pk]))

    def test_saved_reason_survives_reload_and_new_session(self):
        revision = self.reject()
        self.client.force_login(self.owner)
        for attempt in range(3):
            if attempt == 2:
                self.client.logout(); self.client.force_login(self.owner)
            response = self.page()
            self.assertTrue(b'data-place-review-note' in response.content,'Owner feedback block missing')
            rendered = ReviewNoteHTML(response.content.decode())
            self.assertIn(self.note, rendered.text, 'The full saved note and its line breaks must remain visible')
            self.assertEqual(rendered.scripts, 0)
            self.assertNotContains(response,'<script>window.qaUnexpected')
        revision.refresh_from_db()
        self.assertEqual(revision.review_note,self.note)

    def test_rejection_heading_uses_selected_locale(self):
        self.reject(final=True); self.client.force_login(self.owner)
        for language,title in [('ru','Замечание модератора'),('az','Moderatorun qeydi'),('en','Moderator note')]:
            with self.subTest(language=language):
                response = self.page(language)
                rendered = ReviewNoteHTML(response.content.decode())
                self.assertIn(title, rendered.text, 'Localized note heading missing')
                self.assertIn(self.note, rendered.text, 'Saved note missing')
                self.assertEqual(rendered.scripts, 0)

    def test_draft_preserves_reason_resubmission_clears_it(self):
        revision = self.reject()
        revision = self.propose({'description_az':'QA revised again'},revision_version=revision.version,submit=False)
        self.client.force_login(self.owner)
        self.assertTrue(b'data-place-review-note' in self.page().content,'Draft reason missing')
        self.assertEqual(revision.review_note,self.note)
        revision = self.propose({'description_az':'QA revised again'},revision_version=revision.version)
        self.assertEqual(revision.review_note,'')
        self.assertNotContains(self.page(),'data-place-review-note')

    def test_empty_or_inapplicable_note_has_no_feedback_block(self):
        self.client.force_login(self.owner)
        self.assertNotContains(self.page(),'data-place-review-note')
        revision = self.reject()
        for state,note in [('draft',''),('pending',self.note),('approved',self.note)]:
            VolunteerPlaceRevision.objects.filter(pk=revision.pk).update(status=state,review_note=note)
            self.assertNotContains(self.page(),'data-place-review-note')

    def test_outsider_and_guest_cannot_read_reason(self):
        self.reject()
        for actor in (self.other,None):
            self.client.logout()
            if actor: self.client.force_login(actor)
            with override('ru'):
                response = self.client.get(reverse('owner_place_edit',args=[self.place.pk]),follow=True)
            self.assertNotContains(response,escape(self.note))
