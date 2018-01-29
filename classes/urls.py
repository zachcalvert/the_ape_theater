from django.conf.urls import url

from classes import views

urlpatterns = [
    url(r'^$', views.class_list, name='class_list'),
    url(r'^(?P<class_id>\d+)/$', views.class_detail, name='class_detail'),
    url(r'^(?P<class_id>\d+)/(?P<session_id>\d+)/$', views.session_detail, name='session_detail'),
]
