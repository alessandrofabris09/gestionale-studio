from django.db import models
from django.contrib.auth.models import User


TIPI_AZIONE = [
    ('CREAZIONE', 'Creazione'),
    ('MODIFICA', 'Modifica'),
    ('ELIMINAZIONE', 'Eliminazione'),
    ('UPLOAD', 'Upload documento'),
    ('PDF', 'Generazione PDF'),
    ('ALTRO', 'Altro'),
]


class Attivita(models.Model):
    utente = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    tipo = models.CharField(
        max_length=30,
        choices=TIPI_AZIONE,
        default='ALTRO'
    )

    descrizione = models.CharField(max_length=255)

    data = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.descrizione