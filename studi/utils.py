from gestionale.beta_pro import QUOTA_BETA_MB

from .models import ProfiloUtente, Studio


def get_studio_utente(request):
    """
    Restituisce lo studio collegato all'utente loggato.

    Utente normale:
    - restituisce lo studio collegato al ProfiloUtente.

    Superuser con profilo: restituisce il proprio studio.
    Amministratore della piattaforma senza profilo: restituisce None.
    """

    if not request:
        return None

    if not hasattr(request, 'user'):
        return None

    if not request.user.is_authenticated:
        return None

    if hasattr(request, '_studio_corrente'):
        return request._studio_corrente
    try:
        profilo = ProfiloUtente.objects.select_related('studio__beta_pro').get(
            user=request.user
        )
        request._studio_corrente = profilo.studio
    except ProfiloUtente.DoesNotExist:
        # Un amministratore della piattaforma non viene assegnato
        # automaticamente allo studio di un altro professionista.
        request._studio_corrente = None
    return request._studio_corrente


def is_admin_piattaforma(request):
    """
    Amministratore Django senza profilo associato a uno studio.
    Gli eventuali superuser con profilo restano confinati al proprio studio.
    """
    return bool(
        request
        and getattr(request, 'user', None)
        and request.user.is_authenticated
        and request.user.is_superuser
        and not ProfiloUtente.objects.filter(user=request.user).exists()
    )


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


def studio_storage_usato_mb(studio, *, rigoroso=False):
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
                    if rigoroso:
                        raise

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

    if studio.fase_beta():
        # Le viste di upload mantengono il blocco fino al salvataggio.
        studio = Studio.objects.select_for_update().get(pk=studio.pk)
        fase = studio.fase_beta()
        if fase == 'ATTIVA':
            try:
                usati = studio_storage_usato_mb(studio, rigoroso=True)
            except Exception:
                return False
            return usati + nuovo_file_size / (1024 * 1024) <= QUOTA_BETA_MB
        if fase in ('LETTURA', 'CHIUSA'):
            return False

    if studio.is_pro():
        return True

    storage_attuale = studio_storage_usato_mb(studio)

    nuovo_file_mb = nuovo_file_size / (1024 * 1024)

    totale = storage_attuale + nuovo_file_mb

    return totale <= studio.limite_storage_mb
