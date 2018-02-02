from urllib.parse import urlsplit, SplitResult

from django.contrib.contenttypes.models import ContentType
from django.template import Node, Variable, Library
from django.core.urlresolvers import reverse
from django.utils.text import capfirst

register = Library()


@register.filter
def wrapped_url(api_url):
    if api_url:
        parsed = urlsplit(api_url)
        path = parsed.path.replace('.json', '').replace('api/','').replace('pages/','').strip('/')
        path = reverse("web_page_wrapper", args=[path])
        return SplitResult('', '', path, parsed.query, parsed.fragment).geturl()
    else:
        return api_url


@register.simple_tag(name="adminurl")
def admin_url(object, verb="change"):
    opts = object._meta
    return reverse("admin:{app}_{model}_{verb}".format(
        app=opts.app_label,
        model=opts.model_name,
        verb=verb
    ), args=[object.pk])


@register.simple_tag(takes_context=True, name="loopcomma")
def loop_comma(context):
    """
    Tag that outputs a comma, unless we're in the final iteration of a loop
    """
    if 'forloop' in context:
        if not context['forloop'].get('last', False):
            return ','
    return ''


@register.filter
def content_type_id(object):
    return ContentType.objects.get_for_model(object).id


@register.simple_tag
def verbose_name(obj, caps=True, plural=False):
    opts = obj._meta
    if plural:
        name = opts.verbose_name_plural
    else:
        name = opts.verbose_name
    if caps:
        name = capfirst(name)
    return name
