# -*- coding: utf-8 -*-

from django import forms

from .models import Device


class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ["nom", "mac"]
