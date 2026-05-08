from django import forms
from .models import Immobile


class ImmobileForm(forms.ModelForm):

    class Meta:
        model = Immobile
        fields = '__all__'

        widgets = {
            'vincoli': forms.Textarea(attrs={'rows': 4}),
            'note': forms.Textarea(attrs={'rows': 4}),
        }