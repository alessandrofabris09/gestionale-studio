from django import forms

from .models import Pratica
from workflow.models import TipoWorkflow
from workflow.widgets import SelettoreWorkflow
from clienti.models import Cliente
from immobili.models import Immobile


class PraticaForm(forms.ModelForm):

    tipo_pratica = forms.ChoiceField(
        label='Tipo pratica',
        widget=SelettoreWorkflow,
        required=True
    )

    class Meta:
        model = Pratica
        exclude = [
            'studio',
        ]

        widgets = {
            'data_incarico': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'data_deposito': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'scadenza': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'scadenza_compenso': forms.DateInput(format='%Y-%m-%d', attrs={'type': 'date'}),
            'note': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):

        studio = kwargs.pop('studio', None)

        super().__init__(*args, **kwargs)

        self.varianti = {}
        workflow_choices = [('', '---------')]
        categorie = {}
        for workflow in TipoWorkflow.objects.disponibili_per(studio):
            valore = workflow.nome
            etichetta = str(workflow)
            if workflow.studio_id:
                valore = f'variante:{workflow.pk}'
                etichetta = f'{etichetta} (modello dello studio)'
                self.varianti[valore] = workflow
            workflow_choices.append((valore, etichetta))
            categorie[valore] = workflow.get_categoria_display()

        if self.instance.pk:
            nome = self.instance.tipo_pratica
            attivo = getattr(self.instance, 'workflow_pratica', None)
            chiave = f'variante:{attivo.workflow_id}' if attivo else None
            variante = self.varianti.get(chiave)
            if variante and variante.nome == nome:
                self.initial['tipo_pratica'] = chiave
            elif nome not in dict(workflow_choices):
                workflow_choices.append((nome, nome))

        self.fields['tipo_pratica'].choices = workflow_choices
        self.fields['tipo_pratica'].widget.categorie = categorie

        if studio:

            self.fields['cliente'].queryset = Cliente.objects.filter(
                studio=studio
            ).order_by('nome')

            self.fields['immobile'].queryset = Immobile.objects.filter(
                studio=studio
            ).order_by('comune', 'indirizzo')

    def clean_tipo_pratica(self):
        valore = self.cleaned_data['tipo_pratica']
        self.variante_workflow = self.varianti.get(valore)
        return self.variante_workflow.nome if self.variante_workflow else valore
