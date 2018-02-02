from django.db import models
from django.urls import reverse


class Event(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField()
    start_time = models.DateTimeField(null=True)
    max_tickets = models.IntegerField(null=True)
    tickets_sold = models.IntegerField(default=0)
    ticket_price = models.DecimalField(decimal_places=2, max_digits=5)
    banner = models.ForeignKey('pages.BannerWidget', null=True, blank=True)

    def __str__(self):
        return self.name

    def get_api_url(self):
        return reverse('event', kwargs={'event_id': self.pk})

    def get_absolute_url(self):
        return reverse('event_wrapper', kwargs={'event_id': self.pk})