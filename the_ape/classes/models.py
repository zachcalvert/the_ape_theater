import pytz
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


class ApeClass(models.Model):
    TYPE_CHOICES = (
        ('IMPROV', 'Improv'),
        ('SKETCH', 'Sketch'),
        ('ACTING', 'Acting'),
        ('WORKSHOP', 'Workshop'),
    )

    name = models.CharField(max_length=50)
    bio = models.TextField()
    class_type = models.CharField(choices=TYPE_CHOICES, max_length=50)
    banner = models.ForeignKey('pages.BannerWidget', null=True, blank=True)

    teacher = models.ForeignKey('people.Person', null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    num_sessions = models.IntegerField(help_text='Number of Sessions', default=4)
    max_enrollment = models.IntegerField(help_text='Max number of students', default=12)
    class_length = models.IntegerField(default=2, help_text='Length of one class session, in hours.')
    price = models.DecimalField(decimal_places=2, max_digits=5)
    registration_open = models.BooleanField(default=True)

    class Meta(object):
        verbose_name = 'Ape Class'
        verbose_name_plural = 'Ape Classes'

    def __str__(self):
        return self.name

    @property
    def slug(self):
        return slugify(self.name)

    def get_api_url(self):
        return reverse('ape_class', kwargs={'ape_class_id': self.pk})

    def get_absolute_url(self):
        return reverse('ape_class_wrapper', kwargs={'ape_class_id': self.pk})

    def day_of_week(self):
        if not self.start_date:
            return None
        start_date = timezone.localtime(self.start_date)
        day_index = start_date.weekday()
        return WEEKDAYS[day_index][1]

    def start_day_as_date(self):
        """
        Return the first day in the format: MM/DD/YY
        """
        if not self.start_date:
            return ''
        start_date = timezone.localtime(self.start_date)
        return '{}/{}/{}'.format(start_date.month, start_date.day, str(start_date.year)[2:])

    def start_day(self):
        """
        Provide a user-friendly representation of the class start day
        """
        day = ''
        if not self.start_date:
            return None
        start_date = timezone.localtime(self.start_date)
        if start_date == datetime.today().date():
            return '<b style="color:red">TONIGHT</b>'
        elif start_date == datetime.today().date() + timedelta(days=1):
            return 'Tomorrow'
        else:
            day = self.day_of_week()
            month_index = start_date.month - 1
            month = MONTHS[month_index][1]
            day += ', {month} {date}'.format(month=month,
                                             date=start_date.day)
            return day

    def start_time(self):
        pm = False
        hour = timezone.localtime(self.start_date).time().hour
        if hour >= 12:
            pm = True
            if hour > 12:
                hour -= 12
            return '{}pm'.format(hour)
        else:
            return '{}am'.format(hour)

    def end_time(self):
        pm = False
        hour = timezone.localtime(self.start_date).time().hour + self.class_length
        if hour >= 12:
            pm = True
            if hour > 12:
                hour -= 12
            return '{}pm'.format(hour)
        else:
            return '{}am'.format(hour)

    def to_data(self):
        data = {
            "id": self.id,
            "name": self.name,
            "bio": self.bio,
            "type": self.class_type,
            "price": self.price,
            "num_sessions": self.num_sessions
        }
        if self.start_date is not None:
            data["start_day"] = self.start_day()
            data["start_time"] = self.start_time()
            data["end_time"] = self.end_time()
            data["day_of_week"] = self.day_of_week()
            data["start_day_as_date"] = self.start_day_as_date()
        if self.banner:
            data['banner_url'] = self.banner.image.url
        if self.teacher:
            data['teacher'] = self.teacher.to_data()
        return data

    def save(self, *args, **kwargs):
        """
        We collect static when banners change because it seems easier than
        implementing webpack
        """
        collectstatic = False

        if self.pk is not None:
            orig = ApeClass.objects.get(pk=self.pk)
            if orig.banner != self.banner:
                print('banner changed')
                collectstatic = True
        else:
            collectstatic = True  # this is a newly created instance

        super(ApeClass, self).save(*args, **kwargs)
        if collectstatic:
            call_command('collectstatic', verbosity=1, interactive=False)
