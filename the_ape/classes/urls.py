from django.conf import settings
from django.conf.urls import url
from django.views.decorators.cache import cache_page

import classes.views as views
import pages

urlpatterns = [
    url(r'^(?P<ape_class_id>\d+)(?:/(?P<slug>[\w-]+))?/?$', pages.views.ApeClassWrapperView.as_view(), name='ape_class_wrapper'),
]
