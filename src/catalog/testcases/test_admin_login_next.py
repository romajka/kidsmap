from django.contrib.auth import get_user_model
from django.test import TestCase


class AdminLoginRedirectTests(TestCase):
    """Jazzmin's login form has no hidden ``next``; /admin/login/ must still
    return staff to the admin index instead of LOGIN_REDIRECT_URL (a 404)."""

    def setUp(self):
        self.password = "admin-login-test-pass"
        self.user = get_user_model().objects.create_user(
            username="staff-login@example.test", email="staff-login@example.test",
            password=self.password, is_staff=True, is_superuser=True,
        )

    def test_bare_login_page_redirects_to_itself_with_next(self):
        response = self.client.get("/admin/login/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/admin/login/?next=%2Fadmin%2F")

    def test_localized_login_page_points_next_at_localized_index(self):
        response = self.client.get("/ru/admin/login/")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/ru/admin/login/?next=%2Fru%2Fadmin%2F")

    def test_login_with_next_lands_on_admin_index(self):
        response = self.client.post(
            "/admin/login/?next=%2Fadmin%2F",
            {"username": self.user.username, "password": self.password},
        )
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response["Location"], "/admin/")

    def test_explicit_next_is_kept(self):
        response = self.client.get("/admin/login/?next=/admin/catalog/specialist/")
        self.assertEqual(response.status_code, 200)
