import uuid
from datetime import timedelta

from django.db import models
from django.utils import timezone

OBIETTIVO_PRO = 100
VERSIONE_CONSENSO = 'demo-pro-v2'
DURATA_RICHIESTA = timedelta(hours=24)
DURATA_CONSENSO = timedelta(days=365)


class RichiestaPro(models.Model):
    email = models.EmailField(unique=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    token_revoca = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    versione_consenso = models.CharField(max_length=32)
    richiesta_il = models.DateTimeField(default=timezone.now)
    confermata_il = models.DateTimeField(null=True, blank=True, db_index=True)

    @classmethod
    def confermate_attive(cls):
        return cls.objects.filter(
            versione_consenso=VERSIONE_CONSENSO,
            confermata_il__gt=timezone.now() - DURATA_CONSENSO,
        )
