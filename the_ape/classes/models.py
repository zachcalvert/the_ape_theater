from django.core.management import call_command
from django.db import models
from django.urls import reverse


class ApeClass(models.Model):
    TYPE_CHOICES = (
        ('IMPROV', 'Improv'),
        ('SKETCH', 'Sketch'),
        ('ACTING', 'Acting'),
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

    def get_api_url(self):
        return reverse('ape_class', kwargs={'ape_class_id': self.pk})

    def get_absolute_url(self):
        return reverse('ape_class_wrapper', kwargs={'ape_class_id': self.pk})

    def start_day(self):
        if self.start_date:
            return '{}/{}/{}'.format(self.start_date.month,
                                     self.start_date.day,
                                     self.start_date.year)
        return None

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
