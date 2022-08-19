from django.contrib import admin
from django.contrib.auth.models import User, Group
from .models import Utilisateur, Groupe


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
