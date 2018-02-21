from decimal import Decimal
from uuid import uuid4

from squareconnect.rest import ApiException

from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from accounts.models import ClassMember, EventAttendee
from classes.models import ApeClass
from events.models import Event
from square_payments.models import SquareCustomer, SquarePayment


def process_card(request):

    if request.method == 'POST':
        user = request.user
        nonce = request.POST['nonce']
        purchase_for = request.POST['purchase-for']

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
        purchase_model = request.POST['purchase-model']
        purchase_id = request.POST['purchase-id']

        if purchase_model == 'ape_class':
            ape_class = ApeClass.objects.get(id=purchase_id)
            payment.purchase_class = ape_class
            ClassMember.objects.create(student=user.profile, ape_class=ape_class)
            redirect_url = reverse('ape_class_wrapper', kwargs={'ape_class_id': ape_class.id})

        elif purchase_model == 'event':
            event = Event.objects.get(id=purchase_id)
            attendee, created = EventAttendee.objects.get_or_create(event=event, attendee=user.profile)
            if created:
                attendee.create_ticket()

            payment.purchase_event = event
            event.tickets_sold += 1
            event.save()
            redirect_url = reverse('event_wrapper', kwargs={'event_id': event.id})

        payment.save()

        return HttpResponseRedirect(redirect_url)
