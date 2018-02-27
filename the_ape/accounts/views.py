from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView
from django.contrib.auth.models import User
from django.core.urlresolvers import reverse

from accounts.models import Ticket, ClassRegistration


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
        return context


class ClassRegistrationView(TemplateView):
    template_name = 'accounts/class_registration.html'

    def get_context_data(self, **kwargs):
        context = super(ClassRegistrationView, self).get_context_data(**kwargs)
        class_registration = ClassRegistration.objects.get(uuid=kwargs.get('registration_uuid'))
        ape_class = class_registration.class_member.ape_class
        student = class_registration.class_member.student
        context['ape_class'] = ape_class
        context['class_registration'] = class_registration
        return context
