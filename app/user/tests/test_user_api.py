from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

# ENDPOINTS
CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')
ME_URL = reverse('user:me')

# USER VARIABLES (TEST)
# Emails
VALID_EMAIL = 'test@jmits.com'
INVALID_EMAIL = 'test@'
# Passwords
VALID_PASSWORD = 'testPassword123'
INVALID_PASSWORD = 'pwd'
WRONG_PASSWORD = 'wrongPassword'
# Name
NAME = 'Test Name'


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserAPITests(TestCase):
    """Test the users API (public)"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test create user with valid payload is success"""
        payload = {
            'email': VALID_EMAIL,
            'password': VALID_PASSWORD,
            'name': NAME
        }

        """Make HTTP POST request api/user/"""
        res = self.client.post(CREATE_USER_URL, payload)

        """Assert that the user was successful created"""
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)

        """Compare passwords (from db and payload)"""
        user = get_user_model().objects.get(**res.data)
        self.assertTrue(user.check_password(payload['password']))

        """Check that the password is not return in the data"""
        self.assertNotIn('password', res.data)

    def test_user_exists(self):
        """Test that create an existing user failed"""
        payload = {'email': VALID_EMAIL, 'password': VALID_PASSWORD}
        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_restriction(self):
        """Test that the password must be more than 5 chars"""
        payload = {'email': VALID_EMAIL, 'password': INVALID_PASSWORD, 'name': NAME}
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exits = get_user_model().objects.filter(
            email=payload['email']
        ).exists()

        self.assertFalse(user_exits)

    def test_create_token_for_user(self):
        """Test that a token is created"""
        payload = {'email': VALID_EMAIL, 'password': VALID_PASSWORD}
        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_with_invalid_credentials(self):
        """Token should not be created with invalid credentials"""
        create_user(email=VALID_EMAIL, password=VALID_PASSWORD)
        payload = {'email': VALID_EMAIL, 'password': WRONG_PASSWORD}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_with_no_user(self):
        """Test that token is not created if user does not exists"""
        payload = {'email': VALID_EMAIL, 'password': VALID_PASSWORD}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        """Test that email and password are required"""
        res = self.client.post(TOKEN_URL, {'email': INVALID_EMAIL, 'password': INVALID_PASSWORD})

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_retrieve_user_unauthorized(self):
        """Test that authentication is required for user"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)


class PrivateUserApiTests(TestCase):
    """Test API requests that require AUTH"""

    def setUp(self):
        self.user = create_user(
            email=VALID_EMAIL,
            password=VALID_PASSWORD,
            name=NAME,
        )
        self.client = APIClient()
        self.client.force_authenticate(user=self.user)

    def test_retrieve_profile_success(self):
        """Test retrieving profile for logged in user"""
        res = self.client.get(ME_URL)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data, {
            'name': self.user.name,
            'email': self.user.email
        })

    def test_post_me_not_allowed(self):
        """Test that POST is not allowed"""
        res = self.client.post(ME_URL, {})

        self.assertEqual(res.status_code, status.HTTP_405_METHOD_NOT_ALLOWED)

    def test_update_user_profile(self):
        """Test updating user profile for authenticated user"""
        payload = {'name': 'new name', 'password': 'newPassword'}

        res = self.client.patch(ME_URL, payload)

        # Refresh the user object to reflect the updated db
        self.user.refresh_from_db()

        self.assertEqual(self.user.name, payload['name'])
        self.assertTrue(self.user.check_password(payload['password']))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
