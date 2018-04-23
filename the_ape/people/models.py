from django.core.management import call_command
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse


class HouseTeam(models.Model):
    name = models.CharField(max_length=50)
    logo = models.ForeignKey('pages.BannerWidget', null=True, blank=True)
    image_carousel = models.ForeignKey('pages.ImageCarouselWidget', null=True, blank=True)
    videos = models.ManyToManyField('pages.VideoWidget', blank=True)
    show_time = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.name

    @property
    def slug(self):
        return slugify(self.name)

    def get_api_url(self):
        return reverse('house_team', kwargs={'house_team_id': self.pk})

    def get_absolute_url(self):
        return reverse('house_team', kwargs={'house_team_id': self.pk})

    def to_data(self, members=True):
        data = {
            "id": self.id,
            "name": self.name,
            "path": self.get_api_url(),
            "show_time": self.show_time,
            "performers": [
                performer.to_data() for performer in self.performers.all()
            ]
        }
        if self.image_carousel:
            data['image_carousel'] = self.image_carousel.to_data()
        if self.logo:
            data['logo'] = self.logo.to_data()
        if self.videos.exists():
            data['videos'] = [
                {
                    "video_source": video.video_file.url,
                    "name": video.name,
                    "description": video.description
                } for video in self.videos.all()
            ]
        return data


class PeopleManager(models.Manager):

    def __init__(self, inactives=False):
        super(PeopleManager, self).__init__()
        self.inactives = inactives

    def get_queryset(self):
        qs = super(PeopleManager, self).get_queryset()
        if self.inactives:
            return qs
        return qs.filter(active=True)


class Person(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    bio = models.TextField(null=True, blank=True)
    headshot = models.ImageField(null=True, blank=True)
    teaches = models.BooleanField(default=False)
    performs = models.BooleanField(default=True)
    house_team = models.ForeignKey(HouseTeam, null=True, blank=True, related_name='performers')
    videos = models.ManyToManyField('pages.VideoWidget', blank=True)
    active = models.BooleanField(default=True)

    objects = PeopleManager()
    all_objects = PeopleManager(inactives=True)

    class Meta(object):
        verbose_name = 'Person'
        verbose_name_plural = 'People'
        ordering = ['first_name']

    def __str__(self):
        return '{} {}'.format(self.first_name, self.last_name)

    @property
    def slug(self):
        return slugify(self.name)

    @property
    def name(self):
        return '{} {}'.format(self.first_name, self.last_name)

    def get_api_url(self):
        return reverse('person', kwargs={'person_id': self.pk})

    def get_absolute_url(self):
        return reverse('person_wrapper', kwargs={'person_id': self.pk})

    def to_data(self):
        data = {
            "id": self.id,
            "name": self.name,
            "bio": self.bio,
            "teaches": self.teaches,
            "performs": self.performs,
            "path": self.get_api_url(),
            "url": self.get_absolute_url()
        }
        if self.house_team:
            data["house_team"] = self.house_team.to_data(members=False)
        if self.headshot:
            data['image_url'] = self.headshot.url
        if self.videos.exists():
            data['videos'] = [
                {
                    "video_source": video.video_file.url,
                    "name": video.name,
                    "description": video.description
                } for video in self.videos.all()
            ]

        return data

    def save(self, *args, **kwargs):
        """
        We collect static when images change because it seems easier than
        implementing webpack
        """
        collectstatic = False

        if self.pk is not None:
            orig = Person.objects.get(pk=self.pk)
            if orig.headshot != self.headshot:
                print('headshot changed')
                collectstatic = True
        else:
            collectstatic = True  # this is a newly created instance

        super(Person, self).save(*args, **kwargs)
        if collectstatic:
            call_command('collectstatic', verbosity=1, interactive=False)
