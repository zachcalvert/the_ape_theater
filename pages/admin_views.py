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
from people.models import Person


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

    def get_context_data(self, **kwargs):
        query = self.request.GET.get('q')
        data = super(GenericObjectLookup, self).get_context_data(**kwargs)

        size = 0
        sections_query = self.request.GET.get('sections', '')
        if sections_query:
            # allow either content type id or model name
            sections = []
            for section_lookup in sections_query.split(','):
                try:
                    if section_lookup.isdigit():
                        section = ContentType.objects.get(id=section_lookup)
                    else:
                        section = ContentType.objects.get(model=section_lookup)
                    sections.append(section.model_class())
                except (ContentType.DoesNotExist, ContentType.MultipleObjectsReturned):
                    pass
        else:
            sections = [Director, Actor, Writer, Genre]

        #reduce all catalog types to the lowest level (we'll show everything above that anyway)
        catalog_limit = None
        cat_index = 0
        for cat_type in [ApeClass, Event, Person]:
            if cat_type in sections:
                cat_index = sections.index(cat_type)
                sections.remove(cat_type)
                catalog_limit = cat_type
        if catalog_limit:
            sections.insert(cat_index, catalog_limit)

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