from django.core.management import call_command
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import timezone


class ApeClass(models.Model):
    """
    A model for any class/workshop someone can take at The Ape. 

    Anonymous Users are not allowed to register for a class, people must create an account to register for a class.
    """
    TYPE_CHOICES = (
        ('IMPROV', 'Improv'),
        ('SKETCH', 'Sketch'),
        ('ACTING', 'Acting'),
        ('WORKSHOP', 'Workshop'),
    )

    name = models.CharField(max_length=50)
    bio = models.TextField()
    class_type = models.CharField(choices=TYPE_CHOICES, max_length=50)
    banner = models.ForeignKey('pages.BannerWidget', null=True)

    teacher = models.ForeignKey('people.Person', null=True, blank=True)
    start_date = models.DateTimeField(null=True, blank=True)
    num_sessions = models.IntegerField(help_text='Number of Sessions', default=4)
    max_enrollment = models.IntegerField(help_text='Max number of students', default=12)
    class_length = models.IntegerField(default=2, help_text='Length of one class session, in hours.')
    price = models.DecimalField(decimal_places=2, max_digits=5)
    registration_open = models.BooleanField(default=True)
    students_registered = models.IntegerField(default=0)
    deposit_price = models.DecimalField(decimal_places=2, max_digits=5, null=True, blank=True)

    class Meta(object):
        verbose_name = 'Ape Class'
        verbose_name_plural = 'Ape Classes'

    def __str__(self):
        return self.name

    @property
    def slug(self):
        """
        Provide a slug property to make event detail urls SEO-friendly
        """
        return slugify(self.name)

    @property
    def is_free(self):
        """
        If class is free, we display different messaging around registering for it.
        """
        return self.price == 0

    def get_api_url(self):
        return reverse('ape_class', kwargs={'ape_class_id': self.pk})

    def get_absolute_url(self):
        return reverse('ape_class_wrapper', kwargs={'ape_class_id': self.pk})

    def to_data(self):
        data = {
            "id": self.id,
            "name": self.name,
            "bio": self.bio,
            "type": self.class_type,
            "price": self.price,
            "num_sessions": self.num_sessions,
            "students_registered": self.students_registered,
            "is_free": self.is_free
        }
        if self.start_date is not None:
            data["start_date"] = timezone.localtime(self.start_date)
            data["class_length"] = self.class_length
        if self.banner:
            data['banner_url'] = self.banner.image.url
        if self.teacher:
            data['teacher'] = self.teacher.to_data()
        if self.deposit_price:
            data['deposit_price'] = self.deposit_price
        return data

    def save(self, *args, **kwargs):
        """
        We collect static when banners change because it is easier than implementing webpack.
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
