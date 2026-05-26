from .models import ProfiloUtente


def get_studio_utente(request):

    if not request.user.is_authenticated:
        return None

    try:

        profilo = ProfiloUtente.objects.select_related(
            'studio'
        ).get(
            user=request.user
        )

        return profilo.studio

    except ProfiloUtente.DoesNotExist:

        return None


def studio_is_pro(studio):

    if not studio:
        return False

    return studio.is_pro()


def studio_puo_creare_pratiche(studio):

    if not studio:
        return False

    if studio.is_pro():
        return True

    totale_pratiche = studio.pratica_set.count()

    return totale_pratiche < studio.limite_pratiche


def studio_puo_aggiungere_utenti(studio):

    if not studio:
        return False

    if studio.is_pro():
        return True

    totale_utenti = studio.utenti.count()

    return totale_utenti < studio.limite_utenti