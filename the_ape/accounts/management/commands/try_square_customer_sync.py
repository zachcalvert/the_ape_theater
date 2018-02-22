from __future__ import unicode_literals

import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from accounts.models import UserProfile
from square_payments.models import SquareCustomer


class Command(BaseCommand):

    def add_arguments(self, parser):
        parser.add_argument('profile_id')

    def handle(self, profile_id, *args, **options):
        """
        """
        profile = UserProfile.objects.get(id=profile_id)
        try:
            customer = SquareCustomer.objects.get(email=profile.user.email)
        except SquareCustomer.DoesNotExist:
            return

        if customer.profile is None:
            customer.profile = profile
            customer.save()
