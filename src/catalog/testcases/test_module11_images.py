from django.core.files.base import ContentFile
from catalog.services.public_urls import build_public_absolute_uri
from catalog.testcases.test_module11_seo import Module11Fixture,Head

class Images(Head):
    def __init__(self,text):self.images=[];super().__init__(text)
    def handle_starttag(self,tag,attrs):
        super().handle_starttag(tag,attrs)
        if tag=='img':self.images.append(dict(attrs))

class PublicEntitySocialImageTests(Module11Fixture):
    def test_social_image_matches_the_publicly_rendered_entity_hero(self):
        self.spec.photo.save('m11-specialist.png',ContentFile(self.png))
        for lang in ('az','ru','en'):
            for obj,selector in [(self.org,'public-org-media-img'),(self.activity,'public-hero-image'),(self.spec,'km-detail-photo')]:
                with self.subTest(lang=lang,entity=type(obj).__name__):
                    response=self.response(obj,lang);self.assertEqual(response.status_code,200);page=Images(response.content.decode());hero=next(i for i in page.images if selector in i.get('class','').split());expected=build_public_absolute_uri(response.wsgi_request,hero['src']);self.assertEqual(page.one('og:image'),expected);self.assertEqual(page.one('twitter:image'),expected)
    def test_default_logo_remains_when_no_profile_or_visible_branch_photo_exists(self):
        self.place.status='draft';self.place.save(update_fields=['status'])
        for obj in [self.spec,self.org]:
            response=self.response(obj);self.assertEqual(response.status_code,200);page=Head(response.content.decode());self.assertTrue(page.one('og:image').endswith('/static/img/logo.svg'));self.assertEqual(page.one('og:image'),page.one('twitter:image'));self.assertNotIn(self.place.photo.name,page.one('og:image'))
