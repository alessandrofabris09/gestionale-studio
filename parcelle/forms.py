from decimal import Decimal

from django import forms

from pratiche.models import Pratica

from .models import (
    Parcella,
    ALIQUOTE_CASSA_STANDARD,
)


class ParcellaForm(forms.ModelForm):

    class Meta:
        model = Parcella

        fields = [
            'pratica',
            'tipo_documento',
            'numero_documento',
            'descrizione',
            'importo',

            'applica_cassa',
            'tipo_cassa',
            'aliquota_cassa',

            'applica_iva',
            'iva',

            'applica_bollo',
            'importo_bollo',

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
            'aliquota_cassa': forms.NumberInput(
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
            'importo_bollo': forms.NumberInput(
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
            'importo': 'Compenso / imponibile base',

            'applica_cassa': 'Applica contributo cassa',
            'tipo_cassa': 'Tipo cassa previdenziale',
            'aliquota_cassa': 'Aliquota cassa (%)',

            'applica_iva': 'Applica IVA',
            'iva': 'Aliquota IVA (%)',

            'applica_bollo': 'Applica marca da bollo',
            'importo_bollo': 'Importo marca da bollo',

            'importo_pagato': 'Importo pagato',
            'data_emissione': 'Data emissione',
            'data_scadenza': 'Data scadenza',
            'data_pagamento': 'Data pagamento',
            'stato': 'Stato pagamento',
            'note': 'Note',
        }

        help_texts = {
            'numero_documento': 'Lascia vuoto per generare automaticamente il numero documento.',
            'importo': 'Inserire il compenso professionale base, esclusi cassa, IVA e bollo.',
            'applica_cassa': 'Attiva se vuoi addebitare il contributo integrativo previdenziale.',
            'tipo_cassa': 'Scegli la cassa. L’aliquota resta modificabile caso per caso.',
            'aliquota_cassa': 'Geometri 5%, Inarcassa 4%, EPPI 5%, oppure aliquota manuale.',
            'applica_iva': 'Disattiva per operazioni non soggette IVA o regimi particolari.',
            'iva': 'Aliquota IVA. Normalmente 22%.',
            'applica_bollo': 'Attiva se vuoi addebitare marca da bollo.',
            'importo_bollo': 'Normalmente € 2,00.',
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

        self.fields['numero_documento'].required = False
        self.fields['importo_pagato'].required = False
        self.fields['data_emissione'].required = False
        self.fields['data_scadenza'].required = False
        self.fields['data_pagamento'].required = False
        self.fields['note'].required = False
        self.fields['aliquota_cassa'].required = False
        self.fields['iva'].required = False
        self.fields['importo_bollo'].required = False

        if not self.instance or not self.instance.pk:

            self.fields['applica_cassa'].initial = True
            self.fields['tipo_cassa'].initial = 'GEOMETRI'
            self.fields['aliquota_cassa'].initial = Decimal('5.00')

            self.fields['applica_iva'].initial = True
            self.fields['iva'].initial = Decimal('22.00')

            self.fields['applica_bollo'].initial = False
            self.fields['importo_bollo'].initial = Decimal('2.00')

            self.fields['importo_pagato'].initial = Decimal('0.00')

    def clean(self):

        cleaned_data = super().clean()

        applica_cassa = cleaned_data.get('applica_cassa')
        tipo_cassa = cleaned_data.get('tipo_cassa')
        aliquota_cassa = cleaned_data.get('aliquota_cassa')

        applica_iva = cleaned_data.get('applica_iva')
        iva = cleaned_data.get('iva')

        applica_bollo = cleaned_data.get('applica_bollo')
        importo_bollo = cleaned_data.get('importo_bollo')

        if not applica_cassa:

            cleaned_data['tipo_cassa'] = 'NESSUNA'
            cleaned_data['aliquota_cassa'] = Decimal('0.00')

        else:

            if not tipo_cassa:
                cleaned_data['tipo_cassa'] = 'GEOMETRI'
                tipo_cassa = 'GEOMETRI'

            if aliquota_cassa is None or aliquota_cassa == Decimal('0.00'):

                cleaned_data['aliquota_cassa'] = ALIQUOTE_CASSA_STANDARD.get(
                    tipo_cassa,
                    Decimal('0.00')
                )

        if not applica_iva:

            if iva is None:
                cleaned_data['iva'] = Decimal('0.00')

        else:

            if iva is None or iva == Decimal('0.00'):
                cleaned_data['iva'] = Decimal('22.00')

        if applica_bollo:

            if importo_bollo is None or importo_bollo == Decimal('0.00'):
                cleaned_data['importo_bollo'] = Decimal('2.00')

        else:

            if importo_bollo is None:
                cleaned_data['importo_bollo'] = Decimal('2.00')

        return cleaned_data