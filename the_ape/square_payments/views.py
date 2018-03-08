from decimal import Decimal
import random
import string
from uuid import uuid4

from squareconnect.rest import ApiException

from django.contrib.auth.models import User
from django.contrib import messages
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render
from django.urls import reverse

from accounts.models import ClassMember, EventAttendee, UserProfile
from classes.models import ApeClass
from events.models import Event
from square_payments.models import SquarePayment


def process_card(request):

    if request.method == 'POST':
        guest_purchase = False

        # if user not authenticated
        if not request.user.is_authenticated:
            guest_purchase = True
            user = User.objects.create_user(
                first_name=request.POST['first-name'],
                last_name=request.POST['last-name'],
                email=request.POST['email-address'],
                username=request.POST['email-address'],
                password=''.join(random.choices(string.ascii_uppercase + string.digits, k=12))
            )
            UserProfile.objects.create(user=user)
        else:
            user = request.user

        nonce = request.POST['nonce']

        purchase_model = request.POST['purchase-model']
        purchase_id = request.POST['purchase-id']
        purchase_for = request.POST['purchase-for']

        num_tickets = request.POST['num-tickets']
        amount = request.POST['amount']
        amount += '00' # convert to cents
        amount = int(amount)

        payment = SquarePayment.objects.create(
            uuid=str(uuid4()),
            customer=user.profile,
            amount=amount,
            nonce=nonce
        )

        if purchase_model == 'ape_class':
            payment.purchase_class = ApeClass.objects.get(id=purchase_id)
        elif purchase_model == 'event':
            payment.purchase_event = Event.objects.get(id=purchase_id)
        payment.save()

        success = payment.charge()
        if success:
            messages.success(request, 'Your purchase for {} has been processed and was ' \
                                      'successful.'.format(purchase_for))
        else:
            messages.error(request, 'Your purchase for {} was not successful. Your card was ' \
                                    'not charged, please contact talktotheape@gmail.com for further details.'.format(purchase_for))
            return HttpResponseRedirect(reverse('home'))

        #  handle successful purchases
        if purchase_model == 'ape_class':
            class_member = ClassMember.objects.create(student=user.profile, ape_class=ape_class)
            class_member.create_registration()
            class_member.send_registration_email()
            redirect_url = reverse('ape_class_wrapper', kwargs={'ape_class_id': payment.purchase_class.id})        

        elif purchase_model == 'event':
            payment.purchase_event.tickets_sold += int(num_tickets)
            payment.purchase_event.save()
            redirect_url = reverse('event_wrapper', kwargs={'event_id': payment.purchase_event.id})

            attendee, created = EventAttendee.objects.get_or_create(event=payment.purchase_event, attendee=user.profile)
            attendee.create_ticket(num_tickets)
            attendee.send_event_email()

        payment.save()

        return HttpResponseRedirect(redirect_url)
