from django import forms

from pratiche.models import Pratica

from .models import Scadenza


class ScadenzaForm(forms.ModelForm):

    class Meta:
        model = Scadenza
        fields = '__all__'

        widgets = {
            'data_scadenza': forms.DateInput(attrs={'type': 'date'}),
            'descrizione': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):

        studio = kwargs.pop('studio', None)

        super().__init__(*args, **kwargs)

        if studio:

            self.fields['pratica'].queryset = Pratica.objects.filter(
                studio=studio
            ).order_by('-id')