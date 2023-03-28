from django.contrib import admin

from appcom.models import Com_gadz


@admin.register(Com_gadz)
class AdminComGadz(admin.ModelAdmin):
    list_display = ["title"]