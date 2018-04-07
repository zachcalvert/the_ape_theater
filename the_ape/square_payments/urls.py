from django.conf import settings
from django.conf.urls import url

import square_payments.views as views

urlpatterns = [
    url(r'^process-card/$', views.process_card, name='process_card'),
    url(r'^reserve-seat/$', views.reserve_seat, name='reserve_seat'),
]
