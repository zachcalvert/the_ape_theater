from django import forms


class EventTicketPurchaseForm(forms.Form):
    num_tickets = forms.IntegerField(required=True, label="Number of tickets")
    terms_and_conditions = forms.BooleanField(required=True)

    def clean(self):
        cleaned_data = super(EventTicketPurchaseForm, self).clean()
        num_tickets = cleaned_data.get("num_tickets")
        terms_and_conditions = cleaned_data.get("terms_and_conditions")
