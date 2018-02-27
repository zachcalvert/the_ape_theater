import pdfkit
from uuid import uuid4

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

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

    def send_registration_email(self):
        pass


class EventAttendee(models.Model):
    attendee = models.ForeignKey(UserProfile, related_name='event_attendance', null=True)
    event = models.ForeignKey(Event, related_name='event_attendance', null=True)
    purchase_date = models.DateTimeField(auto_now_add=True)

    def create_ticket(self):
        ticket, created = Ticket.objects.get_or_create(event_attendee=self)
        if created:
            ticket.uuid = str(uuid4()).replace('-', '')
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

    def send_event_email(self):
        pass


class Ticket(models.Model):
    event_attendee = models.OneToOneField(EventAttendee, related_name='ticket')
    uuid = models.CharField(max_length=100)
    pdf = models.FileField(upload_to='tickets', null=True)

    def get_absolute_url(self):
        return reverse('ticket', kwargs={'ticket_uuid': self.uuid})
