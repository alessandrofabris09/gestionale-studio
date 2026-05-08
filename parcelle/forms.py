from django import forms
from .models import Parcella


class ParcellaForm(forms.ModelForm):
    class Meta:
        model = Parcella
        fields = '__all__'

        widgets = {
            'data_emissione': forms.DateInput(attrs={'type': 'date'}),
            'data_pagamento': forms.DateInput(attrs={'type': 'date'}),
            'note': forms.Textarea(attrs={'rows': 3}),
        }