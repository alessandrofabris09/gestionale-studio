from .models import ProfiloUtente, Studio


def get_studio_utente(request):
    """
    Restituisce lo studio collegato all'utente loggato.

    Utente normale:
    - restituisce lo studio collegato al ProfiloUtente.

    Superuser:
    - se ha un ProfiloUtente, restituisce quello studio;
    - se non ha un ProfiloUtente, restituisce il primo Studio attivo.

    Questo evita errori 500 nelle viste operative quando l'admin tecnico
    non è collegato direttamente a uno studio.
    """

    if not request:
        return None

    if not hasattr(request, 'user'):
        return None

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

        if request.user.is_superuser:

            return Studio.objects.filter(
                attivo=True
            ).order_by(
                'id'
            ).first()

        return None


def studio_is_pro(studio):
    """
    Verifica se lo studio ha piano PRO attivo.
    """

    if not studio:
        return False

    return studio.is_pro()


def studio_puo_creare_pratiche(studio):
    """
    Verifica se lo studio può creare nuove pratiche.

    Piano PRO:
    - nessun limite.

    Piano FREE:
    - limite basato su studio.limite_pratiche.
    """

    if not studio:
        return False

    if studio.is_pro():
        return True

    from pratiche.models import Pratica

    totale_pratiche = Pratica.objects.filter(
        studio=studio
    ).count()

    return totale_pratiche < studio.limite_pratiche


def studio_puo_aggiungere_utenti(studio):
    """
    Verifica se lo studio può aggiungere nuovi utenti.

    Piano PRO:
    - nessun limite.

    Piano FREE:
    - limite basato su studio.limite_utenti.
    """

    if not studio:
        return False

    if studio.is_pro():
        return True

    totale_utenti = studio.utenti.count()

    return totale_utenti < studio.limite_utenti


def studio_abbonamento_valido(studio):
    """
    Verifica se lo studio ha abbonamento valido.
    """

    if not studio:
        return False

    return studio.abbonamento_attivo()


def studio_deve_upgrade(studio):
    """
    Verifica se lo studio deve passare a PRO.
    """

    if not studio:
        return True

    if studio.is_pro():
        return False

    if studio.stato_abbonamento == 'TRIAL':
        return not studio.trial_attivo()

    return False


def studio_storage_usato_mb(studio):
    """
    Calcola lo storage documenti usato dallo studio in MB.

    Nota:
    Il related_name corretto del modello Pratica verso Studio è 'pratiche',
    quindi si usa studio.pratiche e non studio.pratica_set.
    """

    if not studio:
        return 0

    totale = 0

    pratiche = studio.pratiche.prefetch_related(
        'documenti'
    )

    for pratica in pratiche:

        for documento in pratica.documenti.all():

            if documento.file:

                try:
                    totale += documento.file.size
                except Exception:
                    pass

    return totale / (1024 * 1024)


def studio_puo_caricare_file(studio, nuovo_file_size=0):
    """
    Verifica se lo studio può caricare un nuovo file.

    Piano PRO:
    - nessun limite.

    Piano FREE:
    - limite basato su studio.limite_storage_mb.
    """

    if not studio:
        return False

    if studio.is_pro():
        return True

    storage_attuale = studio_storage_usato_mb(studio)

    nuovo_file_mb = nuovo_file_size / (1024 * 1024)

    totale = storage_attuale + nuovo_file_mb

    return totale <= studio.limite_storage_mb