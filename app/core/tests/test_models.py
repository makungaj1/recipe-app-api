from django.test import TestCase
from django.contrib.auth import get_user_model

class ModelTests(TestCase):
    """docstring for ModelTests"""

    def test_create_user_with_email_successful(self):
        """ Test creating a new user with an email """
        email = 'test@validemail.com'
        password = 'Testpass123'
        user = get_user_model().objects.create_user(
        email = email,
        password = password
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))

    def test_new_user_email_normalize(self):
        """ Test the email for new user is normalize """
        email = 'test@Validemail.com'
        user = get_user_model().objects.create_user(email, 'Testpass123')

        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        """ Test creating user with no email raises error """
        with self.assertRaises(ValueError):
            get_user_model().objects.create_user(None, 'test1234password')

    def test_create_new_super_user(self):
        """ Test creating a new superuser """
        user = get_user_model().objects.create_superuser(
        'test@superuser.com',
        'test123password'
        )

        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
