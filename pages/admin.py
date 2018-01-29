from django.apps import apps
from django.contrib import admin
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.db import models
from django.utils.safestring import mark_safe

from pages.admin_forms import PageForm, FilteredSelect, get_widget_form
from pages.admin_views import WidgetFormView, WidgetNameLookupView, WidgetPageLookupView
from pages.models import Page, BannerWidget, ImageCarouselWidget, \
PeopleWidget, PersonFocusWidget, ApeClassesWidget
from pages.templatetags.page_tags import admin_url

WIDGET_MODELS = [BannerWidget, ImageCarouselWidget, PeopleWidget, PersonFocusWidget, ApeClassesWidget]


class AjaxModelAdmin(admin.ModelAdmin):
    class Media:
        js = (
            "js/jquery.admin-compat.js",
            "js/admin/the_ape.js",
        )
        css = {
             'all': ('css/my_grappelli.css',)
        }

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        request.form_instance = context['adminform'].form
        return super(AjaxModelAdmin, self).render_change_form(request, context, add, change, form_url, obj)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        response = super(AjaxModelAdmin, self).change_view(request, object_id, form_url, extra_context)
        if request.is_ajax():
            messages = get_messages(request)
            response_json = {"messages": [{'level': m.level, 'message': m.message, 'tags': m.tags} for m in messages],
                             'errors': {}}
            if hasattr(request, 'form_instance') and not request.form_instance.is_valid():
                response_json['errors'].update(request.form_instance.errors)
            # add inline_formset errors
            # TODO This could potentially trigger a bug in future django. context_data is not guaranteed to be there.
            if hasattr(response, 'context_data'):
                for formset in response.context_data['inline_admin_formsets']:
                    for form in formset.formset.forms:
                        if not form.is_valid():
                            for field, error in form.errors.iteritems():
                                response_json['errors']["{}-{}".format(form.prefix, field)] = error
            return pages.views.JSONHttpResponse(response_json)
        else:
            return response


class SortedManyToManyAdmin(AjaxModelAdmin):

    def formfield_for_manytomany(self, db_field, request=None, **kwargs):
        if isinstance(db_field, SortedManyToManyField):
            kwargs['widget'] = FilteredSelectMultiple(verbose_name=db_field.verbose_name, is_stacked=False)
            return db_field.formfield(**kwargs)
        else:
            return super(SortedManyToManyAdmin, self).formfield_for_manytomany(db_field, request, **kwargs)


class PageAdmin(SortedManyToManyAdmin):
    search_fields = ['name', 'slug']
    list_display = ['name', 'url', 'created', 'last_modified', 'draft']
    list_filter = ['slug', 'draft']
    date_hierarchy = 'created'
    readonly_fields = ('created', 'last_modified')
    fieldsets = (
        (None, {
            'fields': ('name', ('created', 'last_modified', 'slug'), 'draft')
        }),
    )
    form = PageForm
    formfield_overrides = {
        models.ForeignKey: {'widget': FilteredSelect},
    }

    class Media:
        js = AjaxModelAdmin.Media.js + (
            "js/admin/pages/page.js",
            "js/jquery.typewatch.js",
            "js/FilteredSelect.js",
            "js/admin/pages/generic_lookup.js",
        )
        css = {
            "all": (
                "css/admin/pages/page/change.css",
                "css/filtered_select.css",
                "css/admin/pages/generic_lookup.css",
            )
        }

    def url(self, page):
        return mark_safe(u"<a href='{0}' target='_new'>{0}</a>".format(page.get_url()))

    def get_urls(self):
        from django.conf.urls import url

        app_name = self.model._meta.app_label
        model_name = self.model._meta.model_name

        urlpatterns = [
            url(r'^widget_form/$',
                self.admin_site.admin_view(WidgetFormView.as_view()),
                name='{}_{}_widget_form'.format(app_name, model_name)),
            url(r'^widget_form/(?P<widget_type_name>\w+)/$',
                self.admin_site.admin_view(WidgetFormView.as_view()),
                name='{}_{}_widget_form'.format(app_name, model_name)),
            url(r'^widget_name_lookup/$',
                self.admin_site.admin_view(WidgetNameLookupView.as_view()),
                name='{}_{}_widget_name_lookup'.format(app_name, model_name)),
            url(r'^widget_page_name_lookup/$',
                self.admin_site.admin_view(WidgetPageLookupView.as_view()),
                name='{}_{}_widget_page_name_lookup'.format(app_name, model_name)),
        ] + super(PageAdmin, self).get_urls()
        return urlpatterns

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        context['form'] = context['adminform'].form
        context['widget_types'] = [w._meta for w in WIDGET_MODELS]

        # set up "will replace" warnings for slug dropdown
        slug_pages = Page.objects.filter(slug__isnull=False)
        if obj:
            slug_pages = slug_pages.exclude(pk=obj.pk)
        context['slug_pages'] = slug_pages

        return super(PageAdmin, self).render_change_form(request, context, add, change, form_url, obj)

    def save_form(self, request, form, change):
        return form.save(commit=True)


admin.site.register(Page, PageAdmin)


class GroupWidgetAdmin(admin.ModelAdmin):
    search_fields = ["name", "pages__name"]
    list_display = ["name", "page_links"]
    readonly_fields = ['page_links']
    exclude = [
        'link_id',
        'link_type',

        'source_genre',
        'source_director',
        'source_actor',
        'source_writer',
        'source_year',
    ]
    default_exclude = [
        'name',
        'start_date',
        'end_date',
        'page_links',
        'link',
        'source',

        'movie',
    ]
    change_form_template = "admin/pages/widget_change_form.html"

    class Media:
        js = AjaxModelAdmin.Media.js + (
            "js/admin/pages/page.js",
            "js/jquery.typewatch.js",
        )
        css = {
            "all": (
                "css/admin/pages/widget/change.css",
            )
        }

    def get_form(self, request, obj=None, **kwargs):
        kwargs['form'] = type(get_widget_form(self.model, inline=False))
        return super(GroupWidgetAdmin, self).get_form(request, obj=obj, **kwargs)

    def save_form(self, request, form, change):
        return form.save(commit=True)

    def page_links(self, widget):
        output = ["<ul>"]

        for page in widget.pages.all():
            output.append("<li>")
            output.append("<a href='{url}'>{label}</a>".format(
                url=admin_url(page),
                label=page.name
            ))
            output.append("</li>")

        output.append("</ul>")
        return mark_safe(" ".join(output))
    page_links.short_description = "pages"


for model in WIDGET_MODELS:
    try:
        admin.site.register(model, GroupWidgetAdmin)
    except AlreadyRegistered:
        pass
