# -*- coding: utf-8 -*-

from django import forms

from .models import Participation_event

class ParticipationEventForm(forms.ModelForm):
    class Meta:
        model = Participation_event
        fields = ["number"]

class BucqueEventForm(forms.Form):
    file=forms.FileField(attrs={'enctype':"multipart/form-data"})