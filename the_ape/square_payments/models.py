import squareconnect
from squareconnect.apis.transactions_api import TransactionsApi

from django.conf import settings
from django.db import models

# Create your models here.

api_instance = TransactionsApi()


class SquareError(models.Model):
    payment = models.ForeignKey(SquarePayment)
    date = models.DatTimeField(auto_now_add=True)
    message = models.CharField(max_length=500)


class SquareCustomer(models.Model):
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    profile = models.ForeignKey(UserProfile)


class SquarePayment(models.Model):
    customer = models.ForeignKey(SquareCustomer)
    uuid = models.CharField(max_length=50)
    amount = models.IntegerField()
    currency = models.CharField(max_length=5, default='USD')

    def get_card_nonce(self):
        return 'fake-card-nonce-ok'

    def construct_square_request(self):
        amount = {'amount': self.amount, 'currency': self.currency}
        nonce = self.get_card_nonce()
        body = {
            'idempotency_key': str(self.uuid),
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
            SquareError.objects.create(payment=self, message=e)
