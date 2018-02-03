from django.conf import settings
from django.contrib.admin.widgets import AdminSplitDateTime
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse_lazy as reverse
from django.db.models import Model
from django.apps import apps
from django.forms.formsets import DELETION_FIELD_NAME
from django.forms.models import inlineformset_factory
from django import forms
from django.utils.safestring import mark_safe
from django.utils.text import capfirst

from django.contrib.admin.templatetags.admin_static import static
from django.forms import Select, TextInput

from classes.models import Student, ApeClass
from events.models import Event
import pages.models
from people.models import HouseTeam, Person


class FilteredSelect(Select):

    class Media:
        js = [static("js/FilteredSelect.js")]
        css = {'all': [static("css/filtered_select.css")]}

    def render(self, *args, **kwargs):
        attrs = kwargs.setdefault('attrs', {})
        css_class = attrs.setdefault('class', '')+" filtered-select"
        attrs['class'] = css_class
        rendered = super(FilteredSelect, self).render(*args, **kwargs)
        return mark_safe(rendered)


class GenericLookupWidget(forms.MultiWidget):
    class Media:
        js = (settings.STATIC_URL + "js/admin/pages/generic_lookup.js",)
        css = {
            "all": (settings.STATIC_URL + "css/admin/pages/generic_lookup.css",)
        }

    def __init__(self, attrs=None, sections=None, api_url=None):
        self.sections = sections
        self.api_url = api_url or reverse("generic_object_lookup")
        super(GenericLookupWidget, self).__init__(widgets=[
            forms.HiddenInput(attrs={'class': "generic-object-id"}),
            forms.HiddenInput(attrs={'class': "generic-content-type-id"}),
            forms.TextInput(attrs={
                'class': "generic-field-lookup vTextField grp-search-field",
                'placeholder': "Type here to search",
                'api_url': self.api_url
            }),
        ], attrs=attrs)

    def render(self, name, value, attrs=None):
        if self.sections:
            url = self.api_url + "?sections=" + ",".join([str(s) for s in self.sections])
            self.widgets[2].attrs['api_url'] = url
        output = super(GenericLookupWidget, self).render(name, value, attrs)
        output = u"<div class='generic-lookup-wrapper'>{}</div>".format(output)
        return mark_safe(output)

    def decompress(self, value):
        if value and isinstance(value, Model):
            if hasattr(value, 'full_name'):
                name = value.full_name
            else:
                name = value.name
            label = u"{}: {}".format(capfirst(type(value)._meta.verbose_name), name)
            return value.id, ContentType.objects.get_for_model(type(value)).id, label
        else:
            return None, None, ""


class GenericLookupField(forms.MultiValueField):
    def __init__(self, *args, **kwargs):
        sections = kwargs.pop('sections', None)

        kwargs['fields'] = [
            forms.IntegerField(),
            forms.IntegerField(),
            forms.CharField(),
        ]
        kwargs['widget'] = GenericLookupWidget(sections=sections)
        super(GenericLookupField, self).__init__(*args, **kwargs)

    def compress(self, data_list):
        if data_list:
            obj_id, ct_id, lookup = data_list
            content_type = ContentType.objects.get_for_id(id=ct_id)
            obj = content_type.model_class().objects.get(id=obj_id)
            return obj


class FileRecoveryForm(forms.ModelForm):
    """
    When a form is posted to using "_saveasnew", any file fields that were present (and haven't been overridden)
    need to be recovered from the old version of the model
    """
    def __init__(self, *args, **kwargs):
        super(FileRecoveryForm, self).__init__(*args, **kwargs)

        if self.data and '_saveasnew' in self.data:
            # recycle any files living on the old copy
            pk_field = kwargs.get('prefix', '')+"-id"
            if pk_field in self.data:
                old_copy = self._meta.model.objects.get(id=self.data[pk_field])
                for field_name, field in self.fields.items():
                    if isinstance(field, forms.FileField):
                        self.initial[field_name] = getattr(old_copy, field_name).file


class WidgetForm(FileRecoveryForm):
    name = forms.CharField(widget=forms.TextInput(attrs={'class': 'vTextField'}))
    start_date = forms.SplitDateTimeField(widget=AdminSplitDateTime, required=False)
    end_date = forms.SplitDateTimeField(widget=AdminSplitDateTime, required=False)

    class Meta:
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        self.save_as_new = kwargs.pop('save_as_new', False)
        if self.save_as_new:
            kwargs['instance'] = None
        super(WidgetForm, self).__init__(*args, **kwargs)

    def save_m2m(self):
        pass


