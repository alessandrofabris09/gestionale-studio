from datetime import timedelta

from dateutil.relativedelta import relativedelta
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.utils import timezone

from gestionale.beta_pro import GIORNI_ESPORTAZIONE_BETA, MESI_BETA, POSTI_BETA

from .models import BetaStudio, Studio


@transaction.atomic
def attiva_beta_pro(studio_id):
    studio = Studio.objects.select_for_update().get(pk=studio_id)
    esistente = BetaStudio.objects.filter(studio=studio).first()
    if esistente:
        return esistente, False

    if (
        not studio.attivo or studio.piano != 'FREE' or studio.stripe_subscription_id
        or studio.stripe_checkout_pending
    ):
        raise ValidationError('Lo studio deve essere attivo, sul piano Free e senza checkout o abbonamenti in corso.')
    if not studio.titolare.email or not studio.utenti.filter(user_id=studio.titolare_id, ruolo='TITOLARE').exists():
        raise ValidationError('Serve un titolare dello studio con un indirizzo email per gli avvisi.')

    oggi = timezone.localdate()
    fine_pro = oggi + relativedelta(months=MESI_BETA)
    occupati = set(BetaStudio.objects.values_list('posto', flat=True))
    for posto in range(1, POSTI_BETA + 1):
        if posto in occupati:
            continue
        try:
            with transaction.atomic():
                beta = BetaStudio.objects.create(
                    studio=studio, posto=posto, attivata_il=oggi, fine_pro_il=fine_pro,
                    fine_esportazione_il=fine_pro + timedelta(days=GIORNI_ESPORTAZIONE_BETA),
                )
        except IntegrityError:
            if not BetaStudio.objects.filter(posto=posto).exists():
                raise
        else:
            return beta, True

    raise ValidationError('Tutti i posti della beta sono già stati assegnati.')
