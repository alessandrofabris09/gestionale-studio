from django import forms

from .models import Pratica
from workflow.models import TipoWorkflow


class PraticaForm(forms.ModelForm):

    tipo_pratica = forms.ChoiceField(
        label='Tipo pratica',
        required=True
    )

    class Meta:
        model = Pratica
        fields = '__all__'

        widgets = {
            'data_incarico': forms.DateInput(attrs={'type': 'date'}),
            'data_deposito': forms.DateInput(attrs={'type': 'date'}),
            'scadenza': forms.DateInput(attrs={'type': 'date'}),
            'note': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):

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