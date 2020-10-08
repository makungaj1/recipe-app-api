from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse

from rest_framework.test import APIClient
from rest_framework import status

CREATE_USER_URL = reverse('user:create')
TOKEN_URL = reverse('user:token')


def create_user(**params):
    return get_user_model().objects.create_user(**params)


class PublicUserAPITests(TestCase):
    """Test the users API (public)"""

    def setUp(self):
        self.client = APIClient()

    def test_create_valid_user_success(self):
        """Test create user with valid payload is success"""
        payload = {
            'email': 'test@newuser.com',
            'password': 'passwordTest123',
            'name': 'Test Name'
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
        payload = {'email': 'test@userexists.com', 'password': 'testPassword123'}
        create_user(**payload)

        res = self.client.post(CREATE_USER_URL, payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_password_restriction(self):
        """Test that the password must be more than 5 chars"""
        payload = {'email': 'test@shortpassword.com', 'password': 'pwd', 'name': 'test name'}
        res = self.client.post(CREATE_USER_URL, payload)

        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
        user_exits = get_user_model().objects.filter(
            email=payload['email']
        ).exists()

        self.assertFalse(user_exits)

    def test_create_token_for_user(self):
        """Test that a token is created"""
        payload = {'email': 'test@shortpassword.com', 'password': 'testPass'}
        create_user(**payload)
        res = self.client.post(TOKEN_URL, payload)

        self.assertIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_create_token_with_invalid_credentials(self):
        """Token should not be created with invalid credentials"""
        create_user(email='test@testemail.com', password='testPass')
        payload = {'email': 'test@testemail', 'password': 'wrongPassword'}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_with_no_user(self):
        """Test that token is not created if user does not exists"""
        payload = {'email': 'test@testemail.com', 'password': 'testPassword'}
        res = self.client.post(TOKEN_URL, payload)

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_token_missing_field(self):
        """Test that email and password are required"""
        res = self.client.post(TOKEN_URL, {'email': 'one', 'password': ''})

        self.assertNotIn('token', res.data)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)
