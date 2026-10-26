from django.test import TestCase
from django.contrib.auth import get_user_model


class AccountSettingsRedesignTest(TestCase):
    def setUp(self):
        User = get_user_model()
        self.user = User.objects.create_user(
            username='settings_ui_user',
            email='settings_ui@example.com',
            password='InitialPassword123!',
            first_name='Эльмир',
            last_name='Алиев',
        )

    def test_account_settings_renders_compact_avatar_2x2_grid_and_security_card(self):
        self.client.force_login(self.user)
        response = self.client.get('/ru/account/settings/')
        self.assertEqual(response.status_code, 200)
        html = response.content.decode('utf-8')

        # Check compact 64px avatar uploader
        self.assertIn('account-avatar-uploader--compact', html)
        self.assertIn('account-avatar-uploader__camera-badge', html)
        self.assertIn('id_avatar', html)
        self.assertIn('account-avatar-remove-btn', html)

        # Check symmetric 2x2 grid & field icons
        self.assertIn('account-form-grid--2x2', html)
        self.assertIn('account-field-label__icon', html)

        # Check security card
        self.assertIn('account-security-card', html)
        self.assertIn('data-password-toggle', html)
        self.assertIn('id_old_password', html)
        self.assertIn('id_new_password1', html)
        self.assertIn('id_new_password2', html)

    def test_account_settings_profile_update(self):
        self.client.force_login(self.user)
        response = self.client.post('/ru/account/settings/', {
            'form_action': 'profile',
            'first_name': 'Рамин',
            'last_name': 'Гасанов',
            'email': 'settings_ui@example.com',
            'phone': '+994501234567',
        }, follow=True)
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.assertEqual(self.user.first_name, 'Рамин')
        self.assertEqual(self.user.last_name, 'Гасанов')
