from smtplib import SMTPException
from unittest.mock import patch

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import TestCase, override_settings
from rest_framework.permissions import AllowAny
from rest_framework.test import APIClient

from authentication.models import RegistrationOTP
from authentication.services import create_registration_otp
from authentication.views import LoginView, RegisterVerifyView, RegisterView

User = get_user_model()


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
class RegistrationApiTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_creates_inactive_user_and_sends_otp(self):
        response = self.client.post(
            '/api/register/',
            {'email': 'test@example.com', 'password': 'StrongPass123'},
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        user = User.objects.get(email='test@example.com')
        self.assertFalse(user.is_active)
        self.assertEqual(RegistrationOTP.objects.filter(email='test@example.com').count(), 1)
        self.assertEqual(len(mail.outbox), 1)

    def test_register_returns_clear_error_when_email_fails(self):
        with patch('authentication.serializers.create_registration_otp') as mocked_otp:
            mocked_otp.side_effect = SMTPException()
            response = self.client.post(
                '/api/register/',
                {'email': 'test@example.com', 'password': 'StrongPass123'},
                format='json',
            )

        self.assertEqual(response.status_code, 503)
        self.assertEqual(User.objects.filter(email='test@example.com').count(), 0)

    def test_verify_registration_activates_user(self):
        self.client.post(
            '/api/register/',
            {'email': 'test@example.com', 'password': 'StrongPass123'},
            format='json',
        )
        otp = RegistrationOTP.objects.get(email='test@example.com')

        response = self.client.post(
            '/api/register/verify/',
            {'email': 'test@example.com', 'otp': otp.code},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertTrue(User.objects.get(email='test@example.com').is_active)
        otp.refresh_from_db()
        self.assertIsNotNone(otp.verified_at)

    def test_verify_rejects_bad_otp(self):
        self.client.post(
            '/api/register/',
            {'email': 'test@example.com', 'password': 'StrongPass123'},
            format='json',
        )

        response = self.client.post(
            '/api/register/verify/',
            {'email': 'test@example.com', 'otp': '000000'},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertFalse(User.objects.get(email='test@example.com').is_active)

    def test_verify_rejects_bad_otp_format(self):
        response = self.client.post(
            '/api/register/verify/',
            {'email': 'test@example.com', 'otp': '123'},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertIn('otp', response.data)

    def test_otp_code_is_six_digits(self):
        otp = create_registration_otp('test@example.com')

        self.assertEqual(len(otp.code), 6)
        self.assertTrue(otp.code.isdigit())

    def test_register_page_loads_with_csrf_cookie(self):
        response = self.client.get('/register/')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Create your account')
        self.assertContains(response, 'Verify your email')
        self.assertContains(response, 'id="modalMessage"')
        self.assertContains(response, 'showModalMessage(error.message, \'danger\')')
        self.assertContains(response, 'class="form-control otp-input"', count=6)
        self.assertNotContains(response, 'AM')
        self.assertIn('csrftoken', response.cookies)

    def test_registration_endpoints_allow_anonymous_users(self):
        self.assertEqual(RegisterView.permission_classes, [AllowAny])
        self.assertEqual(RegisterVerifyView.permission_classes, [AllowAny])

    def test_login_sets_auth_cookie(self):
        user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='StrongPass123',
        )

        response = self.client.post(
            '/api/login/',
            {'email': user.email, 'password': 'StrongPass123'},
            format='json',
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn('auth_token', response.cookies)
        self.assertTrue(response.cookies['auth_token']['httponly'])
        self.assertEqual(response.data['user']['email'], 'test@example.com')

    def test_login_rejects_invalid_credentials(self):
        response = self.client.post(
            '/api/login/',
            {'email': 'missing@example.com', 'password': 'badpass'},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertNotIn('auth_token', response.cookies)

    def test_login_requires_verified_user(self):
        User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='StrongPass123',
            is_active=False,
        )

        response = self.client.post(
            '/api/login/',
            {'email': 'test@example.com', 'password': 'StrongPass123'},
            format='json',
        )

        self.assertEqual(response.status_code, 400)
        self.assertNotIn('auth_token', response.cookies)

    def test_me_requires_auth_cookie(self):
        response = self.client.get('/api/me/')

        self.assertEqual(response.status_code, 401)

    def test_me_returns_logged_in_user_from_cookie(self):
        user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='StrongPass123',
        )
        login_response = self.client.post(
            '/api/login/',
            {'email': user.email, 'password': 'StrongPass123'},
            format='json',
        )

        response = self.client.get('/api/me/')

        self.assertEqual(login_response.status_code, 200)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['email'], 'test@example.com')

    def test_login_endpoint_allows_anonymous_users(self):
        self.assertEqual(LoginView.permission_classes, [AllowAny])

    def test_logout_clears_auth_cookie(self):
        user = User.objects.create_user(
            username='test@example.com',
            email='test@example.com',
            password='StrongPass123',
        )
        login_response = self.client.post(
            '/api/login/',
            {'email': user.email, 'password': 'StrongPass123'},
            format='json',
        )

        self.assertEqual(login_response.status_code, 200)
        self.assertIn(settings.JWT_AUTH_COOKIE_NAME, login_response.cookies)

        logout_response = self.client.post('/api/logout/')
        self.assertEqual(logout_response.status_code, 200)
        self.assertEqual(logout_response.cookies.get(settings.JWT_AUTH_COOKIE_NAME).value, '')

        me_response = self.client.get('/api/me/')
        self.assertEqual(me_response.status_code, 401)
