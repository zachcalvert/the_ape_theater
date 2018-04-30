import os
import re
from datetime import datetime, timedelta
from hashlib import md5

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.core.urlresolvers import reverse
from django.db import models
from django.template.defaultfilters import slugify
from django.urls import reverse
from django.utils import timezone

from model_utils.managers import InheritanceManager

from classes.models import ApeClass
from events.models import Event
from pages.fields import SortedManyToManyField, ColorField
from people.models import Person, HouseTeam


def to_cache_key(vals):
    string_vals = []
    for v in vals:
        if isinstance(v, datetime):
            v = v.isoformat()
        string_vals.append(str(v))

    cache_key = "_".join(":".join(string_vals).split())
    return cache_key


class WidgetManager(InheritanceManager):
    def active(self):
        return self.exclude(
            start_date__gt=timezone.now()
        ).exclude(
            end_date__lt=timezone.now()
        )


class AbstractWidget(models.Model):
    """
    So that the custom manager will be used by subclasses
    (custom managers are only inherited if they're created on abstract Models)
    """
    objects = WidgetManager()
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True


class Widget(AbstractWidget):
    """
    A component of a Page.

    Can take these forms:
        a large image (BannerWidget)
        a large carousel of images (ImageCarouselWidget)
        a grouping of objects (PeopleWidget, ApeClassesWidget, EventsWidget)
        an audio clip (AudioWidget)
        a video clip (VideoWidget)
        or just some text (TextWidget)

    Widgets can also be shared across Page instances, i.e. the Home page and the Classes page could
    display the same ImageCarouselWidget. Changing this widget would affect both pages in this case.
    """
    WIDTH_CHOICES = (
        ("full", "Full"),
        ("two_thirds", "Two Thirds"),
        ("half", "Half"),
        ("one_third", "One Third"),
    )
    start_date = models.DateTimeField(null=True, blank=True, help_text="Time at which this widget will turn on")
    end_date = models.DateTimeField(null=True, blank=True, help_text="Time at which this widget will turn off")
    width = models.CharField(max_length=100, choices=WIDTH_CHOICES, default="full")

    @staticmethod
    def autocomplete_search_fields():
        return ("id__iexact", "name__icontains")

    class Meta:
        ordering = ['name']

    def get_subclass(self):
        if type(self) != Widget:
            return self
        return Widget.objects.get_subclass(id=self.id)

    def __str__(self):
        return " ".join([self.name, type(self.get_subclass())._meta.verbose_name])

    def type_name(self, plural=False):
        if plural:
            return type(self)._meta.verbose_name_plural
        else:
            return type(self)._meta.verbose_name

    def type_name_plural(self):
        return self.type_name(plural=True)

    @property
    def is_active(self):
        if self.start_date and self.start_date > timezone.now():
            return False
        if self.end_date and self.end_date < timezone.now():
            return False
        return True

    @property
    def cache_key(self):
        if not hasattr(self, '_cache_key'):
            if self.id:
                self._cache_key = to_cache_key(["widget", self.id, self.last_modified])
            else:
                self._cache_key = None
        return self._cache_key

    @cache_key.setter
    def cache_key(self, new_key):
        self._cache_key = new_key

    def to_data(self):
        data = {
            "id": self.id,
            "name": self.name,
            "width": self.width
        }
        return data


class WidgetItem(models.Model):
    """
    Abstract base class for items that are contained inside widgets
    """
    sort_order = models.IntegerField()
    start_date = models.DateTimeField(null=True, blank=True, help_text="Time at which this item will turn on")
    end_date = models.DateTimeField(null=True, blank=True, help_text="Time at which this item will turn off")

    class Meta:
        abstract = True

    @property
    def is_active(self):
        if self.start_date and self.start_date > timezone.now():
            return False
        if self.end_date and self.end_date < timezone.now():
            return False
        return True


class PageToWidget(models.Model):
    widget = models.ForeignKey(Widget, related_name='page_to_widgets')
    page = models.ForeignKey('Page', related_name='page_to_widgets')
    sort_order = models.IntegerField(default=0)

    class Meta:
        ordering = ['page', 'sort_order']
        unique_together = (
            ['page', 'widget'],
        )

    def clean(self):
        if PageToWidget.objects.exclude(id=self.id).filter(page=self.page, sort_order=self.sort_order).exists():
            max_order = PageToWidget.objects.filter(page=self.page).aggregate(
                max_order=models.Max('sort_order'))['max_order']
            self.sort_order = max_order + 1

    def __str__(self):
        return u"{} on {}".format(self.widget, self.page)


