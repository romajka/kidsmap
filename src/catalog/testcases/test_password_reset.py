from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase
from django.urls import reverse

User = get_user_model()


class PasswordResetTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testparent",
            email="parent@example.com",
            password="StrongPassword123!",
        )

    def test_login_page_renders_modal_markup(self):
        response = self.client.get(reverse("account_login"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'id="resetPasswordModal"')
        self.assertContains(response, 'data-open-reset-modal')
        self.assertContains(response, 'id="resetPasswordAjaxForm"')
        self.assertContains(response, 'id="resetModalEmailInput"')

    def test_password_reset_get_standalone_page(self):
        response = self.client.get(reverse("password_reset"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth/password_reset_form.html")
        self.assertContains(response, "register-shell")
        self.assertContains(response, "register-aside")

    def test_password_reset_standard_post_redirects(self):
        response = self.client.post(
            reverse("password_reset"),
            {"email": "parent@example.com"},
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(reverse("password_reset_done"), response["Location"])
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("parent@example.com", mail.outbox[0].to)

    def test_password_reset_ajax_post_success(self):
        response = self.client.post(
            reverse("password_reset"),
            {"email": "parent@example.com", "is_ajax": "1"},
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("ok"))
        self.assertTrue(bool(data.get("message")))
        self.assertEqual(len(mail.outbox), 1)

    def test_password_reset_ajax_by_username_success(self):
        response = self.client.post(
            reverse("password_reset"),
            {"email": "testparent", "is_ajax": "1"},
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data.get("ok"))
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn("parent@example.com", mail.outbox[0].to)

    def test_password_reset_ajax_post_empty_error(self):
        response = self.client.post(
            reverse("password_reset"),
            {"email": "", "is_ajax": "1"},
            headers={"x-requested-with": "XMLHttpRequest"},
        )
        self.assertEqual(response.status_code, 400)
        data = response.json()
        self.assertFalse(data.get("ok"))
        self.assertTrue("errors" in data)

    def test_password_reset_done_page(self):
        response = self.client.get(reverse("password_reset_done"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth/password_reset_done.html")
        self.assertContains(response, "register-shell")
        self.assertContains(response, "register-status-card")

    def test_password_reset_confirm_invalid_token(self):
        response = self.client.get(
            reverse(
                "password_reset_confirm",
                kwargs={"uidb64": "invalid", "token": "invalid-token"},
            )
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth/password_reset_confirm.html")
        self.assertContains(response, "register-shell")

    def test_password_reset_complete_page(self):
        response = self.client.get(reverse("password_reset_complete"))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "auth/password_reset_complete.html")
        self.assertContains(response, "register-shell")
        self.assertContains(response, "register-status-card")
