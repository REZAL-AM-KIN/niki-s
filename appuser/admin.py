from django.contrib import admin
from django.contrib.auth.models import User, Group
from .models import Utilisateur, Groupe

from datetime import date


class AdminUtilisateur(admin.ModelAdmin):
    def has_cotiz(adminUser, user):
        current_date = date.today()
        return current_date <= user.date_expiration

    # to display the tick and not "True"
    has_cotiz.boolean = True

    list_display = (
        "username",
        "first_name",
        "last_name",
        "phone",
        "email",
        "chambre",
        "is_active",
        "has_cotiz",
        "is_gadz",
        "is_conscrit",
        "is_staff",
        "is_superuser",
    )


class AdminGroupe(admin.ModelAdmin):
    list_display = (
        "name",
        "is_entity",
    )


admin.site.register(Utilisateur, AdminUtilisateur)
admin.site.register(Groupe, AdminGroupe)
admin.site.unregister(User)
admin.site.unregister(Group)
