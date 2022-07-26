from django.contrib import admin
from .models import RechargeLydia

# Register your models here.

#@admin.register(RechargeLydia)
class AdminRechargeLydia(admin.ModelAdmin):
    list_display = ("cible_recharge", "date", "montant")