from django.shortcuts import redirect


def get_studio_utente(request):

    if not request.user.is_authenticated:
        return None

    try:
        return get_studio_utente(request)

    except Exception:
        return None