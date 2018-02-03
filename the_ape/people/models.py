from django.db import models
from django.urls import reverse


class HouseTeam(models.Model):
    name = models.CharField(max_length=50)

    def performers(self):
        return Person.objects.filter(performs=True, house_team=self)

    def __str__(self):
        return self.name


class Person(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    bio = models.TextField(null=True, blank=True)
    headshot = models.ImageField(null=True, blank=True)
    teaches = models.BooleanField(default=False)
    performs = models.BooleanField(default=True)
    house_team = models.ForeignKey(HouseTeam, null=True, blank=True)

    class Meta(object):
        verbose_name = 'Person'
        verbose_name_plural = 'People'
        ordering = ['first_name',]

    def __str__(self):
        return '{} {}'.format(self.first_name, self.last_name)

    @property
    def name(self):
        return '{} {}'.format(self.first_name, self.last_name)

    def get_api_url(self):
        return reverse('person', kwargs={'person_id': self.pk})

    def get_absolute_url(self):
        return reverse('event_wrapper', kwargs={'event_id': self.pk})

    def to_data(self):
        data = {
            "id": self.id,
            "name": self.name,
            "bio": self.bio,
            "teaches": teaches,
            "performs": performs,
            "house_team": house_team
        }
        if self.headshot:
            data['image_url'] = self.headshot.image.url

        return data
