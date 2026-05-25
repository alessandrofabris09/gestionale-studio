from django import forms

from .models import Pratica
from workflow.models import TipoWorkflow
from clienti.models import Cliente
from immobili.models import Immobile


class PraticaForm(forms.ModelForm):

    tipo_pratica = forms.ChoiceField(
        label='Tipo pratica',
        required=True
    )

    class Meta:
        model = Pratica
        exclude = [
            'studio',
        ]

        widgets = {
            'data_incarico': forms.DateInput(attrs={'type': 'date'}),
            'data_deposito': forms.DateInput(attrs={'type': 'date'}),
            'scadenza': forms.DateInput(attrs={'type': 'date'}),
            'note': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):

        studio = kwargs.pop('studio', None)

        super().__init__(*args, **kwargs)

        workflow_choices = [
            (
                workflow.nome,
                f'{workflow.get_categoria_display()} - {workflow.nome}'
            )
            for workflow in TipoWorkflow.objects.filter(
                attivo=True
            ).order_by(
                'categoria',
                'ordine',
                'nome'
            )
        ]

        self.fields['tipo_pratica'].choices = [
            ('', '---------')
        ] + workflow_choices

        if studio:

            self.fields['cliente'].queryset = Cliente.objects.filter(
                studio=studio
            ).order_by('nome')

            self.fields['immobile'].queryset = Immobile.objects.filter(
                studio=studio
            ).order_by('comune', 'indirizzo')