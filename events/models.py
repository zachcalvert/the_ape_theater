from django.db import models


class Event(models.Model):
    name = models.CharField(max_length=100)
    bio = models.TextField(max_length=100)
    start_time = models.DateTimeField(null=True)
    max_tickets = models.IntegerField(null=True)
    tickets_sold = models.IntegerField(default=0)
    ticket_price = models.DecimalField(decimal_places=2, max_digits=2)
