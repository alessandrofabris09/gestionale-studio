from django import forms

from .models import Scadenza


class ScadenzaForm(forms.ModelForm):

    class Meta:
        model = Scadenza

        exclude = [
            'completata',
        ]

        widgets = {
            'data_scadenza': forms.DateInput(attrs={'type': 'date'}),
            'descrizione': forms.Textarea(attrs={'rows': 4}),
        }