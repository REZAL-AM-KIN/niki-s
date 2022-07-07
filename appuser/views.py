# -*- coding: utf-8 -*-

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from appuser.forms import (
    inscriptionform,
    gestioncomptegadzform,
    gestioncompteform,
)
from .models import Utilisateur


# Create your views here.
@login_required
def index(request):
    return render(request, "appuser/index.html")


def about(request):
    return render(request, "appuser/about.html")


def inscription(request):
    if request.method == "POST":
        form = inscriptionform(request.POST)
        if form.is_valid():
            password1 = form.cleaned_data["password"]
            password2 = form.cleaned_data["password_validation"]
            if password1 and password2 and password1 != password2:
                messages.warning(
                    request, u"Les mots de passe renseignés sont différents"
                )
                return redirect(inscription)
            user = form.save(commit=False)
            user.set_password(user.password)
            user.save()
            messages.success(request, u"Création du compte réussie")
            # ajouter une commande pour envoyer un mail automatique pour signaler que l'inscription est réussie
            return redirect(loginview)
        else:
            messages.error(
                request, u"Une erreur est survenue lors de la création du compte"
            )
    else:
        form = inscriptionform()
    return render(request, "inscription.html", {"form": form})


@login_required
def gestioncompte(request):
    user = Utilisateur.objects.get(pk=request.user.pk)
    if user.is_gadz:
        form_to_use = gestioncomptegadzform
    else:
        form_to_use = gestioncompteform
    if request.method == "POST":
        form = form_to_use(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, u"Modification(s) réussie(s)")
            return redirect(gestioncompte)
        else:
            messages.error(request, u"Une erreur est survenue lors de la modification")
            return redirect(gestioncompte)
    else:
        form = form_to_use(instance=user)
    return render(request, "appuser/gestioncompte.html", {"form": form})


def has_cotiz(user):
    test = False
    user = Utilisateur.objects.get(pk=user.pk)
    if user.has_cotiz:
        test = True
    return test

def is_superuser(user):
    test=False
    if user.is_superuser:
        test=True
    return test

@login_required
@staff_member_required
def administration(request):
    return render(request, "appuser/administration.html")

def page_not_found_view(request, exception):
    return render(request, "404.html", status=404)