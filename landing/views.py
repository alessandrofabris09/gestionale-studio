from datetime import timedelta

from django.contrib.auth.models import User
from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.utils import timezone

from studi.models import Studio, ProfiloUtente


def home(request):
    if request.user.is_authenticated:
        return redirect('/dashboard/')

    return render(request, 'landing/home.html')


def privacy_policy(request):
    return render(request, 'landing/privacy.html')


def termini_utilizzo(request):
    return render(request, 'landing/termini.html')


def ripristina_admin(request, codice):
    """
    Funzione temporanea di emergenza.
    Serve solo per ripristinare l'accesso admin sul nuovo database.
    Dopo l'uso va rimossa.
    """

    CODICE_SICUREZZA = 'RIPRISTINA-ADMIN-FABRIS-2026'

    if codice != CODICE_SICUREZZA:
        return HttpResponse(
            'Codice non valido',
            status=403,
            content_type='text/plain'
        )

    username = request.GET.get('username', 'admin').strip()
    email = request.GET.get('email', '').strip()
    password = request.GET.get('password', '').strip()
    nome_studio = request.GET.get('studio', 'Studio Tecnico Fabris').strip()

    if not email or not password:
        return HttpResponse(
            'Devi indicare ?email=...&password=...',
            status=400,
            content_type='text/plain'
        )

    user = User.objects.filter(username=username).first()

    if not user:
        user = User.objects.filter(email=email).first()

    if not user:
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password
        )

    user.username = username
    user.email = email
    user.is_active = True
    user.is_staff = True
    user.is_superuser = True
    user.set_password(password)
    user.save()

    studio = Studio.objects.filter(titolare=user).first()

    if not studio:
        studio = Studio.objects.first()

    if not studio:
        studio = Studio.objects.create(
            nome=nome_studio,
            titolare=user,
            email=email,
            telefono='',
            piano='PRO',
            stato_abbonamento='ATTIVO',
            trial_fino_al=timezone.now().date() + timedelta(days=14),
            limite_pratiche=999999,
            limite_utenti=999999,
            limite_storage_mb=50000,
            attivo=True,
        )

    studio.nome = nome_studio
    studio.titolare = user
    studio.email = email
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
        'Ripristino admin completato.\n\n'
        f'Username: {user.username}\n'
        f'Email: {user.email}\n'
        f'Is active: {user.is_active}\n'
        f'Is staff: {user.is_staff}\n'
        f'Is superuser: {user.is_superuser}\n'
        f'Studio: {studio.nome}\n'
        f'Ruolo: {profilo.ruolo}\n\n'
        'Ora prova ad accedere a /admin/ usando lo username indicato.'
    )

    return HttpResponse(
        testo,
        content_type='text/plain'
    )