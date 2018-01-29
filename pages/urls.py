from django.conf import settings
from django.conf.urls import url

import pages.admin_views as admin_views
import pages.views as views


urlpatterns = [
    url(r'^event/(?P<event_id>\d+)', views.EventView.as_view(), name='event'),
    url(r'^class/(?P<ape_class_id>\d+)', views.ApeClassView.as_view(), name='ape_class'),
    url(r'^person/(?P<person_id>\d+)', views.PersonView.as_view(), name='person'),

    url(r'^(?P<page_slug>.+)/?$', views.SlugPageView.as_view(), name='slug_page'),
    url(r'^(?P<page_id>\d+)/$', views.PageView.as_view(), name="page"),

    url(r'^admin/generic_object_lookup/', admin_views.GenericObjectLookup.as_view(), name='generic_object_lookup'),
]