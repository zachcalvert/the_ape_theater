from django.conf import settings
from django.conf.urls import url

import events.views as views
import pages

urlpatterns = [
    url(r'^(?P<event_id>\d+)(?:/(?P<slug>[\w-]+))?/?$', pages.views.EventWrapperView.as_view(), name='event_wrapper'),
]
