from django.contrib import admin

from .models import Device


# Register your models here.


class AdminDevice(admin.ModelAdmin):
    list_display = ("proprietaire", "nom", "mac", "accepted", "has_rezal")


#admin.site.register(Device, AdminDevice)
