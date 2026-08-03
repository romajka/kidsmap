from django.test import TestCase, override_settings

from catalog.testcases.utils import create_quality_place


class SearchEngineVerificationTests(TestCase):
    @override_settings(
        GOOGLE_SITE_VERIFICATION="google-test-token",
        BING_SITE_VERIFICATION="bing-test-token",
    )
    def test_verification_tags_are_in_head_on_public_pages(self):
        place = create_quality_place(name="Verification public place")
        paths = (
            "/",
            "/ru/catalog/",
            "/en/reviews/",
            f"/place/{place.pk}-{place.slug}/",
        )

        for path in paths:
            with self.subTest(path=path):
                response = self.client.get(path)
                self.assertEqual(response.status_code, 200)
                content = response.content.decode()
                head = content.split("</head>", 1)[0]
                self.assertIn(
                    '<meta name="google-site-verification" content="google-test-token" />',
                    head,
                )
                self.assertIn(
                    '<meta name="msvalidate.01" content="bing-test-token" />',
                    head,
                )

    @override_settings(
        GOOGLE_SITE_VERIFICATION="",
        BING_SITE_VERIFICATION="",
    )
    def test_empty_verification_values_render_no_tags(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "google-site-verification")
        self.assertNotContains(response, "msvalidate.01")

    @override_settings(
        GOOGLE_SITE_VERIFICATION='token"><script>alert(1)</script>',
        BING_SITE_VERIFICATION='bing"><script>alert(2)</script>',
    )
    def test_verification_values_are_html_escaped(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertNotContains(response, "<script>alert(1)</script>", html=False)
        self.assertNotContains(response, "<script>alert(2)</script>", html=False)
        self.assertContains(response, "token&quot;&gt;&lt;script&gt;alert(1)&lt;/script&gt;")
        self.assertContains(response, "bing&quot;&gt;&lt;script&gt;alert(2)&lt;/script&gt;")
