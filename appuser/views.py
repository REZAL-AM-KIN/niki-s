from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect

from appuser.forms import (
    InscriptionForm,
    GestionCompteGadzForm,
    GestionCompteForm,
)
from niki.settings import LOGIN_URL
from .models import Utilisateur


# Create your views here.
@login_required
def index(request):
    return render(request, "appuser/index.html")


def about(request):
    return render(request, "appuser/about.html")


def inscription(request):
    if request.method == "POST":
        form = InscriptionForm(request.POST)
        if form.is_valid():
            password1 = form.cleaned_data["password"]
            password2 = form.cleaned_data["password_validation"]
            if password1 and password2 and password1 != password2:
                messages.warning(
                    request, "Les mots de passe renseignés sont différents"
                )
                return redirect(inscription)
            user = form.save(commit=False)
            user.set_password(user.password)
            user.save()
            messages.success(request, "Création du compte réussie")
            # ajouter une commande pour envoyer un mail automatique pour signaler que l'inscription est réussie
            return redirect(LOGIN_URL)
        else:
            messages.error(
                request, "Une erreur est survenue lors de la création du compte"
            )
    else:
        form = InscriptionForm()
    return render(request, "inscription.html", {"form": form})


@login_required
def gestion_compte(request):
    user = Utilisateur.objects.get(pk=request.user.pk)
    if user.is_gadz:
        form_to_use = GestionCompteGadzForm
    else:
        form_to_use = GestionCompteForm
    if request.method == "POST":
        form = form_to_use(request.POST, instance=user)
        if form.is_valid():
            form.save()
            messages.success(request, "Modification(s) réussie(s)")
            return redirect(gestion_compte)
        else:
            messages.error(request, "Une erreur est survenue lors de la modification")
            return redirect(gestion_compte)
    else:
        form = form_to_use(instance=user)
    return render(request, "appuser/gestioncompte.html", {"form": form})


def has_cotiz(user):
    utilisateur = Utilisateur.objects.get(pk=user.pk)
    current_date = date.today()
    return current_date <= utilisateur.date_expiration


def is_superuser(user):
    return user.is_superuser


@login_required
@staff_member_required
def administration(request):
    return render(request, "appuser/administration.html")


def page_not_found_view(request, exception):
    return render(request, "404.html", status=404)
