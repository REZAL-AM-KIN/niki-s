from django.contrib import admin
from django.contrib import messages
from django.contrib.auth.models import Group
from .models import Consommateur, Produit
from django.db.models import Q

# Register your models here.


class AdminConsommateur(admin.ModelAdmin):
    list_display = ("consommateur", "solde", "activated")

class AdminBucquage(admin.ModelAdmin):
    list_display = ("cible_bucquage","date","nom_produit","prix_produit","entite_produit")


class AdminRecharge(admin.ModelAdmin):
    list_display = ("cible_recharge", "date", "montant", "methode")


class AdminProduit(admin.ModelAdmin):
    list_display = ("nom", "prix", "raccourci", "entite")

#récupérer uniquement les groupes qui sont des entités, c'est à dire ceux qui ne commencent pas par un "_"
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "entite":
            qs=Group.objects.exclude(name__startswith='_')
            if not request.user.is_superuser:
                qs=request.user.groups.exclude(name__startswith='_')
            kwargs["queryset"] = qs
        return super().formfield_for_foreignkey(db_field, request, **kwargs)
    
    def has_change_permission(self, request, obj=None):
        if "appkfet.change_produit" not in request.user.get_all_permissions():
            return False        
        if obj is not None and (request.user.groups.filter(name=obj.entite).exists() or request.user.is_superuser):
            return True
        return False

class AdminHistory(admin.ModelAdmin):
    list_display = ("cible_evenement","nom_evenement","prix_evenement","entite_evenement","date_evenement")

admin.site.register(Consommateur, AdminConsommateur)
#admin.site.register(Bucquage, AdminBucquage)
#admin.site.register(Recharge, AdminRecharge)
admin.site.register(Produit, AdminProduit)
#admin.site.register(History,AdminHistory)
