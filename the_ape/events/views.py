from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse

from accounts.models import EventAttendee
from events.forms import EventTicketPurchaseForm
from events.models import Event


@login_required
def event_ticket_purchase(request, event_id):
    user = request.user
    event = Event.objects.get(id=event_id)
    if request.method == 'GET':
        form = EventTicketPurchaseForm()
        return render(request, 'events/event_ticket_purchase.html', {'event': event, 'form': form})

    if request.method == 'POST':
        form = EventTicketPurchaseForm(data=request.POST)
        if form.is_valid():
            num_tickets = form.cleaned_data['num_tickets']
            EventAttendee.objects.create(event=event, attendee=user.profile)
            messages.add_message(request, messages.SUCCESS,
                                 'Woohoo! Your ticket to {} is in the bag.'.format(event.name))

    return redirect(reverse('event_wrapper', kwargs={'event_id': event.id}))
