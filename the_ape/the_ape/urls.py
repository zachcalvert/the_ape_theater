from django.conf.urls import include, url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.views.generic import TemplateView
from registration.backends.simple.views import RegistrationView
from registration.forms import RegistrationFormUniqueEmail

from accounts.models import UserProfile
from pages.views import SlugPageWrapperView

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()


class ApeRegistrationView(RegistrationView):
    form_class = RegistrationFormUniqueEmail
    success_url = '/'
    # create a profile for the new user upon registration
    def register(self, form_class):
        import pdb
        pdb.set_trace()
        new_user = super(ApeRegistrationView, self).register(form_class)
        user_profile = UserProfile.objects.create(user=new_user)
        return user_profile


urlpatterns = [
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include('pages.api_urls')),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^accounts/register/$', ApeRegistrationView.as_view(form_class=RegistrationFormUniqueEmail), name="registration_register"),
    url(r'^accounts/', include('registration.backends.simple.urls')),
    url(r'^profile/', include('accounts.urls')),

    url(r'', include('pages.urls')),
]

# Uncomment the next line to serve media files in dev.
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# if settings.DEBUG:
#     import debug_toolbar
#     urlpatterns += patterns('',
#                             url(r'^__debug__/', include(debug_toolbar.urls)),
#                             )
