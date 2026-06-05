from datetime import timedelta

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.views import LoginView, LogoutView
from django.shortcuts import render, redirect
from django.utils import timezone

from studi.models import Studio, ProfiloUtente

from .forms import RegistrazioneStudioForm


class CustomLoginView(LoginView):
    template_name = 'accounts/login.html'


class CustomLogoutView(LogoutView):
    pass


def registrazione_studio(request):
    """
    Registrazione pubblica di un nuovo studio.

    Crea:
    - utente titolare
    - studio collegato
    - profilo utente con ruolo TITOLARE
    """

    if request.user.is_authenticated:

        return redirect(
            '/dashboard/'
        )

    if request.method == 'POST':

        form = RegistrazioneStudioForm(
            request.POST
        )

        if form.is_valid():

            user = form.save(
                commit=False
            )

            user.email = form.cleaned_data.get(
                'email'
            )

            user.save()

            studio = Studio.objects.create(
                nome=form.cleaned_data.get(
                    'nome_studio'
                ),
                email=form.cleaned_data.get(
                    'email'
                ),
                telefono=form.cleaned_data.get(
                    'telefono'
                ),
                titolare=user,
                piano='FREE',
                stato_abbonamento='TRIAL',
                trial_fino_al=timezone.now().date() + timedelta(days=14),
                limite_pratiche=10,
                limite_utenti=1,
                limite_storage_mb=500,
                attivo=True,
            )

            ProfiloUtente.objects.create(
                user=user,
                studio=studio,
                ruolo='TITOLARE',
            )

            login(
                request,
                user
            )

            messages.success(
                request,
                'Registrazione completata. Il tuo studio è stato creato correttamente.'
            )

            return redirect(
                '/dashboard/'
            )

    else:

        form = RegistrazioneStudioForm()

    return render(
        request,
        'accounts/registrazione.html',
        {
            'form': form
        }
    )