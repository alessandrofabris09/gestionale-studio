from django.db import models
from django.contrib.auth.models import User

from clienti.models import Cliente
from pratiche.models import Pratica


TIPI_EVENTO = [
    ('APPUNTAMENTO', 'Appuntamento'),
    ('SOPRALLUOGO', 'Sopralluogo'),
    ('SCADENZA', 'Scadenza'),
    ('TELEFONATA', 'Telefonata'),
    ('RIUNIONE', 'Riunione'),
    ('ALTRO', 'Altro'),
]


PRIORITA = [
    ('BASSA', 'Bassa'),
    ('MEDIA', 'Media'),
    ('ALTA', 'Alta'),
]


class EventoAgenda(models.Model):

    titolo = models.CharField(max_length=255)

    tipo = models.CharField(
        max_length=30,
        choices=TIPI_EVENTO,
        default='APPUNTAMENTO'
    )

    priorita = models.CharField(
        max_length=20,
        choices=PRIORITA,
        default='MEDIA'
    )

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    pratica = models.ForeignKey(
        Pratica,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    assegnato_a = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    data = models.DateField()

    ora_inizio = models.TimeField(
        null=True,
        blank=True
    )

    ora_fine = models.TimeField(
        null=True,
        blank=True
    )

    completato = models.BooleanField(default=False)

    descrizione = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titolo