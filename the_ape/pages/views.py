import json

from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.serializers.json import DjangoJSONEncoder
from django.core.urlresolvers import reverse, Resolver404, resolve
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.urls import reverse
from django.views.generic import View, TemplateView

from classes.models import ApeClass, Student
from events.models import Event
from pages.models import Page
from people.models import Person, HouseTeam


class JSONHttpResponse(HttpResponse):
    def __init__(self, content=None, *args, **kwargs):
        kwargs['content_type'] = 'application/json'
        content = json.dumps(content, cls=DjangoJSONEncoder)
        super(JSONHttpResponse, self).__init__(content, *args, **kwargs)


class PageView(TemplateView):
    template_name = 'page.json'

    def get_context_data(self, **kwargs):
        context = super(PageView, self).get_context_data(**kwargs)

        if kwargs.get('page_slug'):
            page = Page.objects.get(slug=kwargs['page_slug'])
        else:
            try:
                page = Page.objects.get(id=kwargs['page_id'])
            except KeyError:
                return 'what'

        context['page'] = page

        return context


class WebPageWrapperView(TemplateView):
    template_name = "pages/page.html"
    context_object_name = "page"
    url_namespace = 'pages.api_urls'

    def get_api_url(self, page_path, *args, **kwargs):
        return u"/pages/" + page_path.strip('/') + u".json"

    def dispatch(self, request, *args, **kwargs):
        try:
            resolver_match = resolve(self.get_api_url(*args, **kwargs), self.url_namespace)
        except Resolver404:
            raise Http404

        request.META['HTTP_X_DHDEVICEOS'] = 'web'
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


class SlugPageWrapperView(WebPageWrapperView):
    page_slug = None

    def get_api_url(self, page_slug=None, *args, **kwargs):
        page_slug = page_slug or self.page_slug
        return reverse('page', kwargs={'page_slug': page_slug}, urlconf='pages.api_urls')


class ApeClassWrapperView(WebPageWrapperView):
    template_name = "classes/ape_class.html"
    context_object_name = "ape_class"

    def get_api_url(self, class_id, *args, **kwargs):
        return reverse('class', kwargs={'class_id': class_id}, urlconf='pages.api_urls')


class EventWrapperView(WebPageWrapperView):
    template_name = "events/event.html"
    context_object_name = "event"

    def get_api_url(self, event_id, *args, **kwargs):
        return reverse('event', kwargs={'event_id': event_id}, urlconf='pages.api_urls')


class PersonWrapperView(WebPageWrapperView):
    template_name = "people/person_focus.html"
    context_object_name = "person"

    def get_api_url(self, person_id, *args, **kwargs):
        return reverse('person', kwargs={'person_id': person_id}, urlconf='pages.api_urls')


class EventView(View):
    def event_data(self, event):
        event_dict = {
            'id': event.id,
            'name': event.name,
            'bio': event.bio,
            'start_time': str(event.start_time),
            'max_tickets': event.max_tickets,
            'tickets_sold': event.tickets_sold,
            'ticket_price': str(event.ticket_price),
            'banner_url': event.banner.image.url
        }

        return event_dict

    def get(self, request, event_id):
        try:
            event = Event.objects.get(id=event_id)
        except Event.DoesNotExist:
            raise Http404()

        api_dict = self.event_data(event)

        return HttpResponse(json.dumps(api_dict))


class PersonView(View):
    def person_data(self, person):
        person_dict = {
            'id': person.id,
            'name': person.name,
            'image_url': person.image.url,
            'house_team': person.house_team.name,
            'url': person.get_absolute_url()
        }
        return person_dict

    def get(self, request, person_id):
        try:
            person = Person.objects.get(id=person_id)
        except Person.DoesNotExist:
            raise Http404()

        api_dict = self.person_data(person)

        return HttpResponse(json.dumps(api_dict))


class ApeClassView(View):
    def ape_class_data(self, ape_class):
        ape_class_dict = {
            'id': ape_class.id,
            'name': ape_class.name,
            'bio': ape_class.bio,
        }

        return ape_class_dict

    def get(self, request, ape_class_id):
        try:
            ape_class = ApeClass.objects.get(id=ape_class_id)
        except ApeClass.DoesNotExist:
            raise Http404()

        api_dict = self.ape_class_data(ape_class)

        return HttpResponse(json.dumps(api_dict))
