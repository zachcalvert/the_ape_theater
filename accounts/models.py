import datetime
from decimal import Decimal
import json
import logging


from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import User
from django.db import models
# Create your models here.


USER_PERMISSIONS = {
    'super_admin': {
        'label': "Super Admin",
        'descr': "Grants access to view and manage everything on the site.",
    },
    'ape_admin': {
        'label': "Ape Admin",
        'descr': "Grants access to manage pages and events, but not people or groups."
    },
}


class UserProfileQuerySet(models.query.QuerySet):
    """
    Expose a simple API for searching UserProfile instances.
    """

    def search(self, search_string):
        query = (
            Q(user__first_name__icontains=search_string) |
            Q(user__last_name__icontains=search_string) |
            Q(user__username__icontains=search_string) |
            Q(user__email__icontains=search_string)
        )
        return self.filter(query)


class UserProfileManager(models.Manager):
    """
    Custom Manager to leverage the search functionality provided by UserProfileQuerySet.
    """
    def get_queryset(self):
        return UserProfileQuerySet(self.model, using=self._db)

    def search(self, search_string):
        return self.get_queryset().search(search_string)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    objects = UserProfileManager()

    # super_admin gives all permissions to everything.
    super_admin = models.BooleanField(default=False)
    # devops_admins can manage all pages and events, but not all groups or people
    ape_admin = models.BooleanField(default=False)

    # Datetime of last activity as determined by the UserActivityMiddleware
    # Used to send count of daily active users in heart beat
    last_activity_time = models.DateTimeField(
        help_text="Time stamp of last activity through the Ape UI.",
        null=True,
        blank=True
    )

    @property
    def username(self):
        return self.user.username

    @username.setter
    def username(self, value):
        raise AttributeError("The username should be set on the User object, "
                             "not UserProfile.")

    @property
    def password(self):
        return self.user.password

    @password.setter
    def password(self, value):
        raise AttributeError("The password should be set on the User object, "
                             "not UserProfile.")

    @property
    def is_ape_admin(self):
        return self.super_admin or self.ape_admin

    def has_permission(self, perm, object):
        return (perm in get_ape_permissions(self, object))
