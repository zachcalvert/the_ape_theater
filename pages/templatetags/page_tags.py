from django.core.urlresolvers import reverse
from django.template import Library

register = Library()

@register.simple_tag(name="adminurl")
def admin_url(object, verb="change"):
    opts = object._meta
    return reverse("admin:{app}_{model}_{verb}".format(
        app=opts.app_label,
        model=opts.model_name,
        verb=verb
    ), args=[object.pk])