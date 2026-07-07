from django import forms
from django.contrib.auth.models import User
from django.db import transaction

from .models import Studio, ProfiloUtente


class StudioForm(forms.ModelForm):

    class Meta:
        model = Studio

        fields = [
            'nome',
            'email',
            'telefono',
            'indirizzo',
            'partita_iva',
        ]

        labels = {
            'nome': 'Nome studio',
            'email': 'Email notifiche studio',
            'telefono': 'Telefono',
            'indirizzo': 'Indirizzo',
            'partita_iva': 'Partita IVA / Codice fiscale',
        }

        widgets = {
            'nome': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Es. Studio Tecnico Rossi'
                }
            ),
            'email': forms.EmailInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'email@studio.it'
                }
            ),
            'telefono': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Telefono studio'
                }
            ),
            'indirizzo': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Indirizzo sede studio'
                }
            ),
            'partita_iva': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Partita IVA o codice fiscale'
                }
            ),
        }


class NuovoUtenteStudioForm(forms.Form):

    username = forms.CharField(
        label='Username',
        max_length=150,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Es. mrossi'
            }
        )
    )

    first_name = forms.CharField(
        label='Nome',
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Nome'
            }
        )
    )

    last_name = forms.CharField(
        label='Cognome',
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Cognome'
            }
        )
    )

    email = forms.EmailField(
        label='Email',
        required=True,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'email@studio.it'
            }
        )
    )

    ruolo = forms.ChoiceField(
        label='Ruolo nel gestionale',
        choices=[
            ('TITOLARE', 'Titolare'),
            ('TECNICO', 'Tecnico'),
            ('SEGRETERIA', 'Segreteria'),
            ('COLLABORATORE', 'Collaboratore'),
        ],
        widget=forms.Select(
            attrs={
                'class': 'form-control'
            }
        )
    )

    password1 = forms.CharField(
        label='Password provvisoria',
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Password provvisoria'
            }
        )
    )

    password2 = forms.CharField(
        label='Conferma password',
        widget=forms.PasswordInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Ripeti la password'
            }
        )
    )

    def clean_username(self):

        username = self.cleaned_data.get('username')

        if User.objects.filter(username__iexact=username).exists():
            raise forms.ValidationError(
                'Esiste già un utente con questo username.'
            )

        return username

    def clean_email(self):

        email = self.cleaned_data.get('email')

        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                'Esiste già un utente con questa email.'
            )

        return email

    def clean(self):

        cleaned_data = super().clean()

        password1 = cleaned_data.get('password1')
        password2 = cleaned_data.get('password2')

        if password1 and password2 and password1 != password2:
            raise forms.ValidationError(
                'Le due password non coincidono.'
            )

        return cleaned_data

    @transaction.atomic
    def save(self, studio):

        user = User.objects.create_user(
            username=self.cleaned_data['username'],
            email=self.cleaned_data['email'],
            password=self.cleaned_data['password1'],
            first_name=self.cleaned_data.get('first_name', ''),
            last_name=self.cleaned_data.get('last_name', ''),
        )

        user.is_active = True
        user.is_staff = False
        user.is_superuser = False
        user.save()

        profilo = ProfiloUtente.objects.create(
            user=user,
            studio=studio,
            ruolo=self.cleaned_data['ruolo']
        )

        return profilo


class ProfiloUtenteRuoloForm(forms.ModelForm):

    first_name = forms.CharField(
        label='Nome',
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Nome utente'
            }
        )
    )

    last_name = forms.CharField(
        label='Cognome',
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Cognome utente'
            }
        )
    )

    email = forms.EmailField(
        label='Email account utente',
        required=False,
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'email@studio.it'
            }
        )
    )

    class Meta:
        model = ProfiloUtente

        fields = [
            'ruolo',
        ]

        labels = {
            'ruolo': 'Ruolo utente',
        }

        widgets = {
            'ruolo': forms.Select(
                attrs={
                    'class': 'form-control'
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        if self.instance and self.instance.user:

            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):

        profilo = super().save(commit=False)

        user = profilo.user

        user.first_name = self.cleaned_data.get(
            'first_name',
            ''
        )

        user.last_name = self.cleaned_data.get(
            'last_name',
            ''
        )

        user.email = self.cleaned_data.get(
            'email',
            ''
        )

        if commit:

            user.save()
            profilo.save()

        return profilo