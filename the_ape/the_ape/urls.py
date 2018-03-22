from importlib import import_module

from django import forms
from django.apps import apps
from django.conf.urls import include, url
from django.conf.urls.static import static
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.sitemaps.views import sitemap
from django.core.exceptions import ValidationError
from django.views.generic import TemplateView

from registration.backends.simple.views import RegistrationView
from registration.forms import RegistrationFormUniqueEmail

from accounts.models import UserProfile
from pages.views import SlugPageWrapperView
from accounts.views import TicketView, ClassRegistrationView

from django.contrib import admin
admin.autodiscover()


# autodiscover sitemaps
sitemaps = {}
for app_config in apps.get_app_configs():
    try:
        module = import_module("{}.sitemap".format(app_config.name))
        sitemaps.update(module.sitemaps)
    except (ImportError, AttributeError):
        pass


class ApeRegistrationForm(forms.Form):
    first_name = forms.CharField(max_length=40)
    last_name = forms.CharField(max_length=40)
    email = forms.EmailField()
    password1 = forms.CharField(max_length=40, widget=forms.PasswordInput)
    password2 = forms.CharField(max_length=40, widget=forms.PasswordInput)

    def clean(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError('A user with that email already exists. Do you need to login perhaps?')
        password1 = self.cleaned_data['password1']
        password2 = self.cleaned_data['password2']
        if password1 != password2:
            raise ValidationError('The provided passwords do not match.')

    def save(self, *args, **kwargs):
        first_name = self.cleaned_data.get('first_name')
        last_name = self.cleaned_data.get('last_name')
        email = self.cleaned_data.get('email')
        password = self.cleaned_data.get('password1')
        return User.objects.create_user(username=email,
                                        email=email,
                                        password=password,
                                        first_name=first_name,
                                        last_name=last_name)


class ApeRegistrationView(RegistrationView):
    success_url = '/'
    # create a profile for the new user upon registration
    def register(self, form_class):
        new_user = super(ApeRegistrationView, self).register(form_class)
        user_profile = UserProfile.objects.create(user=new_user)
        return user_profile


urlpatterns = [
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api/', include('pages.api_urls')),
    url(r'^grappelli/', include('grappelli.urls')),
    url(r'^accounts/register/$', ApeRegistrationView.as_view(form_class=ApeRegistrationForm), name="registration_register"),
    url(r'^accounts/', include('registration.backends.simple.urls')),
    url(r'^profile/', include('accounts.urls')),
    url(r'^square/', include('square_payments.urls')),
    url(r'^ticket/(?P<ticket_uuid>\w+)', TicketView.as_view(), name='ticket'),
    url(r'^class_registration/(?P<registration_uuid>\w+)', ClassRegistrationView.as_view(), name='class_registration'),
    url(r'^robots\.txt', include('robots.urls')),
    url(r'^sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),

    url(r'', include('pages.urls')),
]

# Uncomment the next line to serve media files in dev.
# urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# if settings.DEBUG:
#     import debug_toolbar
#     urlpatterns += patterns('',
#                             url(r'^__debug__/', include(debug_toolbar.urls)),
#                             )