class InlineWidgetFormMixin(WidgetForm):
    sort_order = forms.IntegerField(widget=forms.HiddenInput(attrs={'class': 'widget-sort-order'}))
    delete = forms.BooleanField(widget=forms.HiddenInput(attrs={'class': 'widget-delete'}),
                                initial=False, required=False)

    def is_valid(self):
        result = super(InlineWidgetFormMixin, self).is_valid()
        if self.cleaned_data.get('delete', False):
            return True
        else:
            return result


class PageLinkFormMixin(forms.ModelForm):
    link = GenericLookupField(
        required=False,
        label="Link to",
    )

    class Meta:
        exclude = (
            'link_id',
            'link_type',
        )

    def __init__(self, *args, **kwargs):
        super(PageLinkFormMixin, self).__init__(*args, **kwargs)
        self.fields['link'].widget.sections = [
            ContentType.objects.get_for_model(model).id
            for model in [ApeClass, Event, Person, HouseTeam]
        ]
        if self.instance:
            self.initial['link'] = self.instance.link

    def clean(self):
        self.instance.link = self.cleaned_data.get('link')
        return super(PageLinkFormMixin, self).clean()


class PageLinkWidgetForm(WidgetForm, PageLinkFormMixin):
    class Meta(PageLinkFormMixin.Meta):
        pass


class WidgetItemForm(FileRecoveryForm, PageLinkFormMixin):
    sort_order = forms.IntegerField(widget=forms.HiddenInput(attrs={'class': "widget-item-sort-order"}))
    start_date = forms.SplitDateTimeField(widget=AdminSplitDateTime, required=False)
    end_date = forms.SplitDateTimeField(widget=AdminSplitDateTime, required=False)

    class Meta(PageLinkFormMixin.Meta):
        pass

    def __init__(self, *args, **kwargs):
        super(WidgetItemForm, self).__init__(*args, **kwargs)
        # put start & end date at the end of the form fields
        self.fields['start_date'] = self.fields.pop('start_date')
        self.fields['end_date'] = self.fields.pop('end_date')


class WidgetItemFormset(forms.models.BaseInlineFormSet):
    def add_fields(self, form, index):
        super(WidgetItemFormset, self).add_fields(form, index)
        form.fields[DELETION_FIELD_NAME].widget = forms.HiddenInput(attrs={'class': "widget-item-delete"})


class AbstractGroupWidgetForm(WidgetForm):
    item_model = None  # override in subclasses
    item_form = WidgetItemForm

    def __init__(self, *args, **kwargs):
        super(AbstractGroupWidgetForm, self).__init__(*args, **kwargs)
        ItemFormset = inlineformset_factory(
            self.Meta.model, self.item_model,
            formset=WidgetItemFormset,
            form=self.item_form,
            can_delete=True,
            extra=0
        )
        ItemFormset.opts = self.item_model._meta
        if self.prefix:
            kwargs['prefix'] = self.prefix + "-items"
        else:
            kwargs['prefix'] = "items"
        kwargs['save_as_new'] = self.save_as_new
        self.formset = ItemFormset(*args, **kwargs)

    def is_valid(self):
        valid = super(AbstractGroupWidgetForm, self).is_valid()
        if self.cleaned_data.get('delete', False):
            return True #do this before we check the formsets -- they won't matter anyway
        return valid and self.formset.is_valid()

    def save(self, commit=True):
        widget = super(AbstractGroupWidgetForm, self).save(commit)
        self.formset.instance = widget
        self.formset.save(commit)
        return widget

    def save_m2m(self):
        pass  # for compatability


class ImageCarouselWidgetForm(AbstractGroupWidgetForm):
    item_model = pages.models.ImageCarouselItem


class EventFocusWidgetForm(WidgetForm):
    item_model = pages.models.EventFocusWidget

    class Meta:
        fields = '__all__'
        widgets = {
            'event': FilteredSelect(),
        }


class ApeClassWidgetForm(WidgetForm):
    item_model = pages.models.ApeClass


class PersonWidgetForm(WidgetForm):
    item_model = Person


class EventWidgetForm(WidgetForm):
    item_model = Event


class BannerWidgetForm(WidgetForm):
    item_model = pages.models.BannerWidget


class GroupWidgetForm(WidgetForm):

    def save(self, commit=True):
        return super(GroupWidgetForm, self).save(commit)


