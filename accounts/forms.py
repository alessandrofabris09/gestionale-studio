from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm


class RegistrazioneStudioForm(UserCreationForm):

    nome_studio = forms.CharField(
        label='Nome studio',
        max_length=255,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Es. Studio Tecnico Rossi'
            }
        )
    )

    email = forms.EmailField(
        label='Email account e notifiche',
        widget=forms.EmailInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'email@studio.it'
            }
        )
    )

    telefono = forms.CharField(
        label='Telefono',
        max_length=50,
        required=False,
        widget=forms.TextInput(
            attrs={
                'class': 'form-control',
                'placeholder': 'Telefono studio'
            }
        )
    )

    accetta_privacy = forms.BooleanField(
        label='Dichiaro di aver letto la Privacy Policy.',
        required=True
    )

    accetta_termini = forms.BooleanField(
        label='Dichiaro di accettare i Termini di utilizzo del servizio.',
        required=True
    )

    class Meta:
        model = User

        fields = [
            'username',
            'email',
            'password1',
            'password2',
        ]

        labels = {
            'username': 'Nome utente',
        }

        widgets = {
            'username': forms.TextInput(
                attrs={
                    'class': 'form-control',
                    'placeholder': 'Es. studio.rossi'
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(*args, **kwargs)

        self.fields['password1'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Password'
        })

        self.fields['password2'].widget.attrs.update({
            'class': 'form-control',
            'placeholder': 'Conferma password'
        })

        self.fields['password1'].label = 'Password'
        self.fields['password2'].label = 'Conferma password'

    def clean_email(self):

        email = self.cleaned_data.get(
            'email'
        )

        if User.objects.filter(email=email).exists():

            raise forms.ValidationError(
                'Esiste già un account con questa email.'
            )

        return email