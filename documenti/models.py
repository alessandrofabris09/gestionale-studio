from django.db import models
from pratiche.models import Pratica


TIPI_DOCUMENTO = [
    ('TAVOLA', 'Tavola grafica'),
    ('RELAZIONE', 'Relazione tecnica'),
    ('MODELLO', 'Modello pratica'),
    ('RICEVUTA', 'Ricevuta / Protocollo'),
    ('FOTO', 'Foto'),
    ('PEC', 'PEC'),
    ('ALTRO', 'Altro'),
]


class Documento(models.Model):
    pratica = models.ForeignKey(
        Pratica,
        on_delete=models.CASCADE,
        related_name='documenti'
    )

    titolo = models.CharField(max_length=255)

    tipo_documento = models.CharField(
        max_length=50,
        choices=TIPI_DOCUMENTO,
        default='ALTRO'
    )

    file = models.FileField(upload_to='documenti_pratiche/')

    note = models.TextField(blank=True)

    caricato_il = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.titolo