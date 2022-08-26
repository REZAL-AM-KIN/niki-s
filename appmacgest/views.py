from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import render, redirect

from appmacgest.forms import DeviceForm
from appmacgest.models import Device
from appuser.models import Utilisateur
from appuser.views import has_cotiz, is_superuser

from mac_vendor_lookup import MacLookup


@login_required
@user_passes_test(has_cotiz)
def gestion_connexion(request):
    user = Utilisateur.objects.get(pk=request.user.pk)

    liste_mac = Device.objects.filter(Q(proprietaire=user) & Q(enable=True))
    empty_slot = user.max_devices - liste_mac.count()
    return render(request, "appmacgest/gestionconnexion.html", {"list": liste_mac, "empty_slot":empty_slot})



@login_required
@user_passes_test(has_cotiz)
def ajout_mac(request):
    user = Utilisateur.objects.get(pk=request.user.pk)
    nb_mac_used = Device.objects.filter(Q(proprietaire=request.user.pk) & Q(enable=True)).count()

    if nb_mac_used >= user.max_devices and not user.is_superuser:
        messages.error(request, f"Tu as dépassé la limite de {user.max_devices} appareils. Fais du trie !")
        return redirect(gestion_connexion)

    if request.method == "POST":
        form = DeviceForm(request.POST)
        if form.is_valid():
            form = form.save(commit=False)
            form.proprietaire = user
            if nb_mac_used == 0:
                form.accepted = True
                form.enable = True
                form.save()
                messages.success(request, "Adresse MAC ajoutée")
                return redirect(gestion_connexion)
            else:
                form.save()
                messages.warning(request, "Adresse MAC en attente d'approbation")
                return redirect(gestion_connexion)
        else:
            messages.error(request, "Une erreur est survenue")
            return redirect(gestion_connexion)
    else:
        form = DeviceForm()
    return render(request, "appmacgest/ajoutmac.html", {"form": form})


@login_required
@staff_member_required
@user_passes_test(is_superuser)
def gestion_demande_mac(request):
    liste_mac = Device.objects.filter(Q(accepted=False))
    for device in liste_mac:
        device.vendor = MacLookup().lookup(device.mac)

    return render(request, "appmacgest/gestiondemandemac.html", {"list": liste_mac})


@login_required
@staff_member_required
@user_passes_test(is_superuser)
def activate_device(request, params):
    device_to_modify = Device.objects.get(pk=params)
    device_to_modify.accepted = True
    device_to_modify.enable = True
    device_to_modify.save()
    messages.success(request, "Adresse MAC approuvée")
    return redirect(gestion_demande_mac)


@login_required
@staff_member_required
@user_passes_test(is_superuser)
def delete_device(request, params):
    device_to_delete = Device.objects.get(pk=params)
    device_to_delete.delete()
    messages.success(request, "Adresse MAC rejetée")
    return redirect(gestion_demande_mac)

@login_required
def disable_device(request, params):
    user = Utilisateur.objects.get(pk=request.user.pk)
    device_to_delete = Device.objects.get(pk=params)
    if device_to_delete.proprietaire != user:
        messages.success(request, "Vous ne pouvez pas supprimer un appareil qui ne vous appartient pas.")
        return redirect(gestion_connexion)
    device_to_delete.disable()
    messages.success(request, "Appareil supprimé avec succès.")
    return redirect(gestion_connexion)

def not_logged_in(request):
    return render(request, "appmacgest/notlogged.html")