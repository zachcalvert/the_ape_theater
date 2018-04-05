from django.contrib.auth.models import User
from django.test import TestCase


class UserProfileTest(TestCase):
    """
    Tests how the user's profile page works and displays classes and shows
    """

    def setUp(self):
        if not User.objects.filter(username="admin").exists():
            User.objects.create_superuser("admin", "admin@example.com", "admin")
        self.client.login(username="admin", password="admin")

        self.regular_user = User.objects.create_user('regular_joe', 'regular_joe@hotmail.net', '12345678')
