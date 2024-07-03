from django.contrib import admin
from django.db.models import Q

from .models import Event, ProductEvent, ParticipationEvent


@admin.action(description="Cloture les fin'ss sélectionnés")
def end(modeladmin, request, queryset):
    for finss in queryset:
        finss.end()

@admin.action(description="Passage en mode Prébucquage des fin'ss sélectionnés")
def prebucquage(modeladmin, request, queryset):
    for finss in queryset:
        finss.mode_prebucquage()

@admin.action(description="Passage en mode Bucquage des fin'ss sélectionnés")
def bucquage(modeladmin, request, queryset):
    for finss in queryset:
        finss.mode_bucquage()

@admin.action(description="Passage en mode Débucquage des fin'ss sélectionnés")
def debucquage(modeladmin, request, queryset):
    for finss in queryset:
        finss.mode_debucquage()

@admin.register(Event)
class AdminEvent(admin.ModelAdmin):
    list_display = ("titre", "date_event", "etat_event", "created_by")
    actions = [end, prebucquage, bucquage, debucquage]

    # Surcharge de la méthode de sauvegarde des objets Event (uniquement dans la Console d'admin) afin d'ajouter
    # l'utilisateur qui a créé l'évènement
    def save_model(self, request, obj, form, change):
        if change is False:
            obj.created_by = request.user
        obj.save()

    # Surcharge de la méthode qui fait la requête pour afficher le tableau de tous les Events. On affiche uniquement
    # les events dont je suis le créateur
    def get_queryset(self, request):
        qs = super(AdminEvent, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(Q(created_by=request.user))

    # Surcharge de la méthode permettant d'accéder à l'édition d'un objet Event. On autorise la modification uniquement
    # pour les events dont je suis le créateur
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if "appevents.change_event" not in request.user.get_all_permissions():
            return False
        if obj is not None and obj.created_by != request.user:
            return False
        return True

    # Surcharge de la méthode permettant d'accéder à la vue détaillée d'un objet Event. On autorise la vue uniquement
    # pour les events dont je suis le créateur
    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if "appevents.view_event" not in request.user.get_all_permissions():
            return False
        if obj is not None and obj.created_by != request.user:
            return False
        return True


@admin.register(ProductEvent)
class AdminProductEvent(admin.ModelAdmin):
    list_display = ("parent_event", "nom", "prix_min")

    # ajout d'un filtre sur la page de création/édition d'un product_event permettant d'afficher dans la dropdown
    # uniquement les events non terminés et que j'ai créé
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        if db_field.name == "parent_event":
            qs = Event.objects.filter(etat_event__lt=Event.EtatEventChoices.TERMINE)
            if not request.user.is_superuser:
                qs = qs.filter(created_by=request.user)
            kwargs["queryset"] = qs
        return super().formfield_for_foreignkey(db_field, request, **kwargs)

    # Surcharge de la méthode qui fait la requête pour afficher le tableau de tous les Product_Events. On affiche
    # uniquement les Product_Event appartenant aux events dont je suis le créateur
    def get_queryset(self, request):
        qs = super(AdminProductEvent, self).get_queryset(request)
        if request.user.is_superuser:
            return qs
        return qs.filter(parent_event__created_by=request.user)

    # Surcharge de la méthode permettant d'accéder à l'édition d'un objet Product_Event. On autorise la modification
    # uniquement pour les Product_events d'Event dont je suis le créateur
    def has_change_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if "appevents.change_product_event" not in request.user.get_all_permissions():
            return False
        if obj is not None and obj.parent_event.created_by != request.user:
            return False
        return True

    # Surcharge de la méthode permettant d'accéder à la vue détaillée d'un objet Product_Event. On autorise la vue
    # uniquement pour les Product_event appartenant à un events dont je suis le créateur
    def has_view_permission(self, request, obj=None):
        if request.user.is_superuser:
            return True
        if "appevents.view_product_event" not in request.user.get_all_permissions():
            return False
        if obj is not None and obj.parent_event.created_by != request.user:
            return False
        return True

@admin.register(ParticipationEvent)
class AdminParticipationEvents(admin.ModelAdmin):
    list_display = (
        "cible_participation",
        "product_participation",
        "prebucque_quantity",
        "quantity",
        "participation_bucquee",
        "participation_debucquee",
    )
