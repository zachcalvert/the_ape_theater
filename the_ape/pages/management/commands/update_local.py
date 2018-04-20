"""
DO NOT RUN IN PRODUCTION

Updates a local db with data on the current production site.
"""
from __future__ import unicode_literals

import json
import requests
from dateutil import parser
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify

from classes.models import ApeClass
from events.models import Event
from pages.models import Page, PersonFocusWidget, TextWidget, ImageCarouselItem, ImageCarouselWidget, \
    ApeClassesWidget, BannerWidget, EventsWidget, PeopleWidget
from people.models import Person


PAGES_TO_CREATE = [
    'home',
    'classes',
    'shows',
    'talent',
    'faculty',
    'houseteams',
    'hype',
]

BASE_URL = 'https://theapetheater.org'

class Command(BaseCommand):

    def create_person_from_json(self, person_json):
        first, last = person_json['name'].split(' ')
        person, created = Person.objects.get_or_create(first_name=first, last_name=last)
        if created:
            print('Created new person: {}'.format(person))

        if not person.headshot.name or person.headshot.name == '':
            try:
                image_url = '{}{}'.format(BASE_URL, person_json['image'])
            except KeyError:
                image_url = '{}{}'.format(BASE_URL, person_json['image_url'])
            image = requests.get(image_url)
            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(image.content)
            img_temp.flush()

            person.headshot = None
            person.headshot.save('{}.jpg'.format(slugify(person_json['name'])), File(img_temp), save=True)
        person.bio = person_json['bio']
        person.save()
        return person

    def create_person_focus_widget_from_json(self, focus_json):
        first, last = focus_json['person']['name'].split(' ')
        person = Person.objects.filter(first_name=first, last_name=last).first()
        if not person:
            person = self.create_person_from_json(focus_json['person'])
        widget, created = PersonFocusWidget.objects.get_or_create(name='{}'.format(person.last_name), person=person)
        return widget

    def create_class_from_json(self, class_json):
        ape_class, created = ApeClass.objects.get_or_create(name=class_json['name'], price=class_json['price'])
        if created:
            print('created new ape class: {}'.format(ape_class.name))
        ape_class.class_type = class_json['type']
        ape_class.num_sessions = class_json['num_sessions']
        ape_class.bio = class_json['bio']
        ape_class.price = class_json['price']
        ape_class.class_length = class_json['class_length']
        ape_class.start_date = parser.parse(class_json['start_date'])

        if ape_class.banner is None:
            image_url = '{}{}'.format(BASE_URL, class_json['image'])
            banner = self.create_banner_widget_from_url(url=image_url, name=ape_class.name)
            ape_class.banner = banner
            ape_class.save()

        return ape_class

    def create_show_from_json(self, show_json):
        show, created = Event.objects.get_or_create(name=show_json['name'], 
                                                    start_time=parser.parse(show_json['start_time']),
                                                    ticket_price=show_json['ticket_price'])
        show.bio = show_json['bio']
        if show.banner is None:
            image_url = '{}{}'.format(BASE_URL, show_json['image'])
            show.banner = self.create_banner_widget_from_url(image_url, show.name)
        show.save()

        return show

    def create_text_widget_from_json(self, widget_json):
        text_widget, created = TextWidget.objects.get_or_create(name=widget_json['name'])
        text_widget.content = widget_json['text']
        text_widget.text_color = widget_json['text_color']
        text_widget.width = widget_json['width']
        text_widget.save()

        return text_widget

    def create_carousel_widget_from_json(self, widget_json):
        carousel_widget, created = ImageCarouselWidget.objects.get_or_create(name=widget_json['name'])
        carousel_widget.width = widget_json['width']
        for count, image in enumerate(widget_json['images']):
            item, created = ImageCarouselItem.objects.get_or_create(carousel=carousel_widget, sort_order=count)
            item.path = image['path']

            image_url = '{}{}'.format(BASE_URL, image['image']['url'])
            image = requests.get(image_url)
            img_temp = NamedTemporaryFile(delete=True)
            img_temp.write(image.content)
            img_temp.flush()

            item.image = None
            item.image.save('{}.jpg'.format(item.id), File(img_temp), save=True)
            print('added ImageCarouselItem {} to the {} Image Carousel'.format(item.id, carousel_widget.name))

        return carousel_widget

    def create_banner_widget_from_url(self, url, name):
        image = requests.get(url)
        img_temp = NamedTemporaryFile(delete=True)
        img_temp.write(image.content)
        img_temp.flush()

        banner_widget = BannerWidget.objects.create(name=name)
        banner_widget.image.save('{}.jpg'.format(name), File(img_temp), save=True)
        print('added new banner: {}'.format(banner_widget.name))

        return banner_widget

    def create_widget_from_json(self, widget_json):
        widget_type = widget_json['type']

        if widget_type == 'audio' or widget_type == 'video':
            return None

        elif widget_type == 'text':
            widget = self.create_text_widget_from_json(widget_json)

        elif widget_type == 'image_carousel':
            widget = self.create_carousel_widget_from_json(widget_json)

        elif widget_type == 'person_focus':
            widget = self.create_person_focus_widget_from_json(widget_json)

        elif widget_json['item_type'] is not None:
            if widget_json['item_type'] == 'ape_class':
                widget, created = ApeClassesWidget.objects.get_or_create(name=widget_json['name'])
                widget.display_type = widget_type
                widget.width = widget_json['width']
                widget.type = widget_json['type']
                for item in widget_json['items']:
                    ape_class = self.create_class_from_json(item)
                    widget.ape_classes.add(ape_class)

            elif widget_json['item_type'] == 'event':
                widget, created = EventsWidget.objects.get_or_create(name=widget_json['name'])
                widget.display_type = widget_type
                widget.width = widget_json['width']
                widget.type = widget_json['type']
                widget.save()
                for item in widget_json['items']:
                    show = self.create_show_from_json(item)

            elif widget_json['item_type'] == 'person':
                widget, created = PeopleWidget.objects.get_or_create(name=widget_json['name'])
                widget.display_type = widget_type
                widget.width = widget_json['width']
                widget.type = widget_json['type']
                widget.save()
                for item in widget_json['items']:
                    person = self.create_person_from_json(item)
                    widget.people.add(person)
        else:
            widget = None

        return widget

    def update_slugged_page(self, slug):
        page, created = Page.objects.get_or_create(slug=slug)
        page.page_to_widgets.all().delete()

        page_url = '{}/api/{}.json'.format(BASE_URL, slug)
        response = requests.get(page_url)
        response_json = json.loads(response.content.decode())

        for widget_json in response_json['widgets']:
            widget = self.create_widget_from_json(widget_json)
            if widget:
                page.add_widget(widget)
                print('added {} to the {} page'.format(widget, slug))

    def handle(self, *args, **options):

        # disallow running in production
        if settings.DEBUG:
            for slug in PAGES_TO_CREATE:
                print('UPDATING: {} page'.format(slug))
                self.update_slugged_page(slug)
                print('Finished updating {} page\n'.format(slug))
