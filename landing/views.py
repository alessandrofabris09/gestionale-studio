from datetime import timedelta

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone

from studi.models import Studio, ProfiloUtente


def home(request):
    """
    Landing page pubblica del gestionale.

    Se l'utente è già autenticato, viene portato direttamente
    alla dashboard operativa.
    """

    if request.user.is_authenticated:

        return redirect(
            '/dashboard/'
        )

    return render(
        request,
        'landing/home.html'
    )


def privacy_policy(request):
    """
    Pagina Privacy Policy.
    """

    return render(
        request,
        'landing/privacy.html'
    )


def termini_utilizzo(request):
    """
    Pagina Termini di utilizzo.
    """

    return render(
        request,
        'landing/termini.html'
    )


def crea_superuser_iniziale(request, codice):
    """
    Funzione temporanea di emergenza.

    Serve solo per creare il primo superuser e lo studio iniziale
    dopo il passaggio a un database nuovo.
    Dopo l'uso va rimossa.
    """

    CODICE_SICUREZZA = 'CREA-SUPERUSER-FABRIS-2026'

    if codice != CODICE_SICUREZZA:

        return HttpResponse(
            'Codice non valido',
            status=403,
            content_type='text/plain'
        )

    username = request.GET.get(
        'username',
        'admin'
    ).strip()

    email = request.GET.get(
        'email',
        ''
    ).strip()

    password = request.GET.get(
        'password',
        ''
    ).strip()

    nome_studio = request.GET.get(
        'studio',
        'Studio Tecnico'
    ).strip()

    if not email or not password:

        return HttpResponse(
            'Devi indicare ?email=...&password=...',
            status=400,
            content_type='text/plain'
        )

    user = User.objects.filter(
        email=email
    ).first()

    if not user:

        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )

    else:

        user.username = username
        user.email = email
        user.is_active = True
        user.is_staff = True
        user.is_superuser = True
        user.set_password(password)
        user.save()

    studio = Studio.objects.filter(
        titolare=user
    ).first()

    if not studio:

        studio = Studio.objects.create(
            nome=nome_studio,
            email=email,
            telefono='',
            titolare=user,
            piano='PRO',
            stato_abbonamento='ATTIVO',
            trial_fino_al=timezone.now().date() + timedelta(days=14),
            limite_pratiche=999999,
            limite_utenti=999999,
            limite_storage_mb=50000,
            attivo=True,
        )

    else:

        studio.nome = nome_studio
        studio.email = email
        studio.titolare = user
        studio.piano = 'PRO'
        studio.stato_abbonamento = 'ATTIVO'
        studio.limite_pratiche = 999999
        studio.limite_utenti = 999999
        studio.limite_storage_mb = 50000
        studio.attivo = True
        studio.save()

    profilo, created = ProfiloUtente.objects.get_or_create(
        user=user,
        defaults={
            'studio': studio,
            'ruolo': 'TITOLARE',
        }
    )

    profilo.studio = studio
    profilo.ruolo = 'TITOLARE'
    profilo.save()

    testo = (
        'Creazione completata.\n\n'
        f'Username: {user.username}\n'
        f'Email: {user.email}\n'
        f'Superuser: {user.is_superuser}\n'
        f'Studio: {studio.nome}\n'
        f'Ruolo: {profilo.ruolo}\n\n'
        'Ora puoi accedere dal login.'
    )

    return HttpResponse(
        testo,
        content_type='text/plain'
    )