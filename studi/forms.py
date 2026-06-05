from django import forms

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