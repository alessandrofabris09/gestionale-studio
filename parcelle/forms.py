from django import forms

from pratiche.models import Pratica

from .models import Parcella


class ParcellaForm(forms.ModelForm):

    class Meta:
        model = Parcella

        fields = [
            'pratica',
            'tipo_documento',
            'numero_documento',
            'descrizione',
            'importo',
            'iva',
            'importo_pagato',
            'data_emissione',
            'data_scadenza',
            'data_pagamento',
            'stato',
            'note',
        ]

        widgets = {
            'data_emissione': forms.DateInput(
                attrs={
                    'type': 'date'
                }
            ),
            'data_scadenza': forms.DateInput(
                attrs={
                    'type': 'date'
                }
            ),
            'data_pagamento': forms.DateInput(
                attrs={
                    'type': 'date'
                }
            ),
            'note': forms.Textarea(
                attrs={
                    'rows': 4,
                    'placeholder': 'Eventuali note da riportare nel documento...'
                }
            ),
            'descrizione': forms.TextInput(
                attrs={
                    'placeholder': 'Es. Compenso professionale per pratica edilizia'
                }
            ),
            'importo': forms.NumberInput(
                attrs={
                    'step': '0.01',
                    'min': '0'
                }
            ),
            'importo_pagato': forms.NumberInput(
                attrs={
                    'step': '0.01',
                    'min': '0'
                }
            ),
            'iva': forms.NumberInput(
                attrs={
                    'step': '0.01',
                    'min': '0'
                }
            ),
        }

        labels = {
            'pratica': 'Pratica collegata',
            'tipo_documento': 'Tipo documento',
            'numero_documento': 'Numero documento',
            'descrizione': 'Descrizione prestazione',
            'importo': 'Imponibile',
            'iva': 'IVA (%)',
            'importo_pagato': 'Importo pagato',
            'data_emissione': 'Data emissione',
            'data_scadenza': 'Data scadenza',
            'data_pagamento': 'Data pagamento',
            'stato': 'Stato pagamento',
            'note': 'Note',
        }

        help_texts = {
            'numero_documento': 'Lascia vuoto per generare automaticamente il numero documento.',
            'importo': 'Inserire l’importo imponibile, IVA esclusa.',
            'iva': 'Inserire la percentuale IVA. Usare 0 per operazioni senza IVA.',
            'importo_pagato': 'Inserire quanto è già stato incassato.',
        }

    def __init__(self, *args, **kwargs):

        studio = kwargs.pop(
            'studio',
            None
        )

        super().__init__(
            *args,
            **kwargs
        )

        if studio:

            self.fields['pratica'].queryset = Pratica.objects.filter(
                studio=studio
            ).order_by(
                '-id'
            )

        else:

            self.fields['pratica'].queryset = Pratica.objects.all().order_by(
                '-id'
            )

        self.fields['iva'].required = False
        self.fields['importo_pagato'].required = False
        self.fields['numero_documento'].required = False
        self.fields['data_emissione'].required = False
        self.fields['data_scadenza'].required = False
        self.fields['data_pagamento'].required = False
        self.fields['note'].required = False

        if not self.instance or not self.instance.pk:

            self.fields['iva'].initial = 22
            self.fields['importo_pagato'].initial = 0