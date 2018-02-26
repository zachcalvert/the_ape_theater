from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from accounts.models import Ticket


class UserProfileView(TemplateView):
    template_name = 'accounts/user_profile.html'

    def get_context_data(self, **kwargs):
        context = super(UserProfileView, self).get_context_data(**kwargs)
        if self.request.user.is_authenticated():
            user = get_object_or_404(User, pk=self.request.user.pk)
        else:
            return reverse('auth_login')

        context['user'] = user
        return context


class TicketView(TemplateView):
    template_name = 'accounts/ticket.html'

    def get_context_data(self, **kwargs):
        context = super(TicketView, self).get_context_data(**kwargs)
        ticket = Ticket.objects.get(uuid=kwargs.get('ticket_uuid'))
        event = ticket.event_attendee.event
        attendee = ticket.event_attendee.attendee
        context['ticket'] = ticket
        context['event'] = event
        context['attendee'] = attendee
        return context
