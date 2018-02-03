from django.conf import settings
from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

import pages.views as views

urlpatterns = [
    url(r'^$', login_required(views.SlugPageWrapperView.as_view(page_slug='home')), name='home'),

    url(r'^classes/(?P<ape_class_id>\d+)', views.ApeClassWrapperView.as_view(), name='ape_class_wrapper'),
    url(r'^events/(?P<event_id>\d+)', views.EventWrapperView.as_view(), name='event_wrapper'),
    url(r'^people/(?P<person_id>\d+)', views.PersonWrapperView.as_view(), name='person_wrapper'),

    url(r'^(?P<page_slug>.+)/?$', views.SlugPageWrapperView.as_view(), name='slug_page_wrapper'),
    url(r'^(?P<page_path>.+)/?$', views.WebPageWrapperView.as_view(), name='web_page_wrapper'),
]
