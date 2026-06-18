from django import forms

from .models import VoceOra


class VoceOraForm(forms.ModelForm):

    class Meta:
        model = VoceOra

        fields = [
            'data',
            'tipo_attivita',
            'descrizione',
            'ore',
            'tariffa_oraria',
            'fatturabile',
            'note',
        ]

        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
            'descrizione': forms.Textarea(attrs={'rows': 3}),
            'note': forms.Textarea(attrs={'rows': 2}),
        }