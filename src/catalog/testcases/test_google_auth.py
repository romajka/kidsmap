"""Exercise real allauth callbacks; only Google's HTTP transport is replaced."""
import json
import time
from unittest.mock import patch
from urllib.parse import parse_qs, urlsplit

import jwt
import requests
from django.contrib.auth import get_user_model
from django.core import mail
from django.db import IntegrityError, transaction
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils.translation import override

from catalog.models import UserEmailVerification, UserProfile

User = get_user_model()
PROVIDERS = {"google": {
    "APP": {"client_id": "test-client", "secret": "test-secret", "key": ""},
    "SCOPE": ["openid", "email", "profile"],
    "OAUTH_PKCE_ENABLED": True,
    "AUTH_PARAMS": {"access_type": "online", "prompt": "select_account"},
}}


@override_settings(SOCIALACCOUNT_PROVIDERS=PROVIDERS,
                   GOOGLE_OAUTH_CLIENT_ID="test-client",
                   GOOGLE_OAUTH_CLIENT_SECRET="test-secret")
class GoogleAuthTests(TestCase):
    def start(self, **data):
        response = self.client.post("/auth/google/", data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(urlsplit(response.url).hostname, "accounts.google.com")
        return parse_qs(urlsplit(response.url).query)

    def callback(self, state, **claims):
        payload = {
            "iss": "https://accounts.google.com", "aud": "test-client",
            "iat": int(time.time()), "exp": int(time.time()) + 3600,
            "sub": "google-sub-1", "email": "parent@gmail.com",
            "email_verified": True, "given_name": "Leyla", "family_name": "Aliyeva",
        }
        payload.update(claims)
        response = requests.Response()
        response.status_code = 200
        response.headers["content-type"] = "application/json"
        response._content = json.dumps({
            "access_token": "test-access-token", "token_type": "Bearer", "expires_in": 3600,
            "id_token": jwt.encode(payload, "test-signing-key-that-is-at-least-32-bytes", algorithm="HS256"),
        }).encode()
        # allauth validates issuer/audience/expiry from the server-to-server TLS exchange.
        with patch("requests.sessions.Session.request", return_value=response):
            return self.client.get("/auth/google/callback/", {"state": state, "code": "test-code"})

    def login_google(self, **claims):
        return self.callback(self.start()["state"][0], **claims)

    def assert_denied(self, response):
        self.assertEqual(response.status_code, 302)
        self.assertIn("/auth/login/", response.url)
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertNotIn("test-access-token", str(dict(self.client.session)))

    def test_start_contract_csrf_scopes_pkce_and_fixed_callback(self):
        self.assertEqual(self.client.get("/auth/google/").status_code, 405)
        self.assertEqual(Client(enforce_csrf_checks=True).post("/auth/google/").status_code, 403)
        query = self.start(scope="drive", auth_params="access_type=offline", process="connect")
        self.assertEqual(set(query["scope"][0].split()), {"openid", "email", "profile"})
        self.assertEqual(query["redirect_uri"], ["http://testserver/auth/google/callback/"])
        self.assertEqual(query["code_challenge_method"], ["S256"])
        self.assertEqual(query["access_type"], ["online"])
        self.assertNotIn("client_secret", query)

    def test_new_user_profile_verification_no_tokens_and_session_rotation(self):
        from allauth.account.models import EmailAddress
        from allauth.socialaccount.models import SocialAccount, SocialToken
        state = self.start()["state"][0]
        old_session = self.client.session.session_key
        response = self.callback(state)
        self.assertEqual(response.url, "/account/profile/")
        user = User.objects.get(email="parent@gmail.com")
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))
        self.assertNotEqual(self.client.session.session_key, old_session)
        self.assertFalse(user.has_usable_password())
        self.assertTrue(user.is_active)
        self.assertFalse(user.is_staff or user.is_superuser)
        self.assertEqual((user.first_name, user.last_name), ("Leyla", "Aliyeva"))
        self.assertNotIn("@", user.username)
        self.assertTrue(UserProfile.objects.filter(user=user, phone="").exists())
        self.assertTrue(UserEmailVerification.objects.get(user=user).is_verified)
        self.assertTrue(EmailAddress.objects.get(user=user).verified)
        self.assertEqual(SocialAccount.objects.get(user=user).uid, "google-sub-1")
        self.assertEqual(SocialToken.objects.count(), 0)
        self.assertEqual(len(mail.outbox), 0)

    def test_repeat_login_preserves_profile_and_uses_subject_after_email_change(self):
        self.login_google()
        user = User.objects.get()
        user.first_name = "My chosen name"
        user.save()
        self.client.post(reverse("account_logout"))
        self.login_google(email="changed@gmail.com", given_name="Changed")
        user.refresh_from_db()
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(user.first_name, "My chosen name")
        self.assertEqual(user.email, "parent@gmail.com")
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))

    def test_existing_email_links_case_insensitively_preserving_password_permissions(self):
        from allauth.socialaccount.models import SocialAccount
        user = User.objects.create_user("existing", "Parent@Gmail.com", "StrongPassword123!", is_staff=True)
        profile = UserProfile.objects.create(user=user, phone="+994501112233")
        response = self.login_google()
        self.assertEqual(response.status_code, 302)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(SocialAccount.objects.get().user_id, user.pk)
        user.refresh_from_db()
        profile.refresh_from_db()
        self.assertTrue(user.check_password("StrongPassword123!"))
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertEqual(profile.phone, "+994501112233")
        self.client.post(reverse("account_logout"))
        response = self.client.post(reverse("account_login"), {"username": "parent@gmail.com", "password": "StrongPassword123!"})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.session["_auth_user_id"], str(user.pk))
        self.client.post(reverse("password_reset"), {"email": "parent@gmail.com"})
        self.assertEqual(len(mail.outbox), 1)

    def test_unverified_missing_or_invalid_email_is_rejected_without_linking(self):
        from allauth.socialaccount.models import SocialAccount
        User.objects.create_user("existing", "parent@gmail.com", "StrongPassword123!")
        for claims in [{"email_verified": False}, {"email_verified": "true"},
                       {"email_verified": None}, {"email": None}, {"email": "invalid"}]:
            with self.subTest(claims=claims):
                self.assert_denied(self.login_google(**claims))
                self.assertEqual(User.objects.count(), 1)
                self.assertFalse(SocialAccount.objects.exists())

    def test_inactive_account_is_not_activated_or_duplicated(self):
        user = User.objects.create_user("blocked", "parent@gmail.com", is_active=False)
        self.assert_denied(self.login_google())
        user.refresh_from_db()
        self.assertFalse(user.is_active)
        self.assertEqual(User.objects.count(), 1)

    def test_identity_email_conflict_does_not_switch_or_merge_users(self):
        self.login_google()
        first = User.objects.get()
        self.client.post(reverse("account_logout"))
        second = User.objects.create_user("other", "other@gmail.com")
        self.assert_denied(self.login_google(email=second.email))
        self.assertEqual(User.objects.count(), 2)
        from allauth.socialaccount.models import SocialAccount
        self.assertEqual(SocialAccount.objects.get().user_id, first.pk)

    def test_different_google_subject_cannot_replace_existing_link(self):
        self.login_google()
        self.client.post(reverse("account_logout"))
        self.assert_denied(self.login_google(sub="different-sub"))
        self.assertEqual(User.objects.count(), 1)

    def test_logged_in_browser_cannot_attach_someone_elses_identity(self):
        state = self.start()["state"][0]
        current = User.objects.create_user("current", "current@example.com")
        self.client.force_login(current)
        response = self.callback(state)
        self.assertIn("/auth/login/", response.url)
        self.assertEqual(self.client.session["_auth_user_id"], str(current.pk))
        self.assertEqual(User.objects.count(), 1)

    def test_invalid_expired_and_replayed_state(self):
        self.assert_denied(self.callback("bad-state"))
        state = self.start()["state"][0]
        with patch("allauth.socialaccount.internal.statekit.time.time", return_value=time.time() + 700):
            self.assert_denied(self.callback(state))
        state = self.start()["state"][0]
        self.callback(state)
        self.client.post(reverse("account_logout"))
        self.assert_denied(self.callback(state))
        self.assertEqual(User.objects.count(), 1)

    def test_cancel_provider_error_and_network_failure(self):
        for error in ["access_denied", "server_error"]:
            state = self.start()["state"][0]
            self.assert_denied(self.client.get("/auth/google/callback/", {"state": state, "error": error}))
        state = self.start()["state"][0]
        with patch("requests.sessions.Session.request", side_effect=requests.Timeout("private detail")):
            self.assert_denied(self.client.get("/auth/google/callback/", {"state": state, "code": "test"}))
        self.assertEqual(User.objects.count(), 0)

    def test_invalid_oidc_issuer_audience_expiry_and_subject(self):
        for claims in [{"iss": "https://evil.test"}, {"aud": "wrong"}, {"exp": 1}, {"sub": ""}]:
            with self.subTest(claims=claims):
                self.assert_denied(self.login_google(**claims))
        self.assertEqual(User.objects.count(), 0)

    def test_local_next_and_language_survive_callback(self):
        state = self.start(next="/ru/account/profile/?tab=places#saved", language="ru")["state"][0]
        self.assertEqual(self.callback(state).url, "/ru/account/profile/?tab=places#saved")

    def test_unsafe_next_and_auth_loop_fall_back_to_local_profile(self):
        for target in ["https://evil.test/", "//evil.test/", "/\\evil.test/", "/auth/google/", "/ru/auth/login/"]:
            with self.subTest(target=target):
                state = self.start(next=target, language="en")["state"][0]
                self.assertEqual(self.callback(state).url, "/en/account/profile/")
                self.client.post(reverse("account_logout"))

    def test_auth_pages_have_localized_google_post_form(self):
        for lang, text in [("ru", "Продолжить с Google"), ("az", "Google ilə davam et"), ("en", "Continue with Google")]:
            with override(lang):
                for name in ["account_login", "account_register"]:
                    response = self.client.get(reverse(name), {"next": "/account/profile/"})
                    self.assertContains(response, text)
                    self.assertContains(response, 'action="/auth/google/"')
                    self.assertNotContains(response, "test-secret")

    @override_settings(GOOGLE_OAUTH_CLIENT_ID="", GOOGLE_OAUTH_CLIENT_SECRET="")
    def test_missing_configuration_is_friendly(self):
        response = self.client.post("/auth/google/", {"language": "ru"})
        self.assert_denied(response)
        page = self.client.get(response.url)
        self.assertContains(page, "Не удалось войти через Google")

    def test_google_only_user_can_reset_password_and_login(self):
        self.login_google()
        user = User.objects.get()
        self.client.post(reverse("account_logout"))
        self.client.post(reverse("password_reset"), {"email": user.email})
        self.assertEqual(len(mail.outbox), 1)
        import re
        reset_url = re.search(r"https?://[^\s]+/reset/[^\s]+", mail.outbox[0].body)
        self.assertIsNotNone(reset_url)
        response = self.client.get(reset_url.group(0))
        response = self.client.post(response.url, {"new_password1": "NewStrongPassword456!", "new_password2": "NewStrongPassword456!"})
        self.assertEqual(response.status_code, 302)
        user.refresh_from_db()
        self.assertTrue(user.check_password("NewStrongPassword456!"))

    def test_database_rejects_case_and_whitespace_duplicate_emails(self):
        User.objects.create_user("one", "parent@gmail.com")
        for number, value in enumerate(["PARENT@gmail.com", " parent@gmail.com "]):
            with self.subTest(email=value), self.assertRaises(IntegrityError), transaction.atomic():
                User.objects.create_user(f"duplicate-{number}", value)

    def test_database_allows_multiple_empty_emails(self):
        User.objects.create_user("one", "")
        User.objects.create_user("two", "")
        self.assertEqual(User.objects.count(), 2)

    def test_late_social_identity_collision_rolls_back_new_user(self):
        # Another callback may claim the subject after lookup but before insert.
        with patch("allauth.socialaccount.models.SocialAccount.objects.create", side_effect=IntegrityError("unique subject")):
            self.assert_denied(self.login_google())
        self.assertEqual(User.objects.count(), 0)
        self.assertEqual(UserProfile.objects.count(), 0)

    def test_google_only_reset_does_not_trust_a_changed_unverified_local_email(self):
        self.login_google()
        user = User.objects.get()
        user.email = "unverified@example.com"
        user.save()
        self.client.post(reverse("account_logout"))
        self.client.post(reverse("password_reset"), {"email": user.email})
        self.assertEqual(len(mail.outbox), 0)

    def test_registration_collision_after_validation_is_a_form_error(self):
        from catalog.controllers.auth_controller import AuthController
        original = AuthController.register_user_from_form

        def concurrent_winner(controller, *, form):
            User.objects.create_user("google-winner", form.cleaned_data["email"])
            return original(controller, form=form)

        with patch.object(AuthController, "register_user_from_form", concurrent_winner):
            response = self.client.post(reverse("account_register"), {
                "first_name": "Leyla", "last_name": "Aliyeva", "email": "parent@gmail.com",
                "phone": "+994501112233", "password1": "StrongPassword123!",
                "password2": "StrongPassword123!", "agreement": "on",
            })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["form"].errors)
        self.assertEqual(User.objects.count(), 1)

    def test_profile_email_collision_after_validation_is_a_form_error(self):
        from catalog.controllers.auth_controller import AuthController
        original = AuthController.update_user_profile_from_form
        user = User.objects.create_user("current", "current@example.com")
        self.client.force_login(user)

        def concurrent_winner(controller, *, user, form):
            User.objects.create_user("google-winner", form.cleaned_data["email"])
            return original(controller, user=user, form=form)

        with patch.object(AuthController, "update_user_profile_from_form", concurrent_winner):
            response = self.client.post(reverse("account_profile"), {
                "form_action": "profile", "first_name": "Leyla", "last_name": "Aliyeva",
                "email": "parent@gmail.com", "phone": "+994501112233",
            })
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.context["profile_form"].errors)
        user.refresh_from_db()
        self.assertEqual(user.email, "current@example.com")

    def test_account_permissions_and_existing_sessions_survive_linking(self):
        from django.contrib.auth.models import Group, Permission
        user = User.objects.create_user("owner", "parent@gmail.com", "StrongPassword123!")
        group = Group.objects.create(name="Existing owners")
        permission = Permission.objects.get(codename="change_place", content_type__app_label="catalog")
        group.permissions.add(permission)
        user.groups.add(group)
        existing_client = Client()
        existing_client.force_login(user)
        self.login_google()
        self.assertEqual(list(user.groups.values_list("pk", flat=True)), [group.pk])
        self.assertTrue(User.objects.get(pk=user.pk).has_perm("catalog.change_place"))
        self.assertEqual(existing_client.get(reverse("account_profile")).status_code, 200)

    def test_google_verifies_changed_local_email_without_two_primary_addresses(self):
        from allauth.account.models import EmailAddress
        self.login_google()
        user = User.objects.get()
        user.email = "changed@gmail.com"
        user.save()
        self.client.post(reverse("account_logout"))
        response = self.login_google(email="changed@gmail.com")
        self.assertEqual(response.url, "/account/profile/")
        self.assertEqual(EmailAddress.objects.get(user=user, primary=True).email, "changed@gmail.com")
        self.assertEqual(UserEmailVerification.objects.get(user=user, is_verified=True).email, "changed@gmail.com")

    def test_ambiguous_provider_configuration_has_no_traceback(self):
        from allauth.socialaccount.models import SocialApp
        SocialApp.objects.create(provider="google", name="Duplicate configuration", client_id="another", secret="unused")
        self.assert_denied(self.client.post("/auth/google/"))

    def test_database_rejects_duplicate_email_update(self):
        User.objects.create_user("one", "parent@gmail.com")
        user = User.objects.create_user("two", "other@example.com")
        with self.assertRaises(IntegrityError), transaction.atomic():
            User.objects.filter(pk=user.pk).update(email="PARENT@gmail.com")
