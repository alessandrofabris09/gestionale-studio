from django import forms

from .models import Documento, TIPI_DOCUMENTO


class DocumentoForm(forms.ModelForm):

    class Meta:
        model = Documento

        fields = [
            'titolo',
            'tipo_documento',
            'file',
            'note',
        ]

        widgets = {
            'note': forms.Textarea(attrs={'rows': 3}),
        }


class MultipleFileInput(forms.ClearableFileInput):

    allow_multiple_selected = True

    def __init__(self, *args, **kwargs):

        kwargs.setdefault(
            'attrs',
            {
                'accept': '.pdf,.p7m,.doc,.docx,.xls,.xlsx,.dwg,.dxf,.jpg,.jpeg,.png',
                'multiple': True,
            }
        )

        super().__init__(*args, **kwargs)


class MultipleFileField(forms.FileField):

    def __init__(self, *args, **kwargs):

        kwargs.setdefault(
            'widget',
            MultipleFileInput()
        )

        super().__init__(*args, **kwargs)

    def validate_file_extension(self, file):

        estensioni_bloccate = [
            '.zip',
            '.rar',
            '.7z',
        ]

        nome_file = file.name.lower()

        for estensione in estensioni_bloccate:

            if nome_file.endswith(estensione):

                raise forms.ValidationError(
                    'I file ZIP/RAR/7Z non sono supportati dal caricamento cloud.'
                )

    def clean(self, data, initial=None):

        single_file_clean = super().clean

        if isinstance(data, (list, tuple)):

            result = []

            for d in data:

                self.validate_file_extension(d)

                result.append(
                    single_file_clean(d, initial)
                )

        else:

            self.validate_file_extension(data)

            result = single_file_clean(
                data,
                initial
            )

        return result


class DocumentoMultiploForm(forms.Form):

    titolo_base = forms.CharField(
        max_length=255,
        required=False,
        label='Titolo base'
    )

    tipo_documento = forms.ChoiceField(
        choices=TIPI_DOCUMENTO,
        label='Tipo documento'
    )

    files = MultipleFileField(
        label='File da caricare'
    )

    note = forms.CharField(
        required=False,
        widget=forms.Textarea(attrs={'rows': 3}),
        label='Note'
    )