def get_widget_form(widget_type=None, prefix='__prefix__', inline=True, data=None, *args, **kwargs):
    prefix = "widget-{}".format(prefix)
    kwargs['prefix'] = prefix
    if data:
        kwargs['data'] = data

    if not widget_type:
        widget_model_name = data.get("{}-model_name".format(prefix))
        if not widget_model_name:
            raise ValidationError("Invalid form: missing model_name")
        widget_type = apps.get_model('pages', widget_model_name)

    registry = {
        pages.models.ImageCarouselWidget: ImageCarouselWidgetForm,
        pages.models.EventFocusWidget: EventFocusWidgetForm,
        pages.models.EventsWidget: EventWidgetForm,
        pages.models.BannerWidget: BannerWidgetForm,
        pages.models.PeopleWidget: PersonWidgetForm,
        pages.models.ApeClassesWidget: ApeClassWidgetForm
    }
    if widget_type in registry:
        BaseForm = registry.get(widget_type)
    else:
        if issubclass(widget_type, pages.models.PageLinkMixin):
            BaseForm = PageLinkWidgetForm
        elif issubclass(widget_type, pages.models.GroupWidget):
            BaseForm = GroupWidgetForm
        else:
            BaseForm = WidgetForm

    if inline:
        class TheWidgetForm(InlineWidgetFormMixin, BaseForm):
            class Meta(BaseForm.Meta):
                model = widget_type
    else:
        class TheWidgetForm(BaseForm):
            class Meta(BaseForm.Meta):
                model = widget_type

    if data:
        kwargs['save_as_new'] = '_saveasnew' in data
        widget_pk = data.get("{}-id".format(prefix))
        if widget_pk:
            kwargs['instance'] = widget_type.objects.get(pk=widget_pk)
        else:
            kwargs['save_as_new'] = True

    form = TheWidgetForm(*args, **kwargs)
    form.opts = widget_type._meta
    return form


class PageForm(forms.ModelForm):
    widget_form_count = forms.IntegerField(widget=forms.HiddenInput, initial=0)

    class Meta:
        model = pages.models.Page
        fields = '__all__'

    @property
    def media(self):
        media = super(PageForm, self).media
        for form in self.widget_forms:
            media += form.media
        return media

    def __init__(self, data=None, files=None, **kwargs):
        super(PageForm, self).__init__(data=data, files=files, **kwargs)
        self.widget_forms = []

        if self.is_bound:
            if 'instance' in kwargs:
                del kwargs['instance']  # already used it to create the page form
            # create widget forms based on the data that was posted
            for i in range(int(data["widget_form_count"])):
                widget_form = get_widget_form(prefix=str(i), data=data, files=files, **kwargs)
                self.widget_forms.append(widget_form)

        elif self.instance and self.instance.pk:
            widgets = self.instance.widgets_base.order_by('page_to_widgets__sort_order')

            self.initial['widget_form_count'] = widgets.count()

            # create initial widget forms from self.instance
            for i, widget in enumerate(widgets):
                if hasattr(widget, 'get_proxied_widget'):
                    widget = widget.get_proxied_widget()
                kwargs['instance'] = widget
                widget_form = get_widget_form(type(widget.get_subclass()), prefix=str(i), **kwargs)
                self.widget_forms.append(widget_form)

    def is_valid(self):
        valid = super(PageForm, self).is_valid()
        for form in self.widget_forms:
            valid = form.is_valid() and valid
        return valid

    @property
    def errors(self):
        errordict = super(PageForm, self).errors
        if self.is_bound:
            extra_forms = list(self.widget_forms)
            for form in self.widget_forms:
                if hasattr(form, 'formset') and not form.formset.is_valid():
                    form.is_valid()  # generate cleaned_data
                    if not form.cleaned_data.get('delete', False):
                        extra_forms.extend(list(form.formset))

            for form in extra_forms:
                if not form.is_valid():
                    for field, errorlist in form.errors.items():
                        errordict[form.prefix+"-"+field] = errorlist
        return errordict

    def save_m2m(self, commit=True):
        page = self.instance

        if page.slug and commit:
            other_slug_pages = pages.models.Page.objects.filter(slug=page.slug)
            if page.pk:
                other_slug_pages = other_slug_pages.exclude(pk=page.pk)
            try:
                other_slug_page = other_slug_pages.get()
                other_slug_page.slug = None
                other_slug_page.save()
            except pages.models.Page.DoesNotExist:
                pass

        for form in self.widget_forms:
            if not form.cleaned_data.get('delete', False):
                widget = form.save(commit)
                if not page.widgets_base.filter(id=widget.id).exists():
                    page.add_widget(widget, sort_order=form.cleaned_data['sort_order'])
                else:
                    p2w = page.page_to_widgets.get(widget=widget)
                    p2w.sort_order = form.cleaned_data['sort_order']
                    p2w.save()
            elif form.instance.pk:  # we need to delete an existing widget
                widget = form.instance
                p2w = page.page_to_widgets.get(widget=widget)
                p2w.delete()
                if not widget.page_to_widgets.exists():
                    # clean up orphans
                    widget.delete()

        return page