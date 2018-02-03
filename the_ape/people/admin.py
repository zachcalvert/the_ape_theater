from django.contrib import admin

from people.models import Person, HouseTeam


class PersonAdmin(admin.ModelAdmin):
    search_fields = ['first_name', 'last_name']
    list_display = ['name', 'teaches', 'performs', 'house_team', 'headshot']
    list_filter = ['teaches', 'performs']


admin.site.register(Person, PersonAdmin)
admin.site.register(HouseTeam)
