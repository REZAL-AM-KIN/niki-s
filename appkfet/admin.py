from django.contrib import admin
from django.contrib import messages

from .models import Consommateur, Bucquage, Recharge, Produit, History


# Register your models here.


class AdminConsommateur(admin.ModelAdmin):
    list_display = ("consommateur", "solde", "activated")

class AdminBucquage(admin.ModelAdmin):
    list_display = ("cible_bucquage","date","nom_produit","prix_produit","entite_produit")


class AdminRecharge(admin.ModelAdmin):
    list_display = ("cible_recharge", "date", "montant", "methode")


class AdminProduit(admin.ModelAdmin):
    list_display = ("nom", "prix", "raccourci", "entite")

    def message_user(self, *args):
        pass
    
    def has_change_permission(self, request, obj=None):
        if "appkfet.change_produit" not in request.user.get_all_permissions():
            return False        
        if obj is not None and (request.user.groups.filter(name=obj.entite).exists() or request.user.is_superuser):
            return True
        return False

    def save_model(self, request, obj, form, change):
        if request.user.groups.filter(name=obj.entite).exists() or request.user.is_superuser:
            messages.success(request, "The product has been created or updated")
            obj.save()
        else:
            messages.error(request, "You cannot manage product for this entity")
            return None

class AdminHistory(admin.ModelAdmin):
    list_display = ("cible_evenement","nom_evenement","prix_evenement","entite_evenement","date_evenement")

admin.site.register(Consommateur, AdminConsommateur)
#admin.site.register(Bucquage, AdminBucquage)
#admin.site.register(Recharge, AdminRecharge)
admin.site.register(Produit, AdminProduit)
#admin.site.register(History,AdminHistory)
