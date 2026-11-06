from django.db import models

from clienti.models import Cliente
from studi.models import Studio


class Immobile(models.Model):

    studio = models.ForeignKey(
        Studio,
        on_delete=models.CASCADE,
        related_name='immobili'
    )

    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.CASCADE
    )

    comune = models.CharField(max_length=150)

    indirizzo = models.CharField(
        max_length=255,
        blank=True
    )

    foglio = models.CharField(
        max_length=50,
        blank=True
    )

    mappale = models.CharField(
        max_length=50,
        blank=True
    )

    subalterno = models.CharField(
        max_length=50,
        blank=True
    )

    categoria_catastale = models.CharField(
        max_length=50,
        blank=True
    )

    zona_urbanistica = models.CharField(
        max_length=100,
        blank=True
    )

    vincoli = models.TextField(blank=True)

    note = models.TextField(blank=True)

    def __str__(self):
        return f"{self.comune} - {self.indirizzo}"