class PageManager(models.Manager):

    def __init__(self, filter_defaults=None):
        super(PageManager, self).__init__()
        self.filter_defaults = filter_defaults

    def get_queryset(self):
        qs = super(PageManager, self).get_queryset()
        return qs


class Page(models.Model):
    """
    Data model for a web page, so that the content of the site can be managed through the admin.
    A Page essentially just fetches the Widgets it has relationships with in the DB and displays them, in order.
    There are some customizations built in (background_color, text_color, etc), so that any given Page
    can have a different look and feel.
    """

    SLUG_CHOICES = (
        ("home", "Home"),
        ("classes", "Classes"),
        ("shows", "Shows"),
        ("faculty", "Faculty"),
        ("talent", "Talent"),
        ("houseteams", "House Teams"),
        ("apetv", "Ape TV"),
        ("hype", "Hype"),
    )

    name = models.CharField(max_length=255)
    slug = models.SlugField(null=True, blank=True, choices=SLUG_CHOICES)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    draft = models.BooleanField(default=False)

    # page color
    background_gradient = models.NullBooleanField()
    background_start_color = ColorField(max_length=10, null=True, blank=True)
    background_end_color = ColorField(max_length=10, null=True, blank=True,
                                      help_text="Also used as fade color for background image "
                                                "if specified (default is dominant image color)")

    # text color
    text_color = ColorField(max_length=10, null=True, blank=True)

    # buy button
    button_color = ColorField(max_length=10, null=True, blank=True)
    button_text_color = ColorField(max_length=10, null=True, blank=True)

    # navbar button
    nav_bar_color = ColorField(max_length=10, null=True, blank=True,
                               help_text="This will also set the color of widget headers")
    nav_bar_text_color = ColorField(max_length=10, null=True, blank=True)

    widgets_base = SortedManyToManyField(
        Widget,
        through=PageToWidget,
        related_name='pages'
    )

    objects = PageManager(filter_defaults=False)
    all_objects = PageManager()

    class Meta:
        ordering = ['name']

    @property
    def link_slug(self):
        return slugify(self.name)

    @staticmethod
    def autocomplete_search_fields():
        """
        Admin search
        """
        return ("id__iexact", "name__icontains", "slug__icontains")

    def background_data(self):
        if self.background_gradient:
            return {
                "type": "gradient",
                "start_color": self.background_start_color,
                "end_color": self.background_end_color,
            }
        else:
            return {
                "type": "solid_color",
                "color": self.background_start_color
            }

    def cache_key(self):
        return to_cache_key(["page", self.id, self.last_modified])

    def to_data(self):
        data = {
            'name': self.name,
            'background': self.background_data()
        }
        direct_data_fields = [
            'text_color',
            'button_color',
            'button_text_color',
            'nav_bar_color',
            'nav_bar_text_color'
        ]
        for field in direct_data_fields:
            data[field] = getattr(self, field, None)
        widgets = [w for w in self.widgets if w.is_active]

        data['widgets'] = [widget.get_subclass().to_data() for widget in widgets]
        return data

    @property
    def widgets(self):
        widgets = list(self.widgets_base.select_subclasses().order_by('page_to_widgets__sort_order'))
        return widgets

    @widgets.setter
    def widgets(self, some_widgets):
        self.widgets_base = some_widgets

    def add_widget(self, widget, sort_order=None):
        if sort_order is None:
            sort_order = self.page_to_widgets.aggregate(
                sort_order=models.Max('sort_order'))['sort_order']

            if sort_order is None:
                sort_order = 0
            else:
                sort_order += 1
        return self.page_to_widgets.create(widget=widget, sort_order=sort_order)

    def get_url(self):
        if self.slug:
            return reverse('slug_page_wrapper', kwargs={"page_slug": self.slug})
        else:
            return reverse('page_id_wrapper', kwargs={'page_id': self.id})

    def get_api_url(self):
        return reverse("page", kwargs={"page_id": self.id})

    def __str__(self):
        return self.name


