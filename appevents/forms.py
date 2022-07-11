from django import forms
from django.core import validators

from .models import ParticipationEvent


class ParticipationEventForm(forms.ModelForm):
    class Meta:
        model = ParticipationEvent
        fields = ["number"]


class BucqueEventForm(forms.Form):
    file = forms.FileField(validators=[validators.FileExtensionValidator(["xls"])])
