def get_profilo(request):

    if not request.user.is_authenticated:
        return None

    try:
        return request.user.profilo_studio

    except Exception:
        return None


def get_ruolo(request):

    profilo = get_profilo(request)

    if not profilo:
        return None

    return profilo.ruolo


def is_titolare(request):

    return get_ruolo(request) == 'TITOLARE'


def is_tecnico(request):

    return get_ruolo(request) == 'TECNICO'


def is_segreteria(request):

    return get_ruolo(request) == 'SEGRETERIA'


def is_collaboratore(request):

    return get_ruolo(request) == 'COLLABORATORE'


def puo_gestire_utenti(request):

    return is_titolare(request)


def puo_gestire_abbonamento(request):

    return is_titolare(request)


def puo_creare_pratiche(request):

    return is_titolare(request) or is_tecnico(request)


def puo_modificare_pratiche(request):

    return is_titolare(request) or is_tecnico(request)


def puo_eliminare_pratiche(request):

    return is_titolare(request)


def puo_vedere_parcelle(request):

    return (
        is_titolare(request) or
        is_segreteria(request)
    )


def puo_modificare_parcelle(request):

    return (
        is_titolare(request) or
        is_segreteria(request)
    )


def puo_eliminare_parcelle(request):

    return is_titolare(request)


def puo_gestire_documenti(request):

    return (
        is_titolare(request) or
        is_tecnico(request) or
        is_segreteria(request)
    )


def puo_gestire_backup(request):

    return is_titolare(request)


def puo_usare_agenda(request):

    return (
        is_titolare(request) or
        is_tecnico(request) or
        is_segreteria(request) or
        is_collaboratore(request)
    )