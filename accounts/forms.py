
from django import forms
from django.contrib.auth.models import User
from django.contrib.auth import password_validation
from django.forms.formsets import formset_factory
from django.urls import reverse
from django.utils.functional import lazy
from django.utils.safestring import mark_safe, SafeText
from django.utils.translation import ugettext as _, ugettext_lazy as _lazy

from .models import (
    UserProfile
)
from .templatetags.account_tags import perm_with_tooltip
from common.constants import LOCAL_STORE_VALUE
from common.forms import C2Form, C2ModelForm, get_add_params_formfield
from common.widgets import (
    ButtonGroup, CheckboxSelectMultipleTable, SelectizeSelect,
    SelectizeMultiple)
from infrastructure.models import CustomField, Preconfiguration
from utilities.models import GlobalPreferences


class UserProfileForm(C2ModelForm):
    """
    Form is used for creating new users as well as editing existing users.
    """
    class Meta(object):
        model = User
        fields = (
            'id', 'email', 'username', 'first_name', 'last_name', 'password', 'password2',
            'is_active', 'super_admin', 'ape_admin',
        )

    error_css_class = 'error'
    required_css_class = 'required'

    id = forms.CharField(widget=forms.HiddenInput(), required=False)
    email = forms.EmailField(
        label=_lazy('Email'),
        widget=forms.TextInput(attrs={
            'class': 'email',
            'autocomplete': 'off'
        }))
    first_name = forms.CharField(label=_lazy("First Name"))
    last_name = forms.CharField(label=_lazy("Last Name"))
    username = forms.CharField(
        label=_lazy("Username"),
        widget=forms.TextInput(attrs={
            'autocomplete': 'off'
        }))
    password = forms.CharField(
        required=False,  # Only required when creating a local account
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'off'
        }))
    password2 = forms.CharField(
        required=False,  # Only required when password has a value
        label=_lazy('Confirm password'),
        widget=forms.PasswordInput(attrs={
            'autocomplete': 'off'
        }))

    super_admin = forms.BooleanField(label=lazy(perm_with_tooltip, SafeText)('super_admin'),
                                     required=False)

    ape_admin = forms.BooleanField(label=lazy(perm_with_tooltip, SafeText)('devops_admin'),
                                      required=False)

    def __init__(self, *args, **kwargs):
        # Enable the privileged/superuser fields?  The "requestor" here is the
        # user making the change, not necessarily the user account being edited
        request = kwargs.pop('request', None)
        # userprofile.is_cbadmin will be true if they are a CB Admin or a Super
        # Admin
        self.enable_ape_admin_fields = (request and request.get_user_profile().is_ape_admin)

        super(UserProfileForm, self).__init__(*args, **kwargs)

        if 'instance' in kwargs:
            profile = self.instance.userprofile
            self.editing = True
            self.fields['password'].required = False
            self.fields['password'].label = _("Change password (optional)")
            self.fields['password2'].required = False
            self.fields['super_admin'].initial = \
                profile.super_admin
            self.fields['ape_admin'].initial = \
                profile.ape_admin

            if profile.ldap:
                # Can't edit some details for users imported from LDAP
                del self.fields['password']
                del self.fields['password2']
                del self.fields['email']
                del self.fields['username']
                del self.fields['first_name']
                del self.fields['last_name']

        else:
            self.editing = False

        # Only enable the privileged fields if the requestor is a superuser
        if (not self.enable_cbadmin_fields):
            for field in ['is_active', 'is_superuser', 'super_admin', 'devops_admin']:
                self.fields[field].widget.attrs['disabled'] = True

        # Hide the built-in prompts on these fields, mostly for consistency
        # with the other fields on this form.  This is completely cosmetic
        for field in ['is_active', 'is_superuser']:
            self.fields[field].help_text = ""

    def get_onready_js(self, creating=True):
        req_passwords = ''

        if creating:
            req_passwords = """
            // For consistency, show fields as required
            var $label;
            $label = $('#id_password').closest('.form-group').find('label');
            $label.addClass('requiredField').html($label.html().trim() + '*');
            $label = $('#id_password2').closest('.form-group').find('label');
            $label.addClass('requiredField').html($label.html().trim() + '*');
            """

        return req_passwords + """
            var $domain = $('#id_domain');

            function update_form_for_domain() {
                var val = $domain.val();
                if (val == 'CB_LOCAL_USER_STORAGE') {
                    $('#id_password').closest('.form-group').show();
                    $('#id_password2').closest('.form-group').show();
                } else {
                    $('#id_password').closest('.form-group').hide();
                    $('#id_password2').closest('.form-group').hide();
                }
            }

            $domain.on('change', update_form_for_domain);

            update_form_for_domain();
        """

    def clean(self):
        super(UserProfileForm, self).clean()

        if 'domain' not in self.fields:
            # Editing: Password fields are not required when an LDAP domain has
            # been selected (thus the domain field was removed)
            return self.cleaned_data

        if 'domain' in self.fields and self.cleaned_data.get('domain') != LOCAL_STORE_VALUE:
            # Creating: Password fields are not required if domain is LDAP
            return self.cleaned_data

        password = self.cleaned_data.get('password')
        if self.editing is False and not password:
            raise forms.ValidationError(_("Password is required for 'Local' authentication."))

        if password and password != self.cleaned_data.get('password2'):
            raise forms.ValidationError(_("Passwords do not match."))

        password_validation.validate_password(password)

        return self.cleaned_data

    def clean_email(self):
        email = self.cleaned_data['email']
        found = User.objects.filter(email__iexact=email)

        # It's okay if the email did not change if editing:
        if self.editing:
            this_user = User.objects.get(id=self.instance.id)
            if this_user.email == email:
                return email

        if found.count():
            other_user = found[0]
            error_msg = _("A user with that email exists already. <a href='{url}'>"
                          "View profile</a>").format(url=reverse('user_detail', args=[other_user.id]))
            raise forms.ValidationError(mark_safe(error_msg))
        return email

    def save(self):
        if self.editing:
            user = User.objects.get(id=self.instance.id)  # cleaned_data('id'))
            profile = self.instance.userprofile
        else:
            user = User()

        if not self.editing or not profile.ldap:
            if self.cleaned_data.get('password'):
                user.set_password(self.cleaned_data.get('password'))
            user.username = self.cleaned_data['username']
            user.email = self.cleaned_data['email']
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']

        # Only change the privileged fields if the requestor is a CB admin
        if (self.enable_cbadmin_fields):
            user.is_active = self.cleaned_data['is_active']
            user.is_staff = self.cleaned_data['is_superuser']  # Merge these
            user.is_superuser = self.cleaned_data['is_superuser']

        user.save()

        # Update the associated profile, if necessary; the profile only exists
        # after the user is created
        profile = user.userprofile
        if (self.enable_cbadmin_fields):
            profile.super_admin = self.cleaned_data['super_admin']
            profile.devops_admin = self.cleaned_data['devops_admin']
            profile.save()
        domain = self.cleaned_data.get('domain', None)
        if domain:
            from utilities.models import LDAPUtility
            ldap = LDAPUtility.objects.filter(ldap_domain=domain).first()
            profile.ldap = ldap
            profile.save()

        return user