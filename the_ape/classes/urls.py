from django.conf.urls import url

import pages

urlpatterns = [
    url(r'^(?P<ape_class_id>\d+)(?:/(?P<slug>[\w-]+))?/?$', pages.views.ApeClassWrapperView.as_view(), name='ape_class_wrapper'),
]
