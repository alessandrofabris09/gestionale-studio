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