"""Exercise the actual staff add page, including role assignment and errors."""

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse

from catalog.models import StaffAccessUser, StaffRoleAudit, UserProfile


class StaffCreationRegressionTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.creators = [
            User.objects.create_superuser(
                username=f"creator_{index}", email=f"creator_{index}@example.com",
                password="Test-creator-83!",
            )
            for index in range(2)
        ]

    def payload(self, username="new_staff", role="moderator"):
        return {
            "username": username,
            "email": f"{username}@example.com",
            "password1": "Independent-password-83!",
            "password2": "Independent-password-83!",
            "admin_role": role,
            "profile-TOTAL_FORMS": "1",
            "profile-INITIAL_FORMS": "0",
            "profile-MIN_NUM_FORMS": "0",
            "profile-MAX_NUM_FORMS": "1",
            "profile-0-phone": "",
            "profile-0-gender": "U",
            "_save": "Save",
        }

    def test_add_page_opens_for_both_superadmins_in_all_languages(self):
        for creator in self.creators:
            self.client.force_login(creator)
            for language in ("az", "ru", "en"):
                with self.subTest(creator=creator.username, language=language):
                    self.client.cookies["django_language"] = language
                    response = self.client.get(reverse("admin:catalog_staffaccessuser_add"))
                    self.assertEqual(response.status_code, 200)
                    self.assertContains(response, 'name="username"')
                    self.assertContains(response, 'name="admin_role"')

    def test_both_superadmins_can_create_each_staff_role(self):
        for creator in self.creators:
            self.client.force_login(creator)
            for role in ("moderator", "content_manager", "volunteer"):
                with self.subTest(creator=creator.username, role=role):
                    username = f"{creator.username}_{role}"
                    response = self.client.post(
                        reverse("admin:catalog_staffaccessuser_add"),
                        self.payload(username, role),
                    )
                    self.assertEqual(response.status_code, 302)
                    user = User.objects.get(username=username)
                    self.assertTrue(user.is_active)
                    self.assertTrue(user.is_staff)
                    self.assertFalse(user.is_superuser)
                    self.assertTrue(user.check_password("Independent-password-83!"))
                    self.assertEqual(StaffAccessUser.objects.get(pk=user.pk).pk, user.pk)
                    self.assertEqual(UserProfile.objects.filter(user=user).count(), 1)
                    self.assertEqual(
                        set(user.groups.values_list("name", flat=True)),
                        {"KidsMap Volunteers"} if role == "volunteer" else set(),
                    )
                    self.assertEqual(user.has_perm("catalog.change_place"), role == "content_manager")
                    self.assertEqual(user.has_perm("catalog.change_placereview"), role == "moderator")
                    self.assertTrue(StaffRoleAudit.objects.filter(
                        actor=creator, target_id=user.pk, new_role=role,
                    ).exists())

    def test_invalid_input_returns_field_errors_without_creating_user(self):
        self.client.force_login(self.creators[0])
        cases = (
            ({"username": ""}, "username"),
            ({"username": self.creators[0].username}, "username"),
            ({"email": "invalid-email"}, "email"),
            ({"password1": "", "password2": ""}, "password1"),
            ({"password2": "Different-password-83!"}, "password2"),
            ({"password1": "123", "password2": "123"}, "password2"),
            ({"admin_role": ""}, "admin_role"),
            ({"admin_role": "superadmin"}, "admin_role"),
            ({"admin_role": "unknown-role"}, "admin_role"),
        )
        count = User.objects.count()
        for changes, field in cases:
            with self.subTest(changes=changes):
                response = self.client.post(
                    reverse("admin:catalog_staffaccessuser_add"),
                    {**self.payload(), **changes},
                )
                self.assertEqual(response.status_code, 200)
                self.assertTrue(response.context["adminform"].form.errors.get(field))
                self.assertContains(response, 'role="alert"')
                self.assertEqual(User.objects.count(), count)
                self.assertFalse(StaffRoleAudit.objects.exists())

    def test_staff_with_model_permissions_cannot_create_other_staff(self):
        user = User.objects.create_user("limited_creator", is_staff=True)
        user.user_permissions.add(*Permission.objects.filter(
            content_type__app_label="catalog", content_type__model="staffaccessuser",
            codename__in=("add_staffaccessuser", "change_staffaccessuser"),
        ))
        self.client.force_login(user)
        url = reverse("admin:catalog_staffaccessuser_add")
        self.assertEqual(self.client.get(url).status_code, 403)
        self.assertEqual(self.client.post(url, self.payload()).status_code, 403)
        self.assertFalse(User.objects.filter(username="new_staff").exists())

    def test_existing_email_is_a_validation_error_for_both_creators(self):
        existing = User.objects.create_user("site_account", email="Existing@example.com")
        for creator in self.creators:
            self.client.force_login(creator)
            for email in ("Existing@example.com", "existing@example.com", "  EXISTING@example.com  "):
                with self.subTest(creator=creator.username, email=email):
                    response = self.client.post(
                        reverse("admin:catalog_staffaccessuser_add"),
                        {**self.payload(), "email": email},
                    )
                    self.assertEqual(response.status_code, 200)
                    self.assertTrue(response.context["adminform"].form.errors.get("email"))
                    self.assertContains(response, 'role="alert"')
                    self.assertFalse(User.objects.filter(username="new_staff").exists())
        existing.refresh_from_db()
        self.assertFalse(existing.is_staff)
