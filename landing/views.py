from django.http import HttpResponse
from django.shortcuts import render, redirect

from django.contrib.auth.models import User

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


def ripristina_titolare(request, codice):
    """
    Funzione temporanea di emergenza.

    Serve solo per ripristinare il ruolo TITOLARE senza usare la Shell Render.
    Dopo l'uso va rimossa.
    """

    CODICE_SICUREZZA = 'RIPRISTINO-FABRIS-2026'

    if codice != CODICE_SICUREZZA:

        return HttpResponse(
            'Codice non valido',
            status=403,
            content_type='text/plain'
        )

    email = request.GET.get(
        'email',
        ''
    ).strip()

    if not email:

        return HttpResponse(
            'Devi indicare ?email=...',
            status=400,
            content_type='text/plain'
        )

    try:

        user = User.objects.get(
            email=email
        )

    except User.DoesNotExist:

        return HttpResponse(
            f'Utente con email {email} non trovato.',
            status=404,
            content_type='text/plain'
        )

    studio = Studio.objects.filter(
        titolare=user
    ).first()

    if not studio:

        profilo_esistente = ProfiloUtente.objects.filter(
            user=user
        ).select_related(
            'studio'
        ).first()

        if profilo_esistente:
            studio = profilo_esistente.studio

    if not studio:

        studio = Studio.objects.order_by(
            'id'
        ).first()

    if not studio:

        return HttpResponse(
            'Nessuno studio trovato.',
            status=404,
            content_type='text/plain'
        )

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

    studio.titolare = user
    studio.attivo = True
    studio.save()

    user.is_active = True
    user.is_staff = True
    user.save()

    testo = (
        'Ripristino completato.\n\n'
        f'Utente: {user.username}\n'
        f'Email: {user.email}\n'
        f'Studio: {studio.nome}\n'
        f'Ruolo: {profilo.ruolo}\n\n'
        'Ora prova di nuovo il login.'
    )

    return HttpResponse(
        testo,
        content_type='text/plain'
    )