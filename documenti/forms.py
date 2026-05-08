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


class MultipleFileField(forms.FileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', MultipleFileInput())
        super().__init__(*args, **kwargs)

    def clean(self, data, initial=None):
        single_file_clean = super().clean

        if isinstance(data, (list, tuple)):
            result = [
                single_file_clean(d, initial)
                for d in data
            ]
        else:
            result = single_file_clean(data, initial)

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