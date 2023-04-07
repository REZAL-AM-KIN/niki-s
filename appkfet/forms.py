from django import forms

from appkfet.models import Entity


class EntityForm(forms.ModelForm):

    class Meta:
        model = Entity
        fields = "__all__"
        widgets = {
                'color': forms.widgets.TextInput(attrs={'type': 'color'}),
            }

