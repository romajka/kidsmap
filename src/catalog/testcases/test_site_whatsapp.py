from django.test import TestCase

class SiteWhatsAppContactTests(TestCase):
    def test_support_phone_and_whatsapp_are_available_on_contacts_only(self):
        urls = [
            '/',
            '/ru/',
            '/en/',
            '/contacts/',
            '/ru/contacts/',
            '/en/contacts/',
            '/about/',
            '/ru/about/',
            '/en/about/',
            '/faq/',
            '/ru/faq/',
            '/en/faq/',
            '/catalog/',
            '/ru/catalog/',
            '/en/catalog/',
        ]
        for url in urls:
            response = self.client.get(url)
            self.assertEqual(response.status_code, 200, f"Failed for {url}")
            content = response.content.decode()

            # Support contacts live on their dedicated page, not venue pages.
            if url.endswith('/contacts/'):
                self.assertIn("https://wa.me/994554979723", content, f"Missing WhatsApp url in {url}")
                self.assertIn('href="tel:+994554979723"', content)
                self.assertIn('data-nosnippet', content)
                self.assertIn("+994 55 497 97 23", content, f"Missing phone in {url}")
            else:
                self.assertNotIn('994554979723', content.replace(' ', ''))
                prefix = '/ru' if url.startswith('/ru/') else '/en' if url.startswith('/en/') else ''
                self.assertIn(f'href="{prefix}/contacts/"', content)

            # Verify old phone / WhatsApp is nowhere in the rendered page
            self.assertNotIn("994505406639", content, f"Old WhatsApp found in {url}")
            self.assertNotIn("540 66 39", content, f"Old phone found in {url}")
            self.assertNotIn("5406639", content, f"Old phone digits found in {url}")
