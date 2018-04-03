from django.conf.urls import url

import pages

urlpatterns = [
    url(r'^(?P<event_id>\d+)(?:/(?P<slug>[\w-]+))?/?$', pages.views.EventWrapperView.as_view(), name='event_wrapper'),
]
