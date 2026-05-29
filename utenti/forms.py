from django import forms
from django.contrib.auth.models import User


class RegistrazioneStudioForm(forms.Form):

    nome_studio = forms.CharField(
        max_length=255,
        label='Nome studio'
    )

    email = forms.EmailField(
        label='Email'
    )

    username = forms.CharField(
        max_length=150,
        label='Username'
    )

    password = forms.CharField(
        widget=forms.PasswordInput,
        label='Password'
    )

    conferma_password = forms.CharField(
        widget=forms.PasswordInput,
        label='Conferma password'
    )

    telefono = forms.CharField(
        max_length=50,
        required=False,
        label='Telefono'
    )

    partita_iva = forms.CharField(
        max_length=50,
        required=False,
        label='Partita IVA'
    )

    def clean_username(self):

        username = self.cleaned_data.get('username')

        if User.objects.filter(username=username).exists():

            raise forms.ValidationError(
                'Questo username è già stato utilizzato.'
            )

        return username

    def clean_email(self):

        email = self.cleaned_data.get('email')

        if User.objects.filter(email=email).exists():

            raise forms.ValidationError(
                'Questa email è già registrata.'
            )

        return email

    def clean(self):

        cleaned_data = super().clean()

        password = cleaned_data.get('password')

        conferma_password = cleaned_data.get('conferma_password')

        if password and conferma_password and password != conferma_password:

            raise forms.ValidationError(
                'Le password non coincidono.'
            )

        return cleaned_data
    
from studi.models import ProfiloUtente


class NuovoUtenteStudioForm(forms.Form):

    first_name = forms.CharField(
        max_length=150,
        label='Nome'
    )

    last_name = forms.CharField(
        max_length=150,
        required=False,
        label='Cognome'
    )

    email = forms.EmailField(
        label='Email'
    )

    username = forms.CharField(
        max_length=150,
        label='Username'
    )

    password = forms.CharField(
        widget=forms.PasswordInput,
        label='Password'
    )

    ruolo = forms.ChoiceField(
        choices=[
            ('TECNICO', 'Tecnico'),
            ('SEGRETERIA', 'Segreteria'),
            ('COLLABORATORE', 'Collaboratore'),
        ],
        label='Ruolo'
    )

    def clean_username(self):

        username = self.cleaned_data.get('username')

        if User.objects.filter(username=username).exists():
            raise forms.ValidationError(
                'Questo username è già stato utilizzato.'
            )

        return username

    def clean_email(self):

        email = self.cleaned_data.get('email')

        if User.objects.filter(email=email).exists():
            raise forms.ValidationError(
                'Questa email è già registrata.'
            )

        return email


class ModificaRuoloUtenteForm(forms.ModelForm):

    class Meta:
        model = ProfiloUtente

        fields = [
            'ruolo',
        ]    