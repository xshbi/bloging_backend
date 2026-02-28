"""
Comprehensive tests for the `users` app.

Covers:
  - Registration (success, duplicate username, mismatched passwords, short password)
  - Login / JWT token obtain
  - Token refresh
  - Logout (blacklist refresh token)
  - Profile retrieve & update
  - Public profile
  - Change password
  - Admin-only all-users list
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from .models import User


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def create_user(username='testuser', password='StrongPass1!', role='viewer', **kwargs):
    return User.objects.create_user(username=username, password=password, role=role, **kwargs)


def get_tokens(client, username='testuser', password='StrongPass1!'):
    url = reverse('login')
    resp = client.post(url, {'username': username, 'password': password}, format='json')
    return resp.data.get('access'), resp.data.get('refresh')


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

class RegisterTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('register')

    def test_register_success(self):
        data = {
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'StrongPass1!',
            'password2': 'StrongPass1!',
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)
        self.assertEqual(resp.data['user']['username'], 'newuser')
        self.assertEqual(resp.data['user']['role'], 'viewer')  # default role

    def test_register_password_mismatch(self):
        data = {
            'username': 'user2',
            'email': 'u2@example.com',
            'password': 'StrongPass1!',
            'password2': 'WrongPass2!',
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_password_too_short(self):
        data = {
            'username': 'user3',
            'email': 'u3@example.com',
            'password': 'short',
            'password2': 'short',
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_duplicate_username(self):
        create_user(username='taken')
        data = {
            'username': 'taken',
            'email': 'taken@example.com',
            'password': 'StrongPass1!',
            'password2': 'StrongPass1!',
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_register_missing_fields(self):
        resp = self.client.post(self.url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)


# ---------------------------------------------------------------------------
# Login / JWT
# ---------------------------------------------------------------------------

class LoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.url = reverse('login')

    def test_login_success(self):
        resp = self.client.post(self.url, {'username': 'testuser', 'password': 'StrongPass1!'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)
        self.assertIn('refresh', resp.data)

    def test_login_wrong_password(self):
        resp = self.client.post(self.url, {'username': 'testuser', 'password': 'wrong'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_nonexistent_user(self):
        resp = self.client.post(self.url, {'username': 'nobody', 'password': 'pass'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Token Refresh
# ---------------------------------------------------------------------------

class TokenRefreshTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        _, self.refresh = get_tokens(self.client)
        self.url = reverse('token_refresh')

    def test_refresh_success(self):
        resp = self.client.post(self.url, {'refresh': self.refresh}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertIn('access', resp.data)

    def test_refresh_invalid_token(self):
        resp = self.client.post(self.url, {'refresh': 'badtoken'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Logout
# ---------------------------------------------------------------------------

class LogoutTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.access, self.refresh = get_tokens(self.client)
        self.url = reverse('logout')

    def test_logout_success(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access}')
        resp = self.client.post(self.url, {'refresh': self.refresh}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_logout_invalid_token(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access}')
        resp = self.client.post(self.url, {'refresh': 'invalidtoken'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_logout_unauthenticated(self):
        resp = self.client.post(self.url, {'refresh': self.refresh}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Profile
# ---------------------------------------------------------------------------

class ProfileTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(email='test@example.com')
        self.access, _ = get_tokens(self.client)
        self.url = reverse('profile')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access}')

    def test_get_profile(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['username'], 'testuser')
        self.assertEqual(resp.data['email'], 'test@example.com')

    def test_update_profile_bio(self):
        resp = self.client.patch(self.url, {'bio': 'Hello world'}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['bio'], 'Hello world')

    def test_profile_unauthenticated(self):
        self.client.credentials()
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# Public Profile
# ---------------------------------------------------------------------------

class PublicProfileTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user(username='publicuser')

    def test_public_profile_success(self):
        url = reverse('public_profile', kwargs={'username': 'publicuser'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertEqual(resp.data['username'], 'publicuser')
        # Should NOT expose sensitive fields
        self.assertNotIn('email', resp.data)
        self.assertNotIn('password', resp.data)

    def test_public_profile_not_found(self):
        url = reverse('public_profile', kwargs={'username': 'nobody'})
        resp = self.client.get(url)
        self.assertEqual(resp.status_code, status.HTTP_404_NOT_FOUND)


# ---------------------------------------------------------------------------
# Change Password
# ---------------------------------------------------------------------------

class ChangePasswordTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = create_user()
        self.access, _ = get_tokens(self.client)
        self.url = reverse('change_password')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access}')

    def test_change_password_success(self):
        data = {
            'old_password': 'StrongPass1!',
            'new_password': 'NewStrongPass2!',
            'new_password2': 'NewStrongPass2!',
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_200_OK)

    def test_change_password_wrong_old(self):
        data = {
            'old_password': 'WrongOld!',
            'new_password': 'NewStrongPass2!',
            'new_password2': 'NewStrongPass2!',
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_new_mismatch(self):
        data = {
            'old_password': 'StrongPass1!',
            'new_password': 'NewPass2!',
            'new_password2': 'DifferentPass3!',
        }
        resp = self.client.post(self.url, data, format='json')
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)

    def test_change_password_unauthenticated(self):
        self.client.credentials()
        resp = self.client.post(self.url, {}, format='json')
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)


# ---------------------------------------------------------------------------
# All Users (admin only)
# ---------------------------------------------------------------------------

class AllUsersTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.admin = User.objects.create_superuser(username='admin', password='AdminPass1!')
        self.user = create_user(username='normaluser')
        self.url = reverse('all_users')

    def _auth(self, username, password):
        resp = self.client.post(reverse('login'), {'username': username, 'password': password}, format='json')
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {resp.data["access"]}')

    def test_admin_can_list_users(self):
        self._auth('admin', 'AdminPass1!')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_200_OK)
        self.assertTrue(len(resp.data) >= 2)

    def test_regular_user_cannot_list_users(self):
        self._auth('normaluser', 'StrongPass1!')
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_unauthenticated_cannot_list_users(self):
        resp = self.client.get(self.url)
        self.assertEqual(resp.status_code, status.HTTP_401_UNAUTHORIZED)
