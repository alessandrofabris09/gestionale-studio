from django import forms


class RichiestaProForm(forms.Form):
    email = forms.EmailField(
        label='Email dello studio',
        widget=forms.EmailInput(attrs={'autocomplete': 'email', 'maxlength': 254}),
    )
    consenso = forms.BooleanField(
        label='Acconsento a ricevere via email gli aggiornamenti sulla mia candidatura e sulle condizioni della beta PRO.',
    )

    def clean_email(self):
        return self.cleaned_data['email'].lower()
