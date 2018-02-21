from decimal import Decimal
from uuid import uuid4

from squareconnect.rest import ApiException

from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from square_payments.models import SquareCustomer, SquarePayment


def process_card(request):

	if request.method == 'POST':
		user = request.user
		purchase_for = request.POST['purchase-for']
		nonce = request.POST['nonce']
		amount = request.POST['amount']
		amount = int(amount.replace('.', '')) # convert to cents, integer
		customer, created = SquareCustomer.objects.get_or_create(profile=user.profile)

		payment_uuid = str(uuid4())
		payment = SquarePayment.objects.create(
			uuid=payment_uuid,
			customer=customer,
			amount=amount,
			nonce=nonce
		)

		success = payment.charge()
		if success:
			messages.success(request, 'Your purchase for {} has been processed and was ' \
				                      'successful.'.format(purchase_for))
		else:
			messages.error(request, 'Your purchase for {} was not successful. Your card was ' \
				                    'not charged, please contact talktotheape@gmail.com for further details.'.format(purchase_for))
			return HttpResponseRedirect(reverse('home'))

		# do some more stuff with incrementing purchases for event, class, etc
		return HttpResponseRedirect(reverse('home'))
