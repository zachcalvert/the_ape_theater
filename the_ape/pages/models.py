import re
from datetime import datetime, timedelta

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.urls import reverse

from model_utils.managers import InheritanceManager

from classes.models import ApeClass, Student
from events.models import Event
from people.models import Person, HouseTeam


class WidgetManager(InheritanceManager):
    def active(self):
        return self.exclude(
            start_date__gt=datetime.now()
        ).exclude(
            end_date__lt=datetime.now()
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
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

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


class WidgetItemManager(models.Manager):
    use_for_related_fields = True

    def active(self):
        return self.exclude(
            start_date__gt=datetime.now()
        ).exclude(
            end_date__lt=datetime.now()
        )


class WidgetItem(models.Model):
    """
    Abstract base class for items that are contained inside widgets
    """
    sort_order = models.IntegerField()
    start_date = models.DateTimeField(null=True, blank=True)
    end_date = models.DateTimeField(null=True, blank=True)

    objects = WidgetItemManager()

    class Meta:
        abstract = True


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

    SLUG_CHOICES = (
        ("home", "Home"),
        ("classes", "Classes"),
        ("events", "Events"),
        ("people", "People"),
        ("about", "About"),
    )

    name = models.CharField(max_length=255)
    slug = models.SlugField(null=True, blank=True, choices=SLUG_CHOICES)
    created = models.DateTimeField(auto_now_add=True)
    last_modified = models.DateTimeField(auto_now=True)
    draft = models.BooleanField(default=False)

    widgets_base = models.ManyToManyField(
        Widget,
        through=PageToWidget,
        related_name='pages'
    )

    objects = PageManager(filter_defaults=False)
    all_objects = PageManager()

    class Meta:
        ordering = ['name']

    @staticmethod
    def autocomplete_search_fields():
        return ("id__iexact", "name__icontains", "slug__icontains")

    @property
    def widgets(self):
        return self.widgets_base.active().order_by('page_to_widgets__sort_order')

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
        if self.link_type.model_class() == Event:
            return reverse("event", kwargs={"event_id": self.link.id})
        else:
            return self.link.get_api_url()

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
    template_name = "widgets/text.json"

    class Meta:
        verbose_name = "block of text"
        verbose_name_plural = "blocks of text"

    @property
    def json_content(self):
        return self.content.replace("\n", r"\n").replace("\r", r"\r")


class AbstractGroupWidget(Widget):
    template_name = "widgets/group.json"

    class Meta:
        abstract = True

    def item_type(self):
        raise NotImplementedError("Group widgets need to say their item_type")

    def item_template_name(self):
        return "widgets/items/{}.json".format(self.item_type())

    def see_all_url(self):
        return None


class GroupWidget(AbstractGroupWidget):
    """
    A group of classes, events, or people
    """
    class DefaultMeta:
        required_fields = ['display_type',]

    class Meta:
        abstract = True

    @property
    def items(self):
        raise NotImplementedError()


class EventFocusWidget(Widget):
    template_name = "widgets/event_focus.json"
    event = models.ForeignKey(Event, null=True, blank=True)


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
        ),
    )

    class Meta:
        verbose_name = "group of events"
        verbose_name_plural = "groups of events"


    def item_type(self):
        return "event"

    @property
    def items(self):
        if self.pk and self.events.exists():
            handpicked = Event.objects.filter(events_widgets=self)
            return handpicked
        return Event.objects.all()


class PersonFocusWidget(Widget):
    template_name = "widgets/person_focus.json"
    person = models.ForeignKey(Person, null=True, blank=True)


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

    class Meta:
        verbose_name = "group of people"
        verbose_name_plural = "groups of people"


    def item_type(self):
        return "person"

    @property
    def items(self):
        if self.pk and self.people.exists():
            handpicked = Person.objects.filter(people_widgets=self)
            return handpicked
        return Person.objects.all()


class BannerWidget(Widget, PageLinkMixin):
    image = models.ImageField()
    template_name = "widgets/banner.json"

    class Meta(Widget.Meta):
        verbose_name = "banner"
        verbose_name_plural = "banners"


class ImageCarouselWidget(Widget):
    template_name = "widgets/image_carousel.json"

    class Meta:
        verbose_name = "carousel of big images"
        verbose_name_plural = "carousels of big images"


class ImageCarouselItem(PageLinkWidgetItem):
    carousel = models.ForeignKey(ImageCarouselWidget, related_name='images')
    image = models.ImageField()

    class Meta:
        verbose_name = "image"
        verbose_name_plural = "images"

    def clean(self):
        if not self.link:
            raise ValidationError({'link': ["This field is required."]})
