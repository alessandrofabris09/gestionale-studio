from django.db import models
from pratiche.models import Pratica


PRIORITA = [
    ('BASSA', 'Bassa'),
    ('MEDIA', 'Media'),
    ('ALTA', 'Alta'),
]


class Scadenza(models.Model):

    pratica = models.ForeignKey(
        Pratica,
        on_delete=models.CASCADE,
        related_name='scadenze'
    )

    titolo = models.CharField(max_length=255)

    descrizione = models.TextField(blank=True)

    data_scadenza = models.DateField()

    priorita = models.CharField(
        max_length=20,
        choices=PRIORITA,
        default='MEDIA'
    )

    completata = models.BooleanField(default=False)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titolo