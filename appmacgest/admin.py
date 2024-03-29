from django.contrib import admin

from .models import Device


# Add action to disable device
@admin.action(description="Désactiver les appareils sélectionnés")
def disable(modeladmin, request, queryset):
    for line in queryset:
        line.disable()


@admin.register(Device)
class AdminDevice(admin.ModelAdmin):
    list_display = ("proprietaire", "nom", "mac", "accepted", "enable")
    search_fields = ["proprietaire__username", "proprietaire__phone", "proprietaire__first_name", "proprietaire__last_name", "mac"]
    actions = [disable]

    def has_delete_permission(self, request, obj=None):
        # Disable delete button and delete action for everyone
        return False
