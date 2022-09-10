from django.contrib import admin
from appuser.models import Groupe

from .models import Consommateur, Produit, AuthorizedIP


@admin.register(Consommateur)
class AdminConsommateur(admin.ModelAdmin):
    search_fields = ["consommateur__username", "consommateur__first_name", "consommateur__last_name", "consommateur__bucque", "consommateur__fams", "consommateur__proms"]
    list_display = ("consommateur", "solde", "activated")


# @admin.register(Bucquage)
class AdminBucquage(admin.ModelAdmin):
    list_display = (
        "cible_bucquage",
        "date",
        "nom_produit",
        "prix_produit",
        "entite_produit",
        "initiateur_evenement",
    )


# @admin.register(Recharge)
class AdminRecharge(admin.ModelAdmin):
    list_display = ("cible_recharge", "date", "montant", "methode", "initiateur_evenement",)


@admin.register(Produit)
class AdminProduit(admin.ModelAdmin):
    search_fields = ["nom", "raccourci", "entite"]
    list_display = ("nom", "prix", "raccourci", "entite")

    # récupérer uniquement les groupes qui sont des entités, c'est à dire ceux qui ne commencent pas par un "_"
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "entite":
            qs = Groupe.objects.exclude(is_entity=False)
            if not request.user.is_superuser:
                qs = request.user.groups.exclude(groupe__is_entity=False)
            kwargs["queryset"] = qs
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    def has_change_permission(self, request, obj=None):
        if "appkfet.change_produit" not in request.user.get_all_permissions():
            return False
        if obj is not None and (
            request.user.groups.filter(name=obj.entite).exists()
            or request.user.is_superuser
        ):
            return True
        return False


# @admin.register(History)
class AdminHistory(admin.ModelAdmin):
    list_display = (
        "cible_evenement",
        "nom_evenement",
        "prix_evenement",
        "entite_evenement",
        "date_evenement",
        "initiateur_evenement",
    )


@admin.register(AuthorizedIP)
class AdminAuthorizedIP(admin.ModelAdmin):
    list_display = ("groupe", "ip", "description",)
