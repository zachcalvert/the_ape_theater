from collections import OrderedDict
from django.apps import apps
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.http import Http404
from django.shortcuts import get_object_or_404
from django.views.generic import TemplateView

from classes.models import ApeClass
from events.models import Event
from pages.models import Page, Widget, PageToWidget
from pages.admin_forms import get_widget_form
from people.models import Person, HouseTeam


class WidgetFormView(TemplateView):

    template_name = "admin/pages/inline/widget_form.html"

    def get_context_data(self, **kwargs):
        data = super(WidgetFormView, self).get_context_data(**kwargs)

        prefix = self.request.GET.get('prefix', '__prefix__')
        if 'widget_id' in self.request.GET:
            widget = get_object_or_404(Widget, id=self.request.GET['widget_id']).get_subclass()
            if hasattr(widget, 'get_proxied_widget'):
                widget = widget.get_proxied_widget()
            widget_model = type(widget)
        elif 'widget_type_name' in kwargs:
            widget = None
            widget_model = apps.get_model("pages", kwargs['widget_type_name'])
        else:
            raise Http404()

        form = get_widget_form(
            widget_model,
            prefix=prefix,
            instance=widget
        )
        data['widget_form'] = form
        return data


class WidgetNameLookupView(TemplateView):
    template_name = "admin/pages/inline/widget_options.html"

    def get_context_data(self, **kwargs):
        context = super(WidgetNameLookupView, self).get_context_data(**kwargs)

        query = self.request.GET.get('q')
        widgets = Widget.objects.filter(name__icontains=query).select_subclasses()
        context['widgets'] = widgets
        group_count = len({w.type_name() for w in context['widgets']})
        context['size'] = min(20, max(widgets.count(), 1) + group_count)

        return context


class WidgetPageLookupView(TemplateView):
    template_name = "admin/pages/inline/page_widget_options.html"

    def get_context_data(self, **kwargs):
        context = super(WidgetPageLookupView, self).get_context_data(**kwargs)

        query = self.request.GET.get('q')
        pages = Page.objects.filter(name__icontains=query)
        context['pages'] = pages
        context['size'] = min(20, max(pages.count() + PageToWidget.objects.filter(page__in=pages).count(), 1))

        return context


class GenericObjectLookup(TemplateView):
    template_name = "admin/pages/inline/generic_object_lookup.html"

    def source_event_options(self, query):
        return Event.objects.filter(name__icontains=query)

    def source_apeclass_options(self, query):
        return ApeClass.objects.filter(name__icontains=query)

    def source_person_options(selfself, query):
        return Person.objects.filter(first_name__icontains=query)

    def source_page_options(self, query):
        return Page.objects.filter(name__icontains=query)

    def source_houseteam_options(self, query):
        return HouseTeam.objects.filter(name__icontains=query)

    def get_context_data(self, **kwargs):
        query = self.request.GET.get('q')
        data = super(GenericObjectLookup, self).get_context_data(**kwargs)

        size = 0
        sections = [ApeClass, Event, HouseTeam, Person, Page]

        section_data = OrderedDict()
        for section in sections:
            funcname = "source_{}_options".format(section._meta.model_name)
            if hasattr(self, funcname):
                size += 1
                getter = getattr(self, funcname)
                options = getter(query)
                size += max(len(options), 1)
                section_data[section._meta.verbose_name_plural] = options

        data['sections'] = section_data
        data['size'] = min(size, 20)

        return data
