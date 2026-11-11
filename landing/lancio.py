from datetime import timedelta

from django.conf import settings
from django.db import transaction
from django.utils import timezone

from studi.models import Studio

from .models import IscrizioneFreeLancio

OBIETTIVO_ISCRIZIONI_FREE = 100
POSTI_BETA_LANCIO = 15
MESI_BETA_LANCIO = 6


@transaction.atomic
def crea_studio_free(**dati):
    lancio = settings.LANCIO_BETA_FREE
    studio = Studio.objects.create(
        **dati,
        piano='FREE',
        stato_abbonamento='ATTIVO' if lancio else 'TRIAL',
        trial_fino_al=None if lancio else timezone.now().date() + timedelta(days=14),
        limite_utenti=1,
        limite_storage_mb=500,
    )
    if lancio:
        IscrizioneFreeLancio.objects.create(studio=studio)
    return studio
