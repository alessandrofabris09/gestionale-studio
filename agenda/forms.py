from django import forms

from clienti.models import Cliente
from pratiche.models import Pratica

from .models import EventoAgenda


class EventoAgendaForm(forms.ModelForm):

    class Meta:

        model = EventoAgenda

        exclude = [
            'studio',
        ]

        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
            'ora_inizio': forms.TimeInput(attrs={'type': 'time'}),
            'ora_fine': forms.TimeInput(attrs={'type': 'time'}),
            'descrizione': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):

        studio = kwargs.pop('studio', None)

        super().__init__(*args, **kwargs)

        if studio:

            self.fields['cliente'].queryset = Cliente.objects.filter(
                studio=studio
            ).order_by('nome')

            self.fields['pratica'].queryset = Pratica.objects.filter(
                studio=studio
            ).order_by('-id')