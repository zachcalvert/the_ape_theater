from django.conf.urls import include, url
from django.contrib.auth import views as auth_views

from accounts.views import UserProfileView

urlpatterns = [
    url(r'^login/$', auth_views.login, {'template_name': 'accounts/login.html'}, name='login'),
    url(r'^logout/$', auth_views.logout, name='logout', kwargs={'next_page': '/'}),

    url(r'^', UserProfileView.as_view(), name='user_profile'),
]
