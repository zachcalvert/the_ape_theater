from django.conf import settings
from django.conf.urls import url
from django.contrib.auth.decorators import login_required
from django.views.decorators.cache import cache_page

import pages.views as views

API_CACHE = getattr(settings, 'API_DISPLAY_CACHE_TIME', 60*5)

urlpatterns = [
    url(r'^$', login_required(views.SlugPageWrapperView.as_view(page_slug='home')), name='home'),

    url(r'^classes/(?P<class_id>\d+)', login_required(views.ApeClassWrapperView.as_view()), name='class_wrapper'),
    url(r'^events/(?P<event_id>\d+)', login_required(views.EventWrapperView.as_view()), name='event_wrapper'),
    url(r'^people/(?P<person_id>\d+)', login_required(views.PersonWrapperView.as_view()), name='person_wrapper'),

    url(r'^(?P<page_slug>.+)/?$', login_required(cache_page(API_CACHE)(views.SlugPageWrapperView.as_view())), name='slug_page_wrapper'),
    url(r'^(?P<page_path>.+)/?$', login_required(views.WebPageWrapperView.as_view()), name='web_page_wrapper'),
]
