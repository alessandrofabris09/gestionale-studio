from django import forms

from .models import VoceOra


class VoceOraForm(forms.ModelForm):

    class Meta:
        model = VoceOra

        fields = [
            'data',
            'tipo_attivita',
            'descrizione',
            'ore',
            'tariffa_oraria',
            'fatturabile',
            'note',
        ]

        widgets = {
            'data': forms.DateInput(attrs={'type': 'date'}),
            'descrizione': forms.Textarea(attrs={'rows': 3}),
            'note': forms.Textarea(attrs={'rows': 2}),
        }
    def clean(self):
        cleaned_data = super().clean()
        for field, label in [('ore', 'Le ore'), ('tariffa_oraria', 'La tariffa oraria')]:
            value = cleaned_data.get(field)
            if value is not None and value < 0:
                self.add_error(field, f'{label} non possono essere negative.' if field == 'ore' else f'{label} non può essere negativa.')
        return cleaned_data
