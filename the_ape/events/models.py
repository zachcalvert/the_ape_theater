from datetime import datetime, timedelta

from django.core.management import call_command
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import timezone

WEEKDAYS = (
    (1, 'Monday'),
    (2, 'Tuesday'),
    (3, 'Wednesday'),
    (4, 'Thursday'),
    (5, 'Friday'),
    (6, 'Saturday'),
    (7, 'Sunday'),
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
    videos = models.ManyToManyField('pages.VideoWidget', blank=True)

    class Meta:
        ordering = ['-start_time']

    def __str__(self):
        return self.name

    @property
    def name_with_date(self):
        return '{}: {}'.format(self.name, self.event_day())

    @property
    def slug(self):
        return slugify(self.name)

    def get_api_url(self):
        return reverse('event', kwargs={'event_id': self.pk})

    def get_absolute_url(self):
        return reverse('event_wrapper', kwargs={'event_id': self.pk})

    def event_day(self):
        """
        Provide a user-friendly representation of the event start day
        """
        day = ''
        start_time = timezone.localtime(self.start_time)
        if start_time.date() == datetime.today().date():
            return '<b style="color:red">TONIGHT</b>'
        elif start_time.date() == datetime.today().date() + timedelta(days=1):
            return 'Tomorrow'
        else:
            day_index = start_time.date().weekday()
            day = WEEKDAYS[day_index][1]
            month_index = start_time.month - 1
            month = MONTHS[month_index][1]
            day += ', {month} {date}'.format(month=month,
                                             date=start_time.day)
            return day

    def event_time(self):
        pm = False
        hour = timezone.localtime(self.start_time).time().hour
        if hour >= 12:
            pm = True
            hour -= 12
            return '{} pm'.format(hour)
        else:
            return '{} am'.format(hour)

    def to_data(self):
        data = {
            "id": self.id,
            "name": self.name,
            "bio": self.bio,
            "event_time": self.event_time(),
            "event_day": self.event_day(),
            "ticket_price": self.ticket_price,
            "name_with_date": self.name_with_date,
            "tickets_left": self.max_tickets - self.tickets_sold
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
