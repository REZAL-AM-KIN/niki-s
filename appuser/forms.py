from captcha.fields import CaptchaField, CaptchaTextInput
from django import forms
from django.contrib.auth.forms import PasswordResetForm, AuthenticationForm

from .models import Utilisateur, Groupe


class CustomLoginForm(AuthenticationForm):
    username = forms.CharField(
        widget=forms.TextInput(attrs={"class": "validate", "placeholder": "Username"})
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "Mot de passe"})
    )


class InscriptionForm(forms.ModelForm):
    password_validation = forms.CharField(
        required=True,
        widget=forms.PasswordInput(
            attrs={"placeholder": "Confirmation du mot de passe"}
        ),
    )
    captcha = CaptchaField(
        required=True,
        widget=CaptchaTextInput(attrs={"placeholder": "Captcha"}),
    )
    cgu = forms.BooleanField(
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super(InscriptionForm, self).__init__(*args, **kwargs)
        self.fields["username"].required = True
        self.fields["first_name"].required = True
        self.fields["last_name"].required = True
        self.fields["chambre"].required = True
        self.fields["phone"].required = True
        self.fields["email"].required = True

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


class GestionCompteForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(GestionCompteForm, self).__init__(*args, **kwargs)
        self.fields["chambre"].required = True
        self.fields["phone"].required = True

    class Meta:
        model = Utilisateur
        fields = ["chambre", "phone"]


class GestionCompteGadzForm(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super(GestionCompteGadzForm, self).__init__(*args, **kwargs)
        self.fields["chambre"].required = True
        self.fields["phone"].required = True

    class Meta:
        model = Utilisateur
        fields = ["chambre", "phone", "bucque", "fams", "proms"]


class CustomPasswordResetForm(PasswordResetForm):
    email = forms.EmailField(
        required=True, widget=forms.EmailInput(attrs={"placeholder": "Adresse email"})
    )
    captcha = CaptchaField(
        required=True, widget=CaptchaTextInput(attrs={"placeholder": "Captcha"})
    )


class GroupeForm(forms.ModelForm):

    class Meta:
        model = Groupe
        fields = "__all__"
        widgets = {
                'color': forms.widgets.TextInput(attrs={'type': 'color'}),
            }
