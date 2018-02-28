import re
from urllib.parse import urlsplit, SplitResult

from django.contrib.auth.models import User
from django.contrib.contenttypes.models import ContentType
from django.template import Node, Variable, Library
from django.core.urlresolvers import reverse
from django.utils.safestring import mark_safe
from django.utils.text import capfirst

from accounts.models import UserProfile, EventAttendee, Ticket, ClassMember
from classes.models import ApeClass
from events.models import Event
from people.models import Person, HouseTeam

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


@register.filter
def json_safe(string):
    """
    Takes a json formatted string, and formats if for display in html
    """
    return mark_safe(string.replace(r"\n", "\n").replace(r"\r", "\r"))


# if no redirect is needed, return False; otherwise, return correct path with slug
def get_slug_redirect(path):
    slug_needing_pattern = re.match('^/(?P<type>classes|events|people|house_teams)/(?P<id>\w+)', path)

    # don't bother adding slug to see_all, or if the url is not displaying books, series, or contributors
    if not slug_needing_pattern:
        return False

    item_type = slug_needing_pattern.group('type')
    item_id = slug_needing_pattern.group('id')

    if item_type == 'classes':
        item = ApeClass.objects.get(id=item_id)
    elif item_type == 'events':
        item = Event.objects.get(id=item_id)
    elif item_type == 'people':
        item = Person.objects.get(id=item_id)
    else:
        item = HouseTeam.objects.get(id=item_id)

    if item_type == 'pages':
        slug = item.link_slug
    else:
        slug = item.slug

    end_slug = re.match('^/(classes|events|people|house_teams)/\w+/(?P<page_slug>[\w|\-]+)', path)
    if end_slug and end_slug.group('page_slug') == slug:
        # if current slug is correct there is no need to redirect
        return False

    return '/{}/{}/{}'.format(item_type, item_id, slug)


@register.filter
def is_registered(user_id, ape_class_id):
    profile = User.objects.get(id=user_id).profile
    ape_class = ApeClass.objects.get(id=ape_class_id)
    if ClassMember.objects.filter(student=profile, ape_class=ape_class).exists():
        return True
    return False


@register.filter
def ticket_link(event_id, profile_id):
    event = Event.objects.get(id=event_id)
    profile = UserProfile.objects.get(id=profile_id)
    try:
        ticket = EventAttendee.objects.filter(event=event, attendee=profile).first().ticket
    except AttributeError:
        return ''
    return ticket.get_absolute_url()


@register.filter
def class_registration_link(ape_class_id, profile_id):
    ape_class = ApeClass.objects.get(id=ape_class_id)
    profile = UserProfile.objects.get(id=profile_id)
    try:
        registration = ClassMember.objects.filter(ape_class=ape_class, student=profile).first().registration
    except AttributeError:
        return ''
    return registration.get_absolute_url()
