# -*- coding: utf-8 -*-

from django import forms
from captcha.fields import CaptchaField, CaptchaTextInput
from .models import Utilisateur


class loginform(forms.Form):
    user = forms.CharField(widget=forms.TextInput(attrs={"placeholder": "Login"}))
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Mot de passe"})
    )


class inscriptionform(forms.ModelForm):
    password_validation = forms.CharField(
        required=True,
        widget=forms.PasswordInput(
            attrs={"placeholder": "Confirmation du mot de passe"}
        ),
    )
    captcha = CaptchaField(
        required=True,
        widget=CaptchaTextInput(
            attrs={"placeholder": "Captcha"}
        ),
    )
    cgu =forms.BooleanField(
        required=True,
    )
    class Meta:
        model = Utilisateur
        fields = [
            "username",
            "first_name",
            "last_name",
            "chambre",
            "phone",
            "email",
            "password",
        ]
        widgets = {
            "username": forms.TextInput(attrs={"placeholder": "Username"}),
            "first_name": forms.TextInput(attrs={"placeholder": "Prénom"}),
            "last_name": forms.TextInput(attrs={"placeholder": "Nom de famille"}),
            "chambre": forms.TextInput(attrs={"placeholder": "Chambre"}),
            "phone": forms.TextInput(attrs={"placeholder": "Téléphone"}),
            "email": forms.TextInput(attrs={"placeholder": "Adresse email"}),
            "password": forms.PasswordInput(attrs={"placeholder": "Mot de passe"}),
        }

        def __init__(self, *args, **kwargs):
            super(inscriptionform, self).__init__(*args, **kwargs)
            self.field["username"].required = True
            self.field["first_name"].required = True
            self.field["last_name"].required = True
            self.field["chambre"].required = True
            self.field["phone"].required = True
            self.field["email"].required = True


class gestioncompteform(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ["chambre", "phone"]

        def __init__(self, *args, **kwargs):
            super(gestioncompteform, self).__init__(*args, **kwargs)
            self.field["chambre"].required = True
            self.field["phone"].required = True


class gestioncomptegadzform(forms.ModelForm):
    class Meta:
        model = Utilisateur
        fields = ["chambre", "phone", "bucque", "fams", "proms"]

        def __init__(self, *args, **kwargs):
            super(gestioncomptegadzform, self).__init__(*args, **kwargs)
            self.field["chambre"].required = True
            self.field["phone"].required = True
