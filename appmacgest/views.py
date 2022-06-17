# -*- coding: utf-8 -*-

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required, user_passes_test
from django.db.models import Q
from django.shortcuts import render, redirect

from appmacgest.forms import DeviceForm
from appmacgest.models import Device
from appuser.models import Utilisateur
from appuser.views import has_cotiz, is_superuser


# Create your views here.
@login_required
@user_passes_test(has_cotiz)
def gestionconnexion(request):
    user = Utilisateur.objects.get(pk=request.user.pk)
    listemac = Device.objects.filter(Q(proprietaire=user))
    return render(request, "appmacgest/gestionconnexion.html", {"list": listemac})


@login_required
@user_passes_test(has_cotiz)
def ajoutmac(request):
    if request.method == "POST":
        form = DeviceForm(request.POST)
        if form.is_valid():
            form = form.save(commit=False)
            user = Utilisateur.objects.get(pk=request.user.pk)
            form.proprietaire = user
            macused = Device.objects.filter(proprietaire=request.user.pk).count()
            if macused == 0:
                form.accepted = True
                form.has_rezal = True
                form.save()
                messages.success(request, "Adresse MAC ajoutée")
                return redirect(gestionconnexion)
            else:
                form.save()
                messages.warning(request, "Adresse MAC en attente d'approbation")
                return redirect(gestionconnexion)
        else:
            messages.error(request, "Une erreur est survenue")
            return redirect(gestionconnexion)
    else:
        form = DeviceForm()
    return render(request, "appmacgest/ajoutmac.html", {"form": form})


@login_required
@staff_member_required
@user_passes_test(is_superuser)
def gestiondemandemac(request):
    listemac = Device.objects.filter(Q(accepted=False))
    return render(request, "appmacgest/gestiondemandemac.html", {"list": listemac})


@login_required
@staff_member_required
@user_passes_test(is_superuser)
def activatedevice(request, params):
    device_to_modify = Device.objects.get(pk=params)
    device_to_modify.accepted = True
    device_to_modify.has_rezal = True
    device_to_modify.save()
    messages.success(request, "Adresse MAC approuvée")
    return redirect(gestiondemandemac)


@login_required
@staff_member_required
@user_passes_test(is_superuser)
def deletedevice(request, params):
    device_to_delete = Device.objects.get(pk=params)
    device_to_delete.delete()
    messages.success(request, "Adresse MAC rejetée")
    return redirect(gestiondemandemac)
