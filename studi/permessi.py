def get_profilo(request):
    """
    Recupera il profilo studio dell'utente loggato.
    Se l'utente non è autenticato o non ha profilo, restituisce None.
    """

    if not request:
        return None

    if not hasattr(request, "user"):
        return None

    if not request.user.is_authenticated:
        return None

    try:
        return request.user.profilo_studio
    except Exception:
        return None


def get_ruolo(request):
    """
    Recupera il ruolo dell'utente.
    Restituisce None se non esiste un profilo studio.
    """

    profilo = get_profilo(request)

    if not profilo:
        return None

    return profilo.ruolo


def is_superuser(request):
    """
    Controlla se l'utente è superuser Django.
    Il superuser deve poter accedere a tutto.
    """

    if not request:
        return False

    if not hasattr(request, "user"):
        return False

    return request.user.is_authenticated and request.user.is_superuser


def is_titolare(request):

    return get_ruolo(request) == "TITOLARE"


def is_tecnico(request):

    return get_ruolo(request) == "TECNICO"


def is_segreteria(request):

    return get_ruolo(request) == "SEGRETERIA"


def is_collaboratore(request):

    return get_ruolo(request) == "COLLABORATORE"


def puo_gestire_utenti(request):
    """
    Gestione utenti visibile solo a:
    - superuser
    - TITOLARE
    """

    return (
        is_superuser(request) or
        is_titolare(request)
    )


def puo_gestire_abbonamento(request):
    """
    Gestione abbonamento visibile solo a:
    - superuser
    - TITOLARE
    """

    return (
        is_superuser(request) or
        is_titolare(request)
    )


def puo_creare_pratiche(request):
    """
    Creazione pratiche consentita a:
    - superuser
    - TITOLARE
    - TECNICO
    """

    return (
        is_superuser(request) or
        is_titolare(request) or
        is_tecnico(request)
    )


def puo_modificare_pratiche(request):
    """
    Modifica pratiche consentita a:
    - superuser
    - TITOLARE
    - TECNICO
    """

    return (
        is_superuser(request) or
        is_titolare(request) or
        is_tecnico(request)
    )


def puo_eliminare_pratiche(request):
    """
    Eliminazione pratiche consentita solo a:
    - superuser
    - TITOLARE
    """

    return (
        is_superuser(request) or
        is_titolare(request)
    )


def puo_vedere_parcelle(request):
    """
    Visualizzazione parcelle consentita a:
    - superuser
    - TITOLARE
    - SEGRETERIA
    """

    return (
        is_superuser(request) or
        is_titolare(request) or
        is_segreteria(request)
    )


def puo_modificare_parcelle(request):
    """
    Modifica parcelle consentita a:
    - superuser
    - TITOLARE
    - SEGRETERIA
    """

    return (
        is_superuser(request) or
        is_titolare(request) or
        is_segreteria(request)
    )


def puo_eliminare_parcelle(request):
    """
    Eliminazione parcelle consentita solo a:
    - superuser
    - TITOLARE
    """

    return (
        is_superuser(request) or
        is_titolare(request)
    )


def puo_gestire_documenti(request):
    """
    Gestione documenti consentita a:
    - superuser
    - TITOLARE
    - TECNICO
    - SEGRETERIA
    """

    return (
        is_superuser(request) or
        is_titolare(request) or
        is_tecnico(request) or
        is_segreteria(request)
    )


def puo_gestire_backup(request):
    """
    Backup database consentito solo a:
    - superuser
    - TITOLARE
    """

    return (
        is_superuser(request) or
        is_titolare(request)
    )


def puo_usare_agenda(request):
    """
    Agenda e scadenze consentite a:
    - superuser
    - TITOLARE
    - TECNICO
    - SEGRETERIA
    - COLLABORATORE

    Il collaboratore vede solo agenda/scadenze e non vede pratiche,
    documenti, parcelle, utenti o abbonamento.
    """

    return (
        is_superuser(request) or
        is_titolare(request) or
        is_tecnico(request) or
        is_segreteria(request) or
        is_collaboratore(request)
    )


def puo_gestire_alert(request):
    """
    Gestione alert scadenze consentita a:
    - superuser
    - TITOLARE
    - TECNICO

    Non consentita a:
    - SEGRETERIA
    - COLLABORATORE
    """

    return (
        is_superuser(request) or
        is_titolare(request) or
        is_tecnico(request)
    )