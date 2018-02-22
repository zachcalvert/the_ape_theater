from django.contrib import admin

from accounts.models import UserProfile
from square_payments.models import SquarePayment


class PaymentInline(admin.TabularInline):
    model = SquarePayment
    fields = ['amount', 'created', 'completed']
    readonly_fields = ['amount', 'created', 'completed']
    extra = 0


class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user']
    fields = ['user']
    inlines = [
        PaymentInline,
    ]

admin.site.register(UserProfile, UserProfileAdmin)