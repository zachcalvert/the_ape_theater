from __future__ import unicode_literals

import os

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand

from square_payments.models import SquareCustomer


class Command(BaseCommand):

    def handle(self, *args, **options):
        """
        For each SqareCustomer without an associated profile, see if an account
        has been created with the same email, and if so, link them up.
        """
        for customer in SquareCustomer.objects.filter(profile__isnull=True):
            user = User.objects.filter(email=customer.email).first()
            if user:
                print("syncing user: {} with square customer: {}".format(user, customer))
                customer.profile = user.profile
                customer.save()

                if not user.first_name:
                    user.first_name = customer.first_name
                if not user.last_name:
                    user.last_name = customer.last_name

                user.save()
