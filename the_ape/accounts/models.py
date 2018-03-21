import pdfkit
from uuid import uuid4

from django.core.mail import send_mail, EmailMultiAlternatives
from django.db import models
from django.contrib.auth.models import User
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils.html import strip_tags


from classes.models import ApeClass
from events.models import Event


class UserProfile(models.Model):
    """
    A user profile model for tracking additional user metadata.
    """
    user = models.OneToOneField(User, related_name='profile')
    classes = models.ManyToManyField(ApeClass, through='ClassMember', related_name='students')
    shows = models.ManyToManyField(Event, through='EventAttendee', related_name='attendees')

    def __str__(self):
        return u'%s <%s>' % (self.user.get_full_name(), self.user.email,)

    def get_absolute_url(self):
        return reverse('user_profile', kwargs={'user_id': self.user.pk})

    @property
    def full_name(self):
        return '{} {}'.format(self.user.first_name, self.user.last_name)


class ClassMember(models.Model):
    student = models.ForeignKey(UserProfile, related_name='class_membership')
    ape_class = models.ForeignKey(ApeClass, related_name='class_membership', null=True)
    has_paid = models.BooleanField(default=False)

    def create_registration(self):
        registration, created = ClassRegistration.objects.get_or_create(class_member=self)
        if created:
            registration.uuid = registration.id * 52689
            registration.save()
        if registration.pdf:
            pass
            # url = 'http://localhost:8000{}'.format(reverse('ticket', kwargs={'ticket_uuid': ticket.uuid}))
            # try:
            #     pdf = pdfkit.from_url(url, '{}.pdf'.format(ticket.uuid))
            #     ticket.pdf = pdf
            # except Exception as e:
            #     print(e)
            # ticket.save()

    def send_registration_email(self, registration):
        subject = 'Class registration confirmation: {}'.format(self.ape_class.name)
        from_address = 'noreply@theapetheater.org'
        to_address = self.student.user.email
        html_content = render_to_string('accounts/class_email_confirmation.html', {'class_registration': registration, 'ape_class': self.ape_class, 'student': self.student}) # render with dynamic value
        text_content = strip_tags(html_content)
        msg = EmailMultiAlternatives(subject, text_content, from_address, [to_address])
        msg.attach_alternative(html_content, "text/html")
        msg.send()


class ClassRegistration(models.Model):
    class_member = models.OneToOneField(ClassMember, related_name='registration')
    uuid = models.CharField(max_length=100)
    pdf = models.FileField(upload_to='class_registrations', null=True)

    def get_absolute_url(self):
        return reverse('class_registration', kwargs={'registration_uuid': self.uuid})


class EventAttendee(models.Model):
    attendee = models.ForeignKey(UserProfile, related_name='event_attendance', null=True)
    event = models.ForeignKey(Event, related_name='event_attendance', null=True)
    purchase_date = models.DateTimeField(auto_now_add=True)

    def create_ticket(self, num_tickets=1):
        ticket, created = Ticket.objects.get_or_create(event_attendee=self)
        if created:
            ticket.uuid = ticket.id * 52689
            ticket.num_attendees = num_tickets
            ticket.save()
        if ticket.pdf:
            pass
            # url = 'http://localhost:8000{}'.format(reverse('ticket', kwargs={'ticket_uuid': ticket.uuid}))
            # try:
            #     pdf = pdfkit.from_url(url, '{}.pdf'.format(ticket.uuid))
            #     ticket.pdf = pdf
            # except Exception as e:
            #     print(e)
            # ticket.save()
        return ticket

    def send_event_email(self, ticket):
        subject = 'Ticket confirmation: {}'.format(self.event.name)
        from_address = 'noreply@theapetheater.org'
        to_address = self.attendee.user.email
        html_content = render_to_string('accounts/ticket_email_confirmation.html', {'ticket': ticket,
                                                                                    'event': self.event,
                                                                                    'attendee': self.attendee,
                                                                                    'total': int(self.event.ticket_price) * ticket.num_attendees})
        text_content = strip_tags(html_content)
        msg = EmailMultiAlternatives(subject, text_content, from_address, [to_address])
        msg.attach_alternative(html_content, "text/html")
        msg.send()


class Ticket(models.Model):
    event_attendee = models.OneToOneField(EventAttendee, related_name='ticket')
    uuid = models.CharField(max_length=100)
    pdf = models.FileField(upload_to='tickets', null=True)
    num_attendees = models.IntegerField(default=1)

    def get_absolute_url(self):
        return reverse('ticket', kwargs={'ticket_uuid': self.uuid})
