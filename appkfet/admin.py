from django.contrib import admin
from appuser.models import Groupe
from .forms import EntityForm

from .models import Consommateur, Produit, AuthorizedIP, Entity


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


@admin.register(Entity)
class AdminEntity(admin.ModelAdmin):
    form = EntityForm
    list_display = ("nom", "color")

@admin.register(AuthorizedIP)
class AdminAuthorizedIP(admin.ModelAdmin):
    list_display = ("groupe", "ip", "description",)