class PageLinkMixin(models.Model):
    """
    Mixin which provides the fields necessary to generically link to 
    other page-like content
    """
    link_id = models.PositiveIntegerField(null=True, blank=True)
    link_type = models.ForeignKey(ContentType, null=True, blank=True)
    link = GenericForeignKey("link_type", "link_id")

    @property
    def link_url(self):
        if self.link_type:
            if self.link_type.model_class() == Event:
                return reverse("event", kwargs={"event_id": self.link.id})
            elif self.link_type.model_class() == Page:
                return reverse("page_id_wrapper", kwargs={"page_id": self.link_id})
            else:
                return self.link.get_api_url()
        return ''

    class Meta:
        abstract = True


class PageLinkWidgetItem(WidgetItem, PageLinkMixin):
    """
    A Widget Item that links to a page
    """

    class Meta:
        abstract = True


class TextWidget(Widget):
    content = models.TextField()
    text_color = ColorField(blank=True)

    class Meta:
        verbose_name = "block of text"
        verbose_name_plural = "blocks of text"

    @property
    def json_content(self):
        return self.content.replace("\n", r"").replace("\r", r"")

    def to_data(self, *args, **kwargs):
        data = super(TextWidget, self).to_data(*args, **kwargs)
        data.update({
            "type": "text",
            "text": self.json_content,
            "text_color": self.text_color,
        })
        return data


class GroupWidget(Widget):
    """
    Base class for a group of items.
    """
    group_type = None

    class DefaultMeta:
        required_fields = ['display_type']

    class Meta:
        abstract = True

    def to_data(self, *args, **kwargs):
        data = super(GroupWidget, self).to_data(*args, **kwargs)
        data.update({
            "type": self.display_type,
            "item_type": self.item_type(),
            "items": [
                self.item_data(item) for item in self.items.all()
            ]
        })
        if self.group_type:
            data["group_type"] = self.group_type
        return data

    def item_type(self):
        raise NotImplementedError("Group widgets need to say their item_type")

    @property
    def items(self):
        raise NotImplementedError()

    def item_data(self, item):
        data = {
            "id": item.id,
            "name": item.name,
            "path": item.get_api_url(),
        }
        return data


class EventsWidget(GroupWidget):
    events = models.ManyToManyField(Event, blank=True, related_name='events_widgets')
    display_type = models.CharField(
        max_length=100,
        default='gallery',
        null=True,
        blank=True,
        choices=(
            ('gallery', 'Cover Gallery'),
            ('row_focus', 'Row'),
            ('list', 'List'),
        ),
    )
    # The following two fields allow us to have an EventsWidget that displays whatever
    # shows are happening in the next X days. When these fields are set, the contents of this
    # widget do not need to be managed.
    upcoming_events = models.BooleanField(default=False)
    upcoming_events_window = models.IntegerField(
        blank=True, null=True,
        help_text="Number of days in future for which events will display."
    )

    class Meta:
        verbose_name = "group of events"
        verbose_name_plural = "groups of events"

    def item_type(self):
        return "event"

    def to_data(self, *args, **kwargs):
        data = super(EventsWidget, self).to_data(*args, **kwargs)
        data.update({
            "upcoming_events": self.upcoming_events,
            "upcoming_events_window": self.upcoming_events_window
        })
        return data

    @property
    def items(self):
        events = Event.objects.all()

        if self.upcoming_events:
            events = events.filter(start_time__gt=timezone.now())

            if self.upcoming_events_window is not None:
                window_end = timezone.now() + timedelta(days=int(self.upcoming_events_window))
                events = events.filter(start_time__lt=window_end)
            events = events.order_by('start_time')

        if self.pk and self.events.exists():
            handpicked = Event.objects.filter(events_widgets=self)
            events = handpicked
        return events.distinct()

    def item_data(self, item):
        data = super(EventsWidget, self).item_data(item)
        data.update({
            "image": item.banner.image.url,
            "ticket_price": item.ticket_price,
            "is_free": item.is_free,
            "start_time": timezone.localtime(item.start_time),
            "bio": item.bio
        })
        return data


