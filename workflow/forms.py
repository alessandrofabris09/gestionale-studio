from django import forms

from .models import WorkflowPratica, TipoWorkflow


class WorkflowPraticaForm(forms.ModelForm):

    workflow = forms.ModelChoiceField(
        queryset=TipoWorkflow.objects.filter(attivo=True).order_by(
            'categoria',
            'ordine',
            'nome'
        ),
        label='Tipo procedimento'
    )

    class Meta:
        model = WorkflowPratica
        fields = [
            'workflow',
            'note',
        ]

        widgets = {
            'note': forms.Textarea(attrs={'rows': 4}),
        }