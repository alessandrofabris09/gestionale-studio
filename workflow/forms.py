from django import forms

from .models import ChecklistWorkflow, FaseWorkflow, WorkflowPratica, TipoWorkflow
from .widgets import SelettoreWorkflow


class CopiaModelloForm(forms.Form):
    modello = forms.ModelChoiceField(
        queryset=TipoWorkflow.objects.none(), label='Modello standard', widget=SelettoreWorkflow,
    )

    def __init__(self, *args, standard, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['modello'].queryset = standard


class VarianteWorkflowForm(forms.ModelForm):
    class Meta:
        model = TipoWorkflow
        fields = ['nome', 'descrizione']
        widgets = {'descrizione': forms.Textarea(attrs={'rows': 3})}


FasiVariante = forms.inlineformset_factory(
    TipoWorkflow, FaseWorkflow,
    fields=['titolo', 'descrizione', 'ordine', 'giorni_scadenza'], extra=1,
    widgets={'descrizione': forms.Textarea(attrs={'rows': 2})},
)
ChecklistVariante = forms.inlineformset_factory(
    TipoWorkflow, ChecklistWorkflow,
    fields=['voce', 'descrizione', 'ordine', 'obbligatorio'], extra=1,
    widgets={'descrizione': forms.Textarea(attrs={'rows': 2})},
)


class WorkflowPraticaForm(forms.ModelForm):

    workflow = forms.ModelChoiceField(
        queryset=TipoWorkflow.objects.none(),
        label='Tipo procedimento',
        widget=SelettoreWorkflow,
    )

    def __init__(self, *args, studio=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['workflow'].queryset = TipoWorkflow.objects.disponibili_per(studio)

    class Meta:
        model = WorkflowPratica
        fields = [
            'workflow',
            'note',
        ]

        widgets = {
            'note': forms.Textarea(attrs={'rows': 4}),
        }
