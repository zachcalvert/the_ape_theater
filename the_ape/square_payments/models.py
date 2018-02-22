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


class SquareCustomer(models.Model):
    first_name = models.CharField(max_length=40, null=True, blank=True)
    last_name = models.CharField(max_length=40, null=True, blank=True)
    email = models.CharField(max_length=60, null=True, blank=True)
    profile = models.ForeignKey(UserProfile, null=True, blank=True, related_name='square_purchaser')

    def __str__(self):
        return '{} {} - {}'.format(self.first_name, self.last_name, self.email)


class SquarePayment(models.Model):
    customer = models.ForeignKey(SquareCustomer, related_name='payments')
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
        return 'Purchase by {} for {} on {}'.format(self.customer, self.amount, self.created)

    @property
    def purchase(self):
        if self.purchase_event_id is not None:
            return self.purchase_event
        if self.purchase_class_id is not None:
            return self.purchase_class
        raise AssertionError("Neither 'purchase_event' nor 'purchase_class' is set")

    def get_fake_card_nonce(self):
        return 'fake-card-nonce-ok'

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
            print ('Exception when calling TransactionApi->charge: %s\n' % e)
            self.error_message = str(e)
            self.save()
            return False

        self.completed = True
        self.save()
        return True

    # def clean(self):
    #     if self.purchase_event and self.purchase_class:
    #         raise AssertionError("Both 'purchase_event' and 'purchase_class' are set")
    #     if not self.purchase_event and not self.purchase_class:
    #         raise AssertionError("Neither 'purchase_event' nor 'purchase_class' is set")
