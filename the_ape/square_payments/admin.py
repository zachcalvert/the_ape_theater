from django.contrib import admin

from square_payments.models import SquareCustomer, SquarePayment


class PaymentInline(admin.TabularInline):
	model = SquarePayment
	fields = ['amount', 'created', 'completed']
	readonly_fields = ['amount', 'created', 'completed']
	extra = 0


class SquareCustomerAdmin(admin.ModelAdmin):
	readonly_fields = ['first_name', 'last_name', 'email', 'profile']
	inlines = [
        PaymentInline,
    ]


class SquarePaymentAdmin(admin.ModelAdmin):
	list_display = ['customer', 'amount', 'created', 'completed', 'error_message']
	readonly_fields = ['customer', 'uuid', 'amount', 'currency', 'nonce', 'completed', 'error_message']


admin.site.register(SquareCustomer, SquareCustomerAdmin)
admin.site.register(SquarePayment, SquarePaymentAdmin)
