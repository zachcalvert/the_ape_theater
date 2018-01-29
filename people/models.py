from django.db import models


class HouseTeam(models.Model):
    name = models.CharField(max_length=50)

    def performers(self):
        return Person.objects.filter(performs=True, house_team=self)


class Person(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    bio = models.TextField(null=True, blank=True)
    image_url = models.URLField(max_length=2000, null=True, blank=True)
    teaches = models.BooleanField(default=False)
    house_team = models.ForeignKey(HouseTeam, null=True, blank=True)
    performs = models.BooleanField(default=True)

    class Meta(object):
        verbose_name = 'Person'
        verbose_name_plural = 'People'

    def __str__(self):
        return '{} {}'.format(self.first_name, self.last_name)