# -*- coding: utf-8 -*-

from django.contrib import admin
from django.contrib.auth.models import User
from .models import Utilisateur


# Register your models here.


class AdminUtilisateur(admin.ModelAdmin):
    list_display = (
        "username",
        "first_name",
        "last_name",
        "phone",
        "email",
        "chambre",
        "is_active",
        "is_gadz",
        "is_conscrit",
        "has_cotiz",
        "is_staff",
        "is_superuser",
    )


admin.site.register(Utilisateur, AdminUtilisateur)
admin.site.unregister(User)