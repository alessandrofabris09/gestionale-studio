from django import forms

from pratiche.models import Pratica

from .models import Parcella


class ParcellaForm(forms.ModelForm):

    class Meta:
        model = Parcella
        fields = '__all__'

        widgets = {
            'data_emissione': forms.DateInput(attrs={'type': 'date'}),
            'data_scadenza': forms.DateInput(attrs={'type': 'date'}),
            'data_pagamento': forms.DateInput(attrs={'type': 'date'}),
            'note': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):

        studio = kwargs.pop('studio', None)

        super().__init__(*args, **kwargs)

        if studio:

            self.fields['pratica'].queryset = Pratica.objects.filter(
                studio=studio
            ).order_by('-id')

        self.fields['iva'].required = False
        self.fields['iva'].initial = 0