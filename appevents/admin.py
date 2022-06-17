from django.contrib import admin
from django.contrib import messages

# Register your models here.
from .models import Event, Participation_event, Product_event

class AdminEvent(admin.ModelAdmin):
    list_display = ("titre","date_event", "cansubscribe", "created_by")

#Surcharge de la méthode de sauvegarde des objets Event (uniquement dans la Console d'admin) afin d'ajouter l'utilisateur qui a créé l'évènement
    def save_model(self, request, obj, form, change):
        if change==False: 
            obj.created_by = request.user
        obj.save()

#Surcharge de la méthode qui fait la requête pour afficher le tableau de tous les Events. On affiche uniquement les events dont je suis le créateur
    def get_queryset(self, request):
        qs = super(AdminEvent, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(created_by=request.user)

#Surcharge de la méthode permettant d'accéder à l'édition d'un objet Event. On autorise la modification uniquement pour les events dont je suis le créateur
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if "appevents.change_event" not in request.user.get_all_permissions():
            return False
        if obj is not None and obj.created_by != request.user:
            return False
        return True

#Surcharge de la méthode permettant d'accéder à la vue détaillée d'un objet Event. On autorise la vue uniquement pour les events dont je suis le créateur
    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if "appevents.view_event" not in request.user.get_all_permissions():
            return False
        if obj is not None and obj.created_by != request.user:
            return False
        return True

class AdminProductEvent(admin.ModelAdmin):
    list_display = ("parent_event", "nom", "prix")

    def message_user(self, *args):
        pass
    
#Surcharge de la méthode de sauvegarde des objets Product_Event (uniquement dans la Console d'admin) afin de ne pouvoir ajouter un produit que sur un évènement que j'ai créé
#Obligation de redéfinir la méthode message_user ci-dessus pour ne pas afficher le message de création par défaut
    def save_model(self, request, obj, form, change):
        if not request.user.is_superuser:
            if obj.parent_event.created_by != request.user:
                messages.error(request, "You cannot create a product for this event")
                return None
        messages.success(request, "The product has been created")
        obj.save()

#Surcharge de la méthode qui fait la requête pour afficher le tableau de tous les Product_Events. On affiche uniquement les Product_Event appartenant aux events dont je suis le créateur
    def get_queryset(self, request):
        qs = super(AdminProductEvent, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(parent_event__created_by=request.user)

#Surcharge de la méthode permettant d'accéder à l'édition d'un objet Product_Event. On autorise la modification uniquement pour les Product_events d'Event dont je suis le créateur
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if "appevents.change_product_event" not in request.user.get_all_permissions():
            return False
        if obj is not None and obj.parent_event.created_by != request.user:
            return False
        return True

#Surcharge de la méthode permettant d'accéder à la vue détaillée d'un objet Product_Event. On autorise la vue uniquement pour les Product_event appartenant à un events dont je suis le créateur
    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if "appevents.view_product_event" not in request.user.get_all_permissions():
            return False
        if obj is not None and obj.parent_event.created_by != request.user:
            return False
        return True

class AdminParticipationEvents(admin.ModelAdmin):
    list_display = ("cible_participation", "product_participation", "number", "participation_ok")

admin.site.register(Event, AdminEvent)
admin.site.register(Product_event, AdminProductEvent)
admin.site.register(Participation_event, AdminParticipationEvents)