from datetime import timedelta

from django.contrib.auth import login
from django.contrib.auth.models import Group, User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.utils import timezone
from django.http import HttpResponseForbidden

from studi.models import Studio, ProfiloUtente
from studi.utils import (
    get_studio_utente,
    studio_puo_aggiungere_utenti,
)
from studi.permessi import puo_gestire_utenti

from .forms import (
    RegistrazioneStudioForm,
    NuovoUtenteStudioForm,
)


def accesso_negato(request):
    """
    Pagina semplice di blocco accesso.
    """

    return HttpResponseForbidden(
        """
        <h1>Accesso negato</h1>
        <p>Non hai i permessi per accedere a questa sezione.</p>
        <p><a href="/dashboard/">Torna alla dashboard</a></p>
        """
    )


@login_required
def lista_utenti(request):

    if not puo_gestire_utenti(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio and not request.user.is_superuser:
        return redirect('login')

    if request.user.is_superuser:
        profili = ProfiloUtente.objects.all().select_related(
            'user',
            'studio'
        ).order_by(
            'studio__nome',
            'ruolo',
            'user__username'
        )
    else:
        profili = ProfiloUtente.objects.filter(
            studio=studio
        ).select_related(
            'user'
        ).order_by(
            'ruolo',
            'user__username'
        )

    return render(
        request,
        'utenti/lista_utenti.html',
        {
            'profili': profili,
            'studio': studio,
        }
    )


@login_required
def nuovo_utente(request):

    if not puo_gestire_utenti(request):
        return accesso_negato(request)

    studio = get_studio_utente(request)

    if not studio and not request.user.is_superuser:
        return redirect('login')

    if not request.user.is_superuser:

        if not studio_puo_aggiungere_utenti(studio):

            return render(
                request,
                'studi/upgrade_required.html',
                {
                    'studio': studio,
                    'titolo': 'Limite utenti raggiunto',
                    'messaggio': (
                        f'Il piano FREE consente massimo '
                        f'{studio.limite_utenti} utente. '
                        f'Per aggiungere collaboratori passa al piano PRO.'
                    ),
                    'azione': 'Passa al piano PRO',
                }
            )

    if request.method == 'POST':

        form = NuovoUtenteStudioForm(request.POST)

        if form.is_valid():

            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )

            user.first_name = form.cleaned_data['first_name']
            user.last_name = form.cleaned_data['last_name']
            user.save()

            ProfiloUtente.objects.create(
                user=user,
                studio=studio,
                ruolo=form.cleaned_data['ruolo']
            )

            return redirect('lista_utenti')

    else:

        form = NuovoUtenteStudioForm()

    return render(
        request,
        'utenti/nuovo_utente.html',
        {
            'form': form,
            'studio': studio,
        }
    )


def registrazione_studio(request):

    if request.user.is_authenticated:

        return redirect('home')

    if request.method == 'POST':

        form = RegistrazioneStudioForm(request.POST)

        if form.is_valid():

            user = User.objects.create_user(
                username=form.cleaned_data['username'],
                email=form.cleaned_data['email'],
                password=form.cleaned_data['password']
            )

            user.first_name = form.cleaned_data['nome_studio']
            user.save()

            admin_group, created = Group.objects.get_or_create(
                name='Admin Studio'
            )

            user.groups.add(admin_group)

            studio = Studio.objects.create(
                nome=form.cleaned_data['nome_studio'],
                titolare=user,
                email=form.cleaned_data['email'],
                telefono=form.cleaned_data.get('telefono', ''),
                partita_iva=form.cleaned_data.get('partita_iva', ''),
                attivo=True,
                piano='FREE',
                stato_abbonamento='TRIAL',
                trial_fino_al=timezone.now().date() + timedelta(days=14),
                limite_pratiche=20,
                limite_utenti=1,
                limite_storage_mb=500
            )

            ProfiloUtente.objects.create(
                user=user,
                studio=studio,
                ruolo='TITOLARE'
            )

            login(request, user)

            return redirect('home')

        else:

            print(form.errors)

    else:

        form = RegistrazioneStudioForm()

    return render(
        request,
        'utenti/registrazione_studio.html',
        {
            'form': form
        }
    )