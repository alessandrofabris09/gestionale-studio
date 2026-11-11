from datetime import timedelta

from django.conf import settings
from django.core.mail import send_mail
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from django.utils import timezone

from gestionale.beta_pro import GIORNI_ESPORTAZIONE_BETA, GIORNI_PREAVVISO_BETA
from studi.models import BetaStudio


class Command(BaseCommand):
    help = 'Invia ai titolari l’avviso di scadenza della beta PRO.'

    def add_arguments(self, parser):
        parser.add_argument('--studio-id', type=int, help='Limita il controllo a uno studio.')

    def handle(self, *args, **options):
        oggi = timezone.localdate()
        candidati = BetaStudio.objects.filter(
            studio__attivo=True, avvisata_il__isnull=True, fine_pro_il__gt=oggi,
            fine_pro_il__lte=oggi + timedelta(days=GIORNI_PREAVVISO_BETA),
        )
        if options['studio_id'] is not None:
            candidati = candidati.filter(studio_id=options['studio_id'])
        inviati = 0
        errori = []
        for pk in list(candidati.values_list('pk', flat=True)):
            try:
                with transaction.atomic():
                    beta = BetaStudio.objects.select_for_update(of=('self',)).select_related('studio__titolare').get(pk=pk)
                    if beta.avvisata_il or not beta.studio or beta.studio.fase_beta() != 'ATTIVA':
                        continue
                    destinatario = beta.studio.titolare.email
                    if not destinatario:
                        raise ValueError('Recapito del titolare assente.')
                    offerta = settings.BETA_PRO_CONDIZIONI_USCITA or (
                        'Per conoscere prezzo e condizioni dell’eventuale abbonamento, '
                        'contatta info@studiotecnicocloud.it.'
                    )
                    inviato = send_mail(
                        'Scadenza della beta PRO di Studio Tecnico Cloud',
                        f'La prova PRO termina il {beta.fine_pro_il:%d/%m/%Y}. '
                        f'Seguiranno {GIORNI_ESPORTAZIONE_BETA} giorni in sola lettura per esportare i tuoi dati. '
                        f'{offerta} '
                        'Puoi vedere le date nella sezione Abbonamento del gestionale.',
                        settings.DEFAULT_FROM_EMAIL, [destinatario],
                    )
                    if not inviato:
                        raise ValueError('Invio non confermato.')
                    beta.avvisata_il = timezone.now()
                    beta.save(update_fields=['avvisata_il'])
                    inviati += 1
            except Exception as exc:
                errori.append(f'{pk} ({type(exc).__name__})')

        self.stdout.write(f'Avvisi inviati: {inviati}.')
        if errori:
            raise CommandError('Invio non riuscito per le ammissioni ' + ', '.join(errori))
