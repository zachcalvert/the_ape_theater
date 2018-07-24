from django.core.management import call_command
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import timezone


class Event(models.Model):
    """
    Model representing any one-time event for which the theater can sell tickets.

    Anonymous Users are allowed to purchase tickets for an event. In this case,
    we create an account for them with the provided name and email address.
    """
    name = models.CharField(max_length=100)
    bio = models.TextField()
    start_time = models.DateTimeField(null=True)
    max_tickets = models.IntegerField(default=20, null=True)
    tickets_sold = models.IntegerField(default=0)
    ticket_price = models.DecimalField(decimal_places=2, max_digits=5)
    banner = models.ForeignKey('pages.BannerWidget', null=True)

    class Meta:
        ordering = ['-start_time']

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
        If an event is free, we display different messaging around ticket purchases.
        """
        if self.ticket_price == 0:
            return True
        return False

    def get_api_url(self):
        return reverse('event', kwargs={'event_id': self.pk})

    def get_absolute_url(self):
        return reverse('event_wrapper', kwargs={'event_id': self.pk})

    def to_data(self):
        data = {
            "id": self.id,
            "name": self.name,
            "bio": self.bio,
            "ticket_price": self.ticket_price,
            "tickets_left": self.max_tickets - self.tickets_sold,
            "is_free": self.is_free,
            "start_time": timezone.localtime(self.start_time)
        }
        if self.banner:
            data['banner_url'] = self.banner.image.url

        return data

    def save(self, *args, **kwargs):
        """
        We collect static when banners change because it is easier than implementing webpack.
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