class PeopleWidget(GroupWidget):
    people = models.ManyToManyField(Person, blank=True, related_name='people_widgets')
    display_type = models.CharField(
        max_length=100,
        default='gallery',
        null=True,
        blank=True,
        choices=(
            ('gallery', 'Cover Gallery'),
            ('row_focus', 'Row'),
        ),
    )
    source_house_team = models.ForeignKey(HouseTeam, null=True, blank=True)

    class Meta:
        verbose_name = "group of people"
        verbose_name_plural = "groups of people"

    def item_type(self):
        return "person"

    @property
    def items(self):
        people = Person.objects.all()

        if self.source_house_team:
            people = Person.objects.filter(house_team=self.source_house_team)
            return people
        if self.pk and self.people.exists():
            people = Person.objects.filter(people_widgets=self)

        return people.distinct()

    def item_data(self, item):
        data = super(PeopleWidget, self).item_data(item)
        data.update({
            "image": item.headshot.url,
            "bio": item.bio
        })
        return data


class ApeClassesWidget(GroupWidget):
    ape_classes = models.ManyToManyField(ApeClass, blank=True, related_name='ape_classes_widgets')
    display_type = models.CharField(
        max_length=100,
        default='gallery',
        null=True,
        blank=True,
        choices=(
            ('gallery', 'Cover Gallery'),
            ('row_focus', 'Row'),
        ),
    )
    class_type = models.CharField(
        max_length=100,
        default='IMPROV',
        null=True,
        blank=True,
        choices=(
            ('IMPROV', 'Improv'),
            ('SKETCH', 'Sketch'),
            ('ACTING', 'Acting'),
            ('WORKSHOP', 'Workshop'),
        ),
    )

    class Meta:
        verbose_name = "group of ape classes"
        verbose_name_plural = "groups of ape classes"

    def item_type(self):
        return "ape_class"

    @property
    def items(self):
        ape_classes = ApeClass.objects.filter(registration_open=True)
        if self.class_type:
            ape_classes = ape_classes.filter(class_type=self.class_type)
        if self.pk and self.ape_classes.exists():
            handpicked = ApeClass.objects.filter(ape_classes_widgets=self)
            return handpicked
        return ape_classes.distinct()

    def item_data(self, item):
        data = super(ApeClassesWidget, self).item_data(item)
        data.update({
            "image": item.banner.image.url,
            "type": item.class_type,
            "bio": item.bio,
            "start_date": timezone.localtime(item.start_date),
            "class_length": item.class_length,
            "num_sessions": item.num_sessions,
            "price": item.price,
            "is_free": item.is_free
        })
        if item.teacher:
            data.update({
                "teacher": item.teacher.to_data()
            })
        return data


class PersonFocusWidget(Widget):
    """
    A more detailed display for a Person. Includes their bio.
    """
    person = models.ForeignKey(Person)

    def to_data(self, *args, **kwargs):
        data = super(PersonFocusWidget, self).to_data(*args, **kwargs)
        data.update({
            "type": "person_focus",
            "person": self.person.to_data(*args, **kwargs)
        })
        return data


class HouseTeamFocusWidget(Widget):
    """
    A detailed display for a House Team. Includes their performance time.
    """
    house_team = models.ForeignKey(HouseTeam)

    def to_data(self, *args, **kwargs):
        data = super(HouseTeamFocusWidget, self).to_data(*args, **kwargs)
        data.update({
            "type": "house_team_focus",
            "house_team": self.house_team.to_data(*args, **kwargs)
        })
        return data


class BannerWidget(Widget, PageLinkMixin):
    image = models.ImageField(upload_to='images/banner/')

    class Meta(Widget.Meta):
        verbose_name = "banner"
        verbose_name_plural = "banners"

    def to_data(self, *args, **kwargs):
        data = super(BannerWidget, self).to_data(*args, **kwargs)
        data.update({
            "type": "banner",
            "image":  {"url": self.image.url}
        })
        try:
            if self.link_url:
                data["page_path"] = self.link_url
        except AttributeError:
            pass
        return data

    def save(self, *args, **kwargs):
        """
        We collect static when images change because it seems easier than
        implementing webpack
        """
        collectstatic = False

        if self.pk is not None:
            orig = BannerWidget.objects.get(pk=self.pk)
            if orig.image != self.image:
                collectstatic = True
        else:
            collectstatic = True  # this is a newly created instance

        super(BannerWidget, self).save(*args, **kwargs)
        if collectstatic:
            call_command('collectstatic', verbosity=0, interactive=False)


class ImageCarouselWidget(Widget):
    """
    Container class for the images in the carousel slider.
    """
    class Meta:
        verbose_name = "carousel of big images"
        verbose_name_plural = "carousels of big images"

    def to_data(self, *args, **kwargs):
        data = super(ImageCarouselWidget, self).to_data(*args, **kwargs)
        data.update({
            "type": "image_carousel",
            "images": [
                image.to_data() for image in self.images.all()
            ]
        })
        return data


