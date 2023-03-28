from django import forms
from django.core import validators
from django.db import models

from .models import ParticipationEvent



class ParticipationEventForm(forms.Form):
    def __init__(self, products,  *args, **kwargs):
        super(ParticipationEventForm, self).__init__(*args, **kwargs)
        for p in products:
            self.fields[p.pk] = forms.IntegerField(default=1, verbose_name="Quantité")




class BucqueEventForm(forms.Form):
    file = forms.FileField(validators=[validators.FileExtensionValidator(["xls"])])
