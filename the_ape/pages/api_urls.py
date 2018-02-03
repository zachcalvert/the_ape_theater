from django.conf.urls import url

import pages.views as views
import pages.admin_views as admin_views

urlpatterns = [
    url(r'^classes/(?P<class_id>\w+).json$', views.ApeClassView.as_view(), name='class'),
    url(r'^events/(?P<event_id>\w+).json$', views.EventView.as_view(), name='event'),
    url(r'^people/(?P<person_id>\w+).json$', views.PersonView.as_view(), name='person'),

    url(r'^(?P<page_id>\d+).json', views.PageView.as_view(), name="page"),
    url(r'^(?P<page_slug>[a-zA-Z]\w*).json$', views.PageView.as_view(), name="page"),

    url(r'^admin/generic_object_lookup/', admin_views.GenericObjectLookup.as_view(), name='generic_object_lookup'),
]