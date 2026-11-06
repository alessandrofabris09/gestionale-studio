from django import forms
from .models import Cliente


class ClienteForm(forms.ModelForm):

    class Meta:

        model = Cliente

        exclude = ['studio']

        widgets = {
            'note': forms.Textarea(attrs={'rows': 4}),
        }