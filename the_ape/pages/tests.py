from __future__ import unicode_literals

import json
from bs4 import BeautifulSoup
from datetime import timedelta, datetime
from io import BytesIO
from PIL import Image

from django.core.cache import cache
from django.core.files.base import ContentFile
from django.core.urlresolvers import reverse
from django.test import TestCase, override_settings

from classes.models import ApeClass
from events.models import Event
from pages.models import Page, BannerWidget, TextWidget, ImageCarouselWidget, \
    PersonFocusWidget, EventsWidget
from pages.templatetags.page_tags import wrapped_url
from people.models import HouseTeam, Person, HouseTeamMembership


def make_image_file(name="test.png", size=(200, 1), color="red"):
    image_file = BytesIO()
    image = Image.new(mode='RGBA', size=size, color=color)
    image.save(image_file, format='png')
    content_file = ContentFile(image_file.getvalue())
    if name is not None:
        content_file.name = name
    return content_file


class TestWidgetAPI(TestCase):
    def __init__(self, methodName='runTest'):
        super(TestWidgetAPI, self).__init__(methodName)
        self.initial_time = datetime.now()

    def setUp(self):
        self.banner = BannerWidget.objects.create(
            name="banner test",
            image=make_image_file(size=(2048, 1), color="#ffffff")
        )
        self.house_team = HouseTeam.objects.create(name="The Goof Troop")
        self.person1= Person.objects.create(first_name="Funnyboy", last_name="Jones")
        self.person2 = Person.objects.create(first_name="Lisa", last_name="Crackemups")

        HouseTeamMembership.objects.create(person=self.person1, house_team=self.house_team)
        HouseTeamMembership.objects.create(person=self.person2, house_team=self.house_team)

        self.event1 = Event.objects.create(name="Friday Night Laffs", bio="Every Friday!", ticket_price=10, banner=self.banner)
        self.event2 = Event.objects.create(name="Saturday Night Shakes", bio="Every Saturday!", ticket_price=2, banner=self.banner)

    def get_page_json(self, page):
        """
        Get json value of the given page
        """
        response = self.client.get(page.get_api_url())
        self.assertEqual(response.status_code, 200)
        return json.loads(response.content)

    def get_widget_json(self, widget, empty=False):
        """
        Create a dummy page, and use the test client to get the json rendered by the API for the given widget
        """
        # make sure the widget is valid
        widget.full_clean()
        widget.save()

        page = Page.objects.create(slug="test{}".format(Page.objects.count()))
        page.add_widget(widget)

        page_json = self.get_page_json(page)
        if empty:
            self.assertEqual(0, len(page_json['widgets']))
            return []
        else:
            self.assertEqual(1, len(page_json['widgets']))
            return page_json['widgets'][0]

    def test_text_widget(self):
        """
        Verify that the text widget correctly reports type, text, & text_color
        """
        widget = TextWidget.objects.create(name="test", content="Some text", text_color="#FF0000")
        widget_json = self.get_widget_json(widget)

        self.assertDictContainsSubset({
            "type": "text",
            "text": "Some text",
            "text_color": "#FF0000"
        }, widget_json)

    def test_text_widget_json_content(self):
        """
        Verify that the text widget's json_content property correctly strips bad characters.
        """
        widget = TextWidget.objects.create(name="test", content="Some text.<br />\n\n\rSome more text on a new line.",
                                           text_color="#FF0000")
        widget_json = self.get_widget_json(widget)

        self.assertDictContainsSubset({
            "type": "text",
            "text": "Some text.<br />Some more text on a new line.",
            "text_color": "#FF0000"
        }, widget_json)

    def test_banner_widget(self):
        """
        Verify that the banner widget correctly reports type, image page_path, portrait_alignment & aspect ratio
        """
        widget = BannerWidget.objects.create(
            name="banner test",
            image=make_image_file(size=(2048, 1), color="#ffffff")
        )
        widget.full_clean()
        widget.save()
        widget_json = self.get_widget_json(widget)
        self.assertEqual(widget_json['type'], "banner")
        self.assertFalse('page_path' in widget_json)

        test_page = Page.objects.create(slug="banner_test")
        widget.link = test_page
        widget.save()
        widget_json = self.get_widget_json(widget)
        self.assertEqual(widget_json['page_path'], '/page/{}'.format(test_page.id))

    def test_image_carousel_widget(self):
        """
        Verify that the ad carousel widget correctly reports type and ads (image path & image_url for each)
        """
        widget = ImageCarouselWidget.objects.create(name="test")
        pages = []
        for i in range(3):
            image = widget.images.create(
                link=Page.objects.create(name="Image page {}".format(i), slug="image{}".format(i)),
                image=make_image_file(size=(1536, 1024), color="#DEFACE"),
                sort_order=i,
            )
            pages.append(image.link)
            image.full_clean()
            image.save()

        widget_json = self.get_widget_json(widget)
        self.assertEqual(widget_json["type"], "image_carousel")
        self.assertEqual(len(widget_json["images"]), 3)
        for image_json, page in zip(widget_json["images"], pages):
            self.assertSetEqual({"image", "path", "start_date", "end_date"}, set(image_json.keys()))
            self.assertEqual(image_json["path"], '/page/{}'.format(page.id))

    def test_person_focus_widget(self):
        """
        Verify that the ad carousel widget correctly reports type and ads (image path & image_url for each)
        """
        person = self.person1
        person_focus_widget = PersonFocusWidget.objects.create(name="Funnyboy Jones", person=person)
        page = Page.objects.create(name="Page of Person Focus Widgets")
        page.add_widget(person_focus_widget)

        widget_json = self.get_widget_json(person_focus_widget)
        self.assertEqual(widget_json["type"], "person_focus")
        self.assertIn("person", widget_json)
        person_json = widget_json["person"]
        self.assertEqual(person_json["name"], "Funnyboy Jones")

    def test_widget_link(self):
        """
        Verify that widgets with links render the correct url to dummy pages for various link types
        """
        event = Event.objects.first()
        person = Person.objects.first()
        for linked_obj in [event, person]:
            expected_url = linked_obj.get_api_url()

            widget = BannerWidget.objects.create(
                name="banner test",
                image=make_image_file(size=(2048, 1), color="#ffffff"),
                link=linked_obj,
            )
            widget_json = self.get_widget_json(widget)
            self.assertEqual(widget_json['page_path'], expected_url)

            widget = ImageCarouselWidget.objects.create(name="Image group test")
            widget.images.create(
                link=linked_obj,
                image=make_image_file(size=(320, 216), color="#123456"),
                sort_order=1,
            )
            widget_json = self.get_widget_json(widget)
            self.assertEqual(widget_json['images'][0]['path'], expected_url)

    def test_widget_time_limit(self):
        """
        Verify that widgets aren't displayed before their start_date or after their end_date
        """
        page = Page.objects.create(name="Testing widget expiration")

        unlimited_widget = TextWidget.objects.create(name="always", content="no time limit")
        early_widget = TextWidget.objects.create(
            name="future", content="not yet visible",
            start_date=datetime.now() + timedelta(days=1)
        )
        late_widget = TextWidget.objects.create(
            name="past", content="I am expired",
            end_date=datetime.now() - timedelta(days=1)
        )
        current_widget = TextWidget.objects.create(
            name="current", content="game on",
            start_date=datetime.now() - timedelta(days=1),
            end_date=datetime.now() + timedelta(days=1)
        )
        page.add_widget(unlimited_widget)
        page.add_widget(early_widget)
        page.add_widget(late_widget)
        page.add_widget(current_widget)

        page_data = self.get_page_json(page)
        self.assertEqual(
            ["no time limit", "game on"],
            [w["text"] for w in page_data["widgets"]]
        )

    def test_widget_item_time_limit(self):
        """
        Verify that Widget items aren't displayed before their start_date or after their end_date
        """
        for WidgetClass, size, item_key in [
            (ImageCarouselWidget, (1536, 1024), 'images')
        ]:
            page = Page.objects.create(name="Testing widget expiration")
            widget = WidgetClass.objects.create(name="group of images")
            page.add_widget(widget)
            widget.images.create(
                sort_order=1,
                link=page,
                image=make_image_file(size=size, color="#000000"),
            )
            widget.images.create(
                sort_order=2,
                link=page,
                image=make_image_file(size=size, color="#111111"),
                end_date=datetime.now() - timedelta(days=1)  # past
            )
            widget.images.create(
                sort_order=3,
                link=page,
                image=make_image_file(size=size, color="#222222"),
                start_date=datetime.now() - timedelta(days=1),  # present
                end_date=datetime.now() + timedelta(days=1)
            )
            widget.images.create(
                sort_order=4,
                link=page,
                image=make_image_file(size=size, color="#333333"),
                start_date=datetime.now() + timedelta(days=1)  # future
            )
            for image in widget.images.all():
                image.full_clean()
                image.save()

            page_data = self.get_page_json(page)
            self.assertEqual(1, len(page_data['widgets']))

    def test_new_releases_window(self):
        """
        Make sure BooksWidget is limited by new_releases_window days
        """
        self.event1.start_time=datetime.now() + timedelta(days=1)
        self.event1.save()
        self.event2.start_time=datetime.now() + timedelta(days=2)
        self.event2.save()
        widget = EventsWidget.objects.create(name="Upcoming Shows", upcoming_events=True, upcoming_events_window=7)

        widget_json = self.get_widget_json(widget)
        self.assertEqual(widget_json["item_type"], "event")
        self.assertEqual(len(widget_json["items"]), 2)

        widget.upcoming_events_window = 1
        widget.save()

        widget_json = self.get_widget_json(widget)
        self.assertEqual(widget_json["item_type"], "event")
        self.assertEqual(len(widget_json["items"]), 1)


