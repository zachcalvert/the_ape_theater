from django.contrib import admin

from square_payments.models import SquarePayment


class SquarePaymentAdmin(admin.ModelAdmin):
    list_display = ['purchase', 'customer', 'amount', 'created', 'completed', 'error_message']
    fields = ['purchase', 'customer', 'amount', 'created', 'completed', 'error_message', 'uuid', 'nonce']
    readonly_fields = ['purchase', 'customer', 'amount', 'created', 'uuid', 'nonce', 'completed', 'error_message']


admin.site.register(SquarePayment, SquarePaymentAdmin)
