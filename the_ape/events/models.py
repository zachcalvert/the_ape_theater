import pytz
from datetime import datetime, timedelta

from django.core.management import call_command
from django.db import models
from django.urls import reverse

WEEKDAYS = (
    (0, 'Monday'),
    (1, 'Tuesday'),
    (2, 'Wednesday'),
    (3, 'Thursday'),
    (4, 'Friday'),
    (5, 'Saturday'),
    (6, 'Sunday'),
)

MONTHS = (
    (1, 'January'),
    (2, 'February'),
    (3, 'March'),
    (4, 'April'),
    (5, 'May'),
    (6, 'June'),
    (7, 'July'),
    (8, 'August'),
    (9, 'September'),
    (10, 'October'),
    (11, 'November'),
    (12, 'December'),
)


class Event(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField()
    start_time = models.DateTimeField(null=True)
    max_tickets = models.IntegerField(null=True)
    tickets_sold = models.IntegerField(default=0)
    ticket_price = models.DecimalField(decimal_places=2, max_digits=5)
    banner = models.ForeignKey('pages.BannerWidget', null=True, blank=True)

    class Meta:
        ordering = ['start_time']

    def __str__(self):
        return self.name

    @property
    def name_with_date(self):
        return '{}: {}'.format(self.name, self.event_day())

    def get_api_url(self):
        return reverse('event', kwargs={'event_id': self.pk})

    def get_absolute_url(self):
        return reverse('event_wrapper', kwargs={'event_id': self.pk})

    def event_day(self):
        """
        Provide a user-friendly representation of the event start day
        """
        day = ''
        time = ''
        if self.start_time.date() == datetime.today():
            day = 'Tonight'
        elif self.start_time.date() == datetime.today() + timedelta(days=1):
            day = 'Tomorrow'
        else:
            # if it's within a week
            if self.start_time.date() <= datetime.today().date() + timedelta(days=6):
                day = 'This '
                day_index = self.start_time.date().weekday()
                day += WEEKDAYS[day_index][1]
            else:
                day_index = self.start_time.date().weekday()
                day = WEEKDAYS[day_index][1]
                month_index = self.start_time.month - 1
                month = MONTHS[month_index][1]
                day += ', {month} {date}'.format(month=month,
                                                 date=self.start_time.day)

        return day

    def to_data(self):
        data = {
            "id": self.id,
            "name": self.name,
            "bio": self.bio,
            "start_time": self.start_time,
            "event_day": self.event_day(),
            "ticket_price": self.ticket_price,
            "name_with_date": self.name_with_date
        }
        if self.banner:
            data['banner_url'] = self.banner.image.url

        return data

    def save(self, *args, **kwargs):
        """
        We collect static when banners change because it seems easier than
        implementing webpack
        """
        collectstatic = False

        if self.pk is not None:
            orig = Event.objects.get(pk=self.pk)
            if orig.banner != self.banner:
                print('banner changed')
                collectstatic = True
        else:
            collectstatic = True  # this is a newly created instance

        super(Event, self).save(*args, **kwargs)
        if collectstatic:
            call_command('collectstatic', verbosity=1, interactive=False)
