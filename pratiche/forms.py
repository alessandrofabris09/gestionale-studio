from django import forms
from .models import Pratica


class PraticaForm(forms.ModelForm):
    class Meta:
        model = Pratica
        fields = [
            'cliente',
            'immobile',
            'tipo_pratica',
            'stato',
            'oggetto',
            'comune',
            'protocollo',
            'data_incarico',
            'data_deposito',
            'scadenza',
            'compenso',
            'note',
        ]

        widgets = {
            'data_incarico': forms.DateInput(attrs={'type': 'date'}),
            'data_deposito': forms.DateInput(attrs={'type': 'date'}),
            'scadenza': forms.DateInput(attrs={'type': 'date'}),
            'note': forms.Textarea(attrs={'rows': 4}),
        }