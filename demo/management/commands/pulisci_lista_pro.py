from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone

from demo.models import DURATA_CONSENSO, DURATA_RICHIESTA, RichiestaPro


class Command(BaseCommand):
    help = 'Elimina le richieste scadute e mostra il totale delle adesioni confermate.'

    def handle(self, *args, **options):
        now = timezone.now()
        deleted, _ = RichiestaPro.objects.filter(
            Q(confermata_il__isnull=True, richiesta_il__lte=now - DURATA_RICHIESTA)
            | Q(confermata_il__lte=now - DURATA_CONSENSO)
        ).delete()
        self.stdout.write(f'Richieste rimosse: {deleted}. Confermate attive: {RichiestaPro.confermate_attive().count()}.')