class ImageCarouselItem(PageLinkWidgetItem):
    carousel = models.ForeignKey(ImageCarouselWidget, related_name='images')
    image = models.ImageField()

    class Meta:
        verbose_name = "image"
        verbose_name_plural = "images"
        ordering = ["sort_order"]

    def image_as_data(self, image):
        return {"url": image.url}

    def to_data(self):
        return {
            "image": self.image_as_data(self.image),
            "path": self.link_url,
            "start_date": self.start_date,
            "end_date": self.end_date,
        }

    def save(self, *args, **kwargs):
        """
        We collect static when images change because it seems easier than
        implementing webpack
        """
        collectstatic = False

        if self.pk is not None:
            orig = ImageCarouselItem.objects.get(pk=self.pk)
            if orig.image != self.image:
                collectstatic = True
        else:
            collectstatic = True  # this is a newly created instance

        super(ImageCarouselItem, self).save(*args, **kwargs)
        if collectstatic:
            call_command('collectstatic', verbosity=0, interactive=False)


class AudioWidget(Widget):
    audio_file = models.FileField(upload_to='audio', help_text="Allowed type - .mp3, .ogg")
    description = models.TextField(null=True, blank=True)

    def to_data(self, *args, **kwargs):
        data = super(AudioWidget, self).to_data(*args, **kwargs)
        data.update({
            "type": "audio",
            "description": self.description,
            "audio_source": self.audio_file.url,
        })
        return data

    def save(self, *args, **kwargs):
        """
        We collect static when audio changes because it seems easier than
        implementing webpack
        """
        collectstatic = False

        if self.pk is not None:
            orig = AudioWidget.objects.get(pk=self.pk)
            if orig.audio_file != self.audio_file:
                print('audio changed')
                collectstatic = True
        else:
            collectstatic = True  # this is a newly created instance

        super(AudioWidget, self).save(*args, **kwargs)
        if collectstatic:
            call_command('collectstatic', verbosity=1, interactive=False)


class Video(models.Model):
    """
    Class representing an uploaded Video file. Can be referenced across multiple VideosWidgets
    without needing to be uploaded multiple times.
    """
    name = models.CharField(max_length=100)
    video_file = models.FileField(upload_to='videos', help_text="Allowed type - .mp4, .ogg")
    description = models.TextField(null=True, blank=True)

    def get_api_url(self):
        return ''

    def __str__(self):
        return self.name

    def to_data(self, *args, **kwargs):
        data = {
            "name": self.name,
            "description": self.description,
            "source": self.video_file.url,
        }
        return data

    def save(self, *args, **kwargs):
        """
        Collect static when video changes because it is easier than implementing webpack.
        """
        collectstatic = False

        if self.pk is not None:
            orig = Video.objects.get(pk=self.pk)
            if orig.video_file != self.video_file:
                print('video changed')
                collectstatic = True
        else:
            # this is a newly created instance
            collectstatic = True

        super(Video, self).save(*args, **kwargs)
        if collectstatic:
            call_command('collectstatic', verbosity=0, interactive=False)


class VideoFocusWidget(Widget):
    video = models.ForeignKey(Video)

    def to_data(self, *args, **kwargs):
        data = super(VideoFocusWidget, self).to_data(*args, **kwargs)
        data.update({
            "type": "video_focus",
            "video": self.video.to_data(*args, **kwargs)
        })
        return data


class VideosWidget(GroupWidget):
    videos = models.ManyToManyField(Video, blank=True, related_name='video_widgets')
    display_type = models.CharField(
        max_length=100,
        default='gallery',
        null=True,
        blank=True,
        choices=(
            ('gallery', 'Cover Gallery'),
            ('row_focus', 'Row'),
        ),
    )

    class Meta:
        verbose_name = "group of videos"
        verbose_name_plural = "groups of videos"

    def item_type(self):
        return "video"

    @property
    def items(self):
        videos = Video.objects.all()
        if self.pk and self.videos.exists():
            videos = Video.objects.filter(video_widgets=self)
        return videos.distinct()

    def item_data(self, item):
        data = super(VideosWidget, self).item_data(item)
        data.update({
            "source": item.video_file.url,
            "description": item.description
        })
        return data
