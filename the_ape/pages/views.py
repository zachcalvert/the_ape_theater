import json
import re

from django.contrib import messages
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse, Resolver404, resolve
from django.http import Http404, HttpResponse
from django.http.response import HttpResponsePermanentRedirect
from django.shortcuts import render, render_to_response, get_object_or_404
from django.template.response import TemplateResponse
from django.template import TemplateDoesNotExist, RequestContext
from django.template.loader import get_template
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.views.generic import View, TemplateView

from accounts.models import ClassMember, UserProfile, EventAttendee
from classes.models import ApeClass
from events.models import Event
from pages.models import Page, EventsWidget, PeopleWidget, ApeClassesWidget, \
    ImageCarouselWidget, BannerWidget
from pages.templatetags.page_tags import get_slug_redirect
from people.models import Person, HouseTeam


REDIRECT_NEEDED_URL_PATTERNS = [
    'ape_class',
    'event',
    'person',
    'house_team',
]
# need this because the url match detected for these categories is just 'web_page_wrapper'
REDIRECT_NEEDED_WRAPPER_PATTERN = re.compile('^/(series|contributors)/(?P<item_id>\d+)')


def handler404(request):
    response = render_to_response('404.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 404
    return response


def handler500(request):
    response = render_to_response('500.html', {},
                                  context_instance=RequestContext(request))
    response.status_code = 500
    return response


class JSONHttpResponse(HttpResponse):
    def __init__(self, content=None, *args, **kwargs):
        kwargs['content_type'] = 'application/json'
        content = json.dumps(content, cls=DjangoJSONEncoder)
        super(JSONHttpResponse, self).__init__(content, *args, **kwargs)


class JSONView(View):

    def dispatch(self, request, *args, **kwargs):
        data = super(JSONView, self).dispatch(request, *args, **kwargs)

        if isinstance(data, HttpResponse):
            return data
        else:
            return JSONHttpResponse(data)


def widget_for_group(group, **kwargs):
    """
    Create (but don't save) a widget of the correct subclass of CatalogGroupWidget based on the contents of the group.

    Widget is created using **kwargs
    :return:
    """
    if isinstance(group, Event):
        widget_class = EventsWidget
    elif isinstance(group, Person):
        widget_class = PeopleWidget
    else:
        widget_class = ApeClassesWidget

    kwargs.setdefault('name', group.name)
    return widget_class(**kwargs)


class PageView(JSONView):
    content_type = "text/json"

    def dispatch(self, request, *args, **kwargs):
        if self.request.path == 'favicon.ico':
            return HttpResponse(status_code=200)

        return super(PageView, self).dispatch(request, *args, **kwargs)

    def get_page(self, page_id=None, page_slug=None, **kwargs):
        if page_id:
            page = get_object_or_404(Page, id=page_id)
        elif page_slug:
            try:
                page = Page.objects.get(slug=page_slug)
            except Page.DoesNotExist:
                return None
        else:
            raise Http404()
        return page

    def get(self, request, *args, **kwargs):
        page = self.get_page(**kwargs)
        if not page:
            page = Page.objects.get(slug='home')
        page_data = page.to_data()
        return page_data


class WebPageWrapperView(TemplateView):
    template_name = "pages/page.html"
    context_object_name = "page"
    url_namespace = 'pages.api_urls'

    def get_api_url(self, page_path, *args, **kwargs):
        return u"/pages/" + page_path.strip('/') + u".json"

    def dispatch(self, request, *args, **kwargs):
        try:
            if 'favicon.ico' in self.request.path:
                return HttpResponse(200)
            resolver_match = resolve(self.get_api_url(*args, **kwargs), self.url_namespace)
        except Resolver404:
            raise Http404

        resolved_url_name = resolver_match.url_name

        if resolved_url_name in REDIRECT_NEEDED_URL_PATTERNS and not kwargs.get('page_slug'):
            redirect_url = get_slug_redirect(request.path)
            if redirect_url:
                return HttpResponsePermanentRedirect(redirect_url)  # uses a 301 instead of 302 code

        response = resolver_match.func(request, *resolver_match.args, **resolver_match.kwargs)
        if response.status_code >= 400:
            return response

        # working solution
        if isinstance(response, TemplateResponse):
            response.render()

        self.page_data = json.loads(response.content.decode())
        for widget in self.page_data.get('widgets', []):
            template_name = "widgets/{}.html".format(widget['type'])
            try:
                get_template(template_name)
            except TemplateDoesNotExist:
                pass
            else:
                widget['template_name'] = template_name

        return super(WebPageWrapperView, self).dispatch(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super(WebPageWrapperView, self).get_context_data(**kwargs)
        context[self.context_object_name] = self.page_data
        return context


class PageIDWrapperView(WebPageWrapperView):

    def get_api_url(self, page_id=None, slug=None, *args, **kwargs):
        return reverse('page', kwargs={'page_id': page_id}, urlconf='pages.api_urls')


class SlugPageWrapperView(WebPageWrapperView):
    page_slug = None

    def get_api_url(self, page_slug=None, *args, **kwargs):
        page_slug = page_slug or self.page_slug
        return reverse('page', kwargs={'page_slug': page_slug}, urlconf='pages.api_urls')


class ApeClassWrapperView(WebPageWrapperView):
    template_name = "classes/ape_class.html"
    context_object_name = "ape_class"

    def get_api_url(self, ape_class_id, *args, **kwargs):
        return reverse('ape_class', kwargs={'ape_class_id': ape_class_id}, urlconf='pages.api_urls')

    def get_context_data(self, ape_class_id, **kwargs):
        context = super(ApeClassWrapperView, self).get_context_data(**kwargs)
        ape_class = get_object_or_404(ApeClass, pk=ape_class_id)
        if self.request.user.is_authenticated:
            try:
                is_registered = ClassMember.objects.filter(student=self.request.user.profile, ape_class=ape_class).exists()
            except UserProfile.DoesNotExist:
                is_registered = False
            if is_registered:
                messages.success(self.request, mark_safe("Woohoo! You're registered for this class! See your registration <a href='/profile/'>here</a>."))
        else:
            is_registered = False
        context['class'] = ape_class.to_data()
        return context


class EventWrapperView(WebPageWrapperView):
    template_name = "events/event.html"
    context_object_name = "event"

    def get_api_url(self, event_id, *args, **kwargs):
        return reverse('event', kwargs={'event_id': event_id}, urlconf='pages.api_urls')

    def get_context_data(self, event_id, **kwargs):
        context = super(EventWrapperView, self).get_context_data(**kwargs)
        event = get_object_or_404(Event, pk=event_id)
        context['event'] = event.to_data()
        return context


class PersonWrapperView(WebPageWrapperView):
    template_name = "people/person.html"
    context_object_name = "person"

    def get_api_url(self, person_id, *args, **kwargs):
        return reverse('person', kwargs={'person_id': person_id}, urlconf='pages.api_urls')

    def get_context_data(self, person_id, **kwargs):
        context = super(PersonWrapperView, self).get_context_data(**kwargs)
        person = get_object_or_404(Person, pk=person_id)
        context['person'] = person.to_data()
        return context


class HouseTeamWrapperView(WebPageWrapperView):
    template_name = "people/house_team.html"
    context_object_name = "person"

    def get_api_url(self, house_team_id, *args, **kwargs):
        return reverse('house_team', kwargs={'house_team_id': house_team_id}, urlconf='pages.api_urls')

    def get_context_data(self, house_team_id, **kwargs):
        context = super(HouseTeamWrapperView, self).get_context_data(**kwargs)
        house_team = get_object_or_404(HouseTeam, pk=house_team_id)
        context['house_team'] = house_team.to_data()
        return context


class EventView(JSONView):

    def get(self, request, event_id):
        event = get_object_or_404(Event, pk=event_id)
        data = event.to_data()
        return data


class PersonView(JSONView):

    def get(self, request, person_id):
        person = get_object_or_404(Person, pk=person_id)
        data = person.to_data()
        return data


class ApeClassView(JSONView):

    def get(self, request, ape_class_id):
        ape_class = get_object_or_404(ApeClass, pk=ape_class_id)
        data = ape_class.to_data()
        return data


class HouseTeamView(JSONView):

    def get(self, request, house_team_id):
        house_team = get_object_or_404(HouseTeam, pk=house_team_id)
        data = house_team.to_data()
        return data
