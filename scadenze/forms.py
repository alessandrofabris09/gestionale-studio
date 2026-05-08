from django import forms
from .models import Scadenza


class ScadenzaForm(forms.ModelForm):
    class Meta:
        model = Scadenza
        fields = [
            'pratica',
            'titolo',
            'descrizione',
            'data_scadenza',
            'priorita',
            'completata',
        ]

        widgets = {
            'data_scadenza': forms.DateInput(attrs={'type': 'date'}),
            'descrizione': forms.Textarea(attrs={'rows': 3}),
        }