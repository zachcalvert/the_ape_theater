from django.contrib import admin

from square_payments.models import SquarePayment


class SquarePaymentAdmin(admin.ModelAdmin):
    list_display = ['purchase', 'customer', 'amount', 'created', 'completed', 'error_message']
    fields = ['purchase', 'customer', 'amount', 'created', 'completed', 'error_message', 'uuid', 'nonce']
    readonly_fields = ['purchase', 'customer', 'amount', 'created', 'uuid', 'nonce', 'completed', 'error_message']

    def has_add_permission(self, request):
        return False


admin.site.register(SquarePayment, SquarePaymentAdmin)
