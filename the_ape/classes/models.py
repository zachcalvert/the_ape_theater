from datetime import datetime, timedelta

from django.core.management import call_command
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse


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
    enrollment_opens = models.DateField(null=True, blank=True)
    enrollment_closes = models.DateField(null=True, blank=True)
    price = models.DecimalField(decimal_places=2, max_digits=5)

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

    def start_day(self):
        """
        Provide a user-friendly representation of the event start day
        """
        day = ''
        if not self.start_date:
            return None
        if self.start_date == datetime.today().date():
            return '<b style="color:red">TONIGHT</b>'
        elif self.start_date == datetime.today().date() + timedelta(days=1):
            return 'Tomorrow'
        else:
            day_index = self.start_date.weekday()
            day = WEEKDAYS[day_index][1]
            month_index = self.start_date.month - 1
            month = MONTHS[month_index][1]
            day += ', {month} {date}'.format(month=month,
                                             date=self.start_date.day)
            return day

    def to_data(self):
        data = {
            "id": self.id,
            "name": self.name,
            "bio": self.bio,
            "type": self.class_type,
            "price": self.price,
        }
        if self.start_day() is not None:
            data["start_day"] = self.start_day()
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
