import squareconnect
from squareconnect.rest import ApiException
from squareconnect.apis.transactions_api import TransactionsApi

from django.conf import settings
from django.db import models

from accounts.models import UserProfile
from classes.models import ApeClass
from events.models import Event

squareconnect.configuration.access_token = settings.SQUARE_ACCESS_TOKEN
api_instance = TransactionsApi()


class SeatReservation(models.Model):
    """
    Used in lieu of SquarePayment when a show/class is free.
    """
    customer = models.ForeignKey(UserProfile, null=True, related_name='reservations')
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.CharField(max_length=50)

    reserved_event = models.ForeignKey(Event, null=True, blank=True)
    reserved_class = models.ForeignKey(ApeClass, null=True, blank=True)

    @property
    def reservation(self):
        """
        A SeatReservation can either be for an ApeClass, or an Event. It must be for one of
        these things, not both of them and not 0 of them.
        """
        if self.reserved_event_id is not None:
            return self.reserved_event.name_with_date
        if self.reserved_class_id is not None:
            return self.reserved_class
        raise AssertionError("Neither 'reserved_event' nor 'reserved_class' is set")


class SquarePayment(models.Model):
    customer = models.ForeignKey(UserProfile, null=True, related_name='payments')
    created = models.DateTimeField(auto_now_add=True)
    uuid = models.CharField(max_length=50)
    amount = models.IntegerField()
    currency = models.CharField(max_length=5, default='USD')
    nonce = models.CharField(max_length=200)
    completed = models.BooleanField(default=False)
    error_message = models.CharField(max_length=1000, null=True, blank=True)

    purchase_event = models.ForeignKey(Event, null=True, blank=True)
    purchase_class = models.ForeignKey(ApeClass, null=True, blank=True)

    class Meta:
        ordering = ['-created']

    def __str__(self):
        return 'Purchase by {} on {}'.format(self.customer, self.created.date())

    @property
    def purchase(self):
        """
        A SquarePayment can either be for an ApeClass, or an Event. It must be for one of
        these things, not both of them and not 0 of them.
        """
        if self.purchase_event_id is not None:
            return self.purchase_event.name_with_date
        if self.purchase_class_id is not None:
            return self.purchase_class
        raise AssertionError("Neither 'purchase_event' nor 'purchase_class' is set")

    def construct_square_request(self):
        amount = {'amount': self.amount, 'currency': self.currency}
        nonce = self.nonce
        body = {
            'idempotency_key': self.uuid,
            'card_nonce': nonce,
            'amount_money': amount
        }
        return body

    def charge(self):
        location_id = settings.SQUARE_LOCATION_ID
        body = self.construct_square_request()

        try:
            api_response = api_instance.charge(location_id, body)
        except ApiException as e:
            print('Exception when calling TransactionApi->charge: {}\n'.format(e))
            self.error_message = str(e)
            self.save()
            return False

        self.completed = True
        self.save()
        return True
