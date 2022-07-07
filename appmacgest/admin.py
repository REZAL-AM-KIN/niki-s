from django.contrib import admin

from .models import Device


# Register your models here.


class AdminDevice(admin.ModelAdmin):
    list_display = ("proprietaire", "nom", "mac", "accepted", "has_rezal")
    search_fields=['proprietaire__username', 'proprietaire__phone', 'mac']


admin.site.register(Device, AdminDevice)
