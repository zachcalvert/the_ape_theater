from django.core.urlresolvers import reverse, Resolver404, resolve
from django.http import Http404, HttpResponse
from django.shortcuts import render
from django.template.response import TemplateResponse
from django.template import TemplateDoesNotExist
from django.template.loader import get_template
from django.views.generic import View, TemplateView

class PageView(TemplateView):
    template_name = "pages/page.html"
    context_object_name = "page"

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


class SlugPageView(PageView):
    page_slug = None

    def get(self, page_slug=None, *args, **kwargs):
        page_slug = page_slug or self.page_slug
        return reverse('page', kwargs={'page_slug': page_slug}, urlconf='pages.api_urls')


class EventView(TemplateView):
    template_name = 'events/event.html'


class ApeClassView(TemplateView):
    template_name = 'classes/ape_class.html'


class PersonView(TemplateView):
    template_name = 'people/person.html'