"""
DO NOT RUN IN PRODUCTION

Updates a local db with data on the current production site.
"""
from __future__ import unicode_literals

import json
import requests
from tempfile import NamedTemporaryFile

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand, CommandError
from django.template.defaultfilters import slugify

from pages.models import Page, PersonFocusWidget, TextWidget
from people.models import Person


PAGE_SLUGS = [
    'home',
    'talent',
    'faculty',
    'shows',
    'classes',
]

BASE_URL = 'https://theapetheater.org'

class Command(BaseCommand):

    def update_hype_page(self):
        page, created = Page.objects.get_or_create(slug='hype')
        page.page_to_widgets.all().delete()

        hype_url = '{}/api/hype.json'.format(BASE_URL)
        response = requests.get(hype_url)
        response_json = json.loads(response.content.decode())

        for text_widget in response_json['widgets']:
            widget, created = TextWidget.objects.get_or_create(name=text_widget['name'])
            widget.content = text_widget['text']
            widget.text_color = text_widget['text_color']
            widget.width = text_widget['width']
            widget.save()
            page.add_widget(widget)
            print('added {} text widget to Hype page'.format(widget.name))

    def update_house_team_page(self):
        pass

    def update_classes_page(self):
        pass

    def update_shows_page(self):
        pass    

    def update_home_page(self):
        pass

    def update_people(self):
        talent_url = '{}/api/talent.json'.format(BASE_URL)
        response = requests.get(talent_url)
        response_json = json.loads(response.content.decode())

        print('Updating from the {} performers found on the live site.'.format(len(response_json['widgets'][0]['items'])))

        for person_json in response_json['widgets'][0]['items']:
            first, last = person_json['name'].split(' ')
            person, created = Person.objects.get_or_create(first_name=first, last_name=last)
            if created:
                print('Created new person: {}'.format(person))
                person_url = '{}{}'.format(BASE_URL, person_json['path'])
                response = requests.get(talent_url)
                response_json = json.loads(response.content.decode())

            if not person.headshot.name or person.headshot.name == '':
                image_url = '{}{}'.format(BASE_URL, person_json['image'])
                image = requests.get(image_url)
                img_temp = NamedTemporaryFile(delete=True)
                img_temp.write(image.content)
                img_temp.flush()

                person.headshot = None
                person.headshot.save('{}.jpg'.format(slugify(person_json['name'])), File(img_temp), save=True)

        print('Finished updating talent.')

        faculty_url = '{}/api/faculty.json'.format(BASE_URL)
        response = requests.get(faculty_url)
        response_json = json.loads(response.content.decode())

        print('Updating from the {} teachers found on the live site.'.format(len(response_json['widgets'])))

        for person_json in response_json['widgets']:
            first, last = person_json['person']['name'].split(' ')
            person, created = Person.objects.get_or_create(first_name=first, last_name=last)
            if not person.teaches:
                person.teaches = True
                person.save()
            if created:
                print('Created new teacher: {}'.format(person))

            person.bio = person_json['person']['bio']

            if not person.headshot.name or person.headshot.name == '':
                image_url = '{}{}'.format(BASE_URL, person_json['person']['image_url'])
                image = requests.get(image_url)
                img_temp = NamedTemporaryFile(delete=True)
                img_temp.write(image.content)
                img_temp.flush()

                person.headshot = None
                person.headshot.save('{}.jpg'.format(slugify(person_json['person']['name'])), File(img_temp), save=True)
            else:
                person.save()

        print('Finished updating faculty.')

    def update_talent_page(self):
        page, created = Page.objects.get_or_create(slug='talent')

        try:
            talent_widget = page.widgets_base.first().peoplewidget
            performers = Person.objects.filter(house_team__isnull=False)
            talent_widget.people.set(performers)
        except Exception:
            print('unable to update the talent page: {}'.format(e))
            pass

    def update_faculty_page(self):
        page, created = Page.objects.get_or_create(slug='faculty')
        page.page_to_widgets.all().delete()

        for teacher in Person.objects.filter(teaches=True):
            widget, created = PersonFocusWidget.objects.get_or_create(name='{}'.format(teacher.last_name), person=teacher)
            page.add_widget(widget)
            print('added teacher widget to Faculty page for {} {}'.format(teacher.first_name, teacher.last_name))

    def handle(self, *args, **options):

        # disallow running in production
        if settings.DEBUG:
            self.update_people()
            self.update_talent_page()
            self.update_faculty_page()
            self.update_hype_page()


