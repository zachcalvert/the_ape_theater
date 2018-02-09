from django import forms


class ApeClassRegistrationForm(forms.Form):
    pay_now = forms.BooleanField(required=False)

    def clean(self):
        cleaned_data = super(ApeClassRegistrationForm, self).clean()
        pay_now = cleaned_data.get("pay_now")