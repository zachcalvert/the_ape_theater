from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib import admin
from django.contrib.auth import views as auth_views

from ape_admin.views import ape_home

urlpatterns = [
    url(r'^login/$', auth_views.login, {'template_name': 'registration/login_modal.html'}, name='login'),
    url(r'^logout/$', auth_views.logout, name='logout'),
    url(r'^admin/', admin.site.urls),
    url(r'^grappelli/', include('grappelli.urls')),

    url(r'^classes/', include('classes.urls')),
    url(r'^', include('pages.urls')),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) \
  + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)