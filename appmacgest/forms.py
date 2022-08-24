from django import forms

from .models import Device


class DeviceForm(forms.ModelForm):
    class Meta:
        model = Device
        fields = ["nom", "mac"]

    def clean_mac(self):
        mac = self.cleaned_data['mac']
        return mac.lower()
