from django.db import models
from django.contrib.auth.models import User

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
    def shows(self):
        from square_payments.models import SquareCustomer
        customer = SquareCustomer.objects.filter(profile=self).first()
        if customer:
            return customer.shows.all()
        return None


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
        pass

    def send_event_email(self):
        pass
