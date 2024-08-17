from captcha.fields import CaptchaField, CaptchaTextInput
from django import forms
from django.contrib.auth.forms import PasswordResetForm, AuthenticationForm, SetPasswordForm, PasswordChangeForm

from .models import Utilisateur


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


class CustomSetPasswordForm(SetPasswordForm):
    """
    Surcharge du form fournis par la bibliothèque Django pour utiliser l'objet Utilisateur plutôt que User
    """
    def save(self, commit=True):
        user = Utilisateur.objects.get(pk=self.user.pk)
        # on met à jour le mot de passe de l'objet Utilisateur et de l'objet user parce que sinon la mise à jour de la
        # session ne marche pas correctement et l'utilisateur est déconnecté
        password = self.cleaned_data["new_password1"]
        user.set_password(password)
        self.user.set_password(password)
        if commit:
            user.save()
            self.user.save()
        return self.user


class CustomPasswordChangeForm(CustomSetPasswordForm, PasswordChangeForm):
    """
    Redéfinition de PasswordChangeForm avec la class surchargée définit précedement
    """
    pass
