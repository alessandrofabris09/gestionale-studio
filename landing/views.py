from django.shortcuts import render, redirect


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