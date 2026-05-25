from django import forms

from clienti.models import Cliente

from .models import Immobile


class ImmobileForm(forms.ModelForm):

    class Meta:
        model = Immobile

        exclude = [
            'studio',
        ]

        widgets = {
            'vincoli': forms.Textarea(attrs={'rows': 4}),
            'note': forms.Textarea(attrs={'rows': 4}),
        }

    def __init__(self, *args, **kwargs):

        studio = kwargs.pop('studio', None)

        super().__init__(*args, **kwargs)

        if studio:

            self.fields['cliente'].queryset = Cliente.objects.filter(
                studio=studio
            ).order_by('nome')