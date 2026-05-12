from django import forms
from .models import EventoAgenda


class EventoAgendaForm(forms.ModelForm):

    class Meta:
        model = EventoAgenda

        fields = '__all__'

        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
            'ora_inizio': forms.TimeInput(attrs={'type': 'time'}),
            'ora_fine': forms.TimeInput(attrs={'type': 'time'}),
            'descrizione': forms.Textarea(attrs={'rows': 4}),
        }