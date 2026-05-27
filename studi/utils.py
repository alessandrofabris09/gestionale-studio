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


def studio_abbonamento_valido(studio):

    if not studio:
        return False

    return studio.abbonamento_attivo()


def studio_deve_upgrade(studio):

    if not studio:
        return True

    if studio.is_pro():
        return False

    if studio.stato_abbonamento == 'TRIAL':

        return not studio.trial_attivo()

    return False

def studio_storage_usato_mb(studio):

    if not studio:
        return 0

    totale = 0

    for documento in studio.pratica_set.prefetch_related(
        'documenti'
    ):

        for file in documento.documenti.all():

            if file.file:

                try:
                    totale += file.file.size
                except Exception:
                    pass

    return totale / (1024 * 1024)


def studio_puo_caricare_file(studio, nuovo_file_size=0):

    if not studio:
        return False

    if studio.is_pro():
        return True

    storage_attuale = studio_storage_usato_mb(studio)

    nuovo_file_mb = nuovo_file_size / (1024 * 1024)

    totale = storage_attuale + nuovo_file_mb

    return totale <= studio.limite_storage_mb