class WebPageWrapperTest(TestCase):
    """
    NOT WORKING YET


    Tests features of the new page system powering the site. The content of each page is generated through the admin,
    and mirrors the content of the respective API resource for that page. These tests verify that the content of the
    HTML matches up with its corresponding API resource.
    """

    def setUp(self):
        self.house_team = HouseTeam.objects.create(name="The Goof Troop")
        self.person1 = Person.objects.create(first_name="Funnyboy", last_name="Jones")
        self.person2 = Person.objects.create(first_name="Lisa", last_name="Crackemups")

        HouseTeamMembership.objects.create(person=self.person1, house_team=self.house_team)
        HouseTeamMembership.objects.create(person=self.person2, house_team=self.house_team)

        self.event1 = Event.objects.create(name="Friday Night Laffs", bio="Every Friday!", ticket_price=10)


    def assert_page_widgets(self, page_url, widgets):
        """
        Asserts that the rendered html for a given page aligns with the expected data
        """
        response = self.client.get(page_url)
        self.assertEqual(response.status_code, 200)
        soup = BeautifulSoup(response.content)

        widget_nodes = soup.select("ul#widgets-list li.widget")
        self.assertEqual(len(widgets), len(widget_nodes))
        for widget, widget_html in zip(widgets, widget_nodes):
            type = widget.get('type').replace('_', '-')
            self.assertTrue(widget_html.find(attrs={'class': 'page-{}'.format(type)}))
            if widget['type'] not in ['banner', 'text'] and widget.get('item_type') != 'ad':
                title = widget_html.find('h2').text.replace('\n', '').strip()
                self.assertEqual(title, widget.get('title'))

            for item in widget.get('items', []):
                selector = item['select']
                self.assertTrue(widget_html.select(selector), msg="No item matching {}".format(selector))
        return soup

    def test_custom_page(self):
        custom_page = Page.objects.create(name="custom content")

        banner_widget = BannerWidget.objects.create(name="Banner Widget",
                                                    image=make_image_file(size=(2048, 1), color="#ff0000"))

        text_widget = TextWidget.objects.create(name="Text Widget", content="text")

        custom_page.add_widget(banner_widget)
        custom_page.add_widget(text_widget)

        url_params = {'page_path': '/page/{0}/{1}'.format(custom_page.id, custom_page.link_slug)}
        page_url = reverse('web_page_wrapper', kwargs=url_params)

        self.assert_page_widgets(page_url, [
            {'type': 'banner'},
            {'type': 'text', 'title': "Text Widget"},
        ])

    # for pages/<slug> urls
    def test_slug_page(self):
        page = Page.objects.create(
            name='Slug',
            slug='slug'
        )
        page.add_widget(
            BannerWidget.objects.create(name="Banner Widget",
                                        image=make_image_file(size=(2048, 1), color="#ff0000"))
        )

        page_url = reverse('slug_page_wrapper', kwargs={'page_slug': 'slug'})
        self.assert_page_widgets(page_url, [
            {'type': 'banner'}
        ])

    def test_page_slug_redirect(self):
        """
        Verify that created pages will properly redirect to the url with a title slug
        """
        page = Page.objects.create(name="Pagey McPageface")
        # ensure page request without a slug redirects
        url_params = {'page_path': '/page/{}/'.format(page.id)}
        page_url = reverse('web_page_wrapper', kwargs=url_params)

        response = self.client.get(page_url)
        self.assertRedirects(response, expected_url='/page/{0}/{1}'.format(page.id, page.link_slug),
                             status_code=301)

        # ensure a page request with slug does not redirect
        url_params = {'page_path': '/page/{}/{}'.format(page.id, page.link_slug)}
        page_url = reverse('web_page_wrapper', kwargs=url_params)

        response = self.client.get(page_url)
        self.assertEqual(response.status_code, 200)

    def test_get_404_as_guest(self):
        self.client.logout()
        url = "page/thisisinnowayshapeorformavalidurl"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_wrapped_url(self):
        """
        the wrapped_url template tag takes an api_url as input and returns a reversed web url.
        """
        # test a slugged page api_url
        page = Page.objects.create(name="Featured", slug="featured")
        api_url = page.get_api_url()
        web_url = wrapped_url(api_url)
        self.assertEqual(web_url, '/{}'.format(page.id))
        # and ensure it resolves
        response = self.client.get(web_url)
        self.assertEqual(response.status_code, 200)

