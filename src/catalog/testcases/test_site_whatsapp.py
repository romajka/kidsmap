from django.test import TestCase

class SiteWhatsAppContactTests(TestCase):
    def test_whatsapp_and_phone_across_site_pages(self):
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

            # Verify new WhatsApp link and phone
            self.assertIn("https://wa.me/994554979723", content, f"Missing WhatsApp url in {url}")
            self.assertIn("+994 55 497 97 23", content, f"Missing phone in {url}")

            # Verify old phone / WhatsApp is nowhere in the rendered page
            self.assertNotIn("994505406639", content, f"Old WhatsApp found in {url}")
            self.assertNotIn("540 66 39", content, f"Old phone found in {url}")
            self.assertNotIn("5406639", content, f"Old phone digits found in {url}")
