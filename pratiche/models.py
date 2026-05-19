from django.db import models
from clienti.models import Cliente
from immobili.models import Immobile


TIPI_PRATICA = [
    ('CILA', 'CILA'),
    ('SCIA', 'SCIA'),
    ('PDC', 'Permesso di Costruire'),
    ('SANATORIA', 'Sanatoria'),
    ('PAESAGGISTICA', 'Paesaggistica'),
    ('CATASTO', 'Catasto'),
    ('FRAZIONAMENTO', 'Frazionamento'),
    ('SUCCESSIONE', 'Successione'),
    ('APE', 'APE'),
    ('PERIZIA', 'Perizia'),
]


STATI_PRATICA = [
    ('PREVENTIVO', 'Preventivo'),
    ('IN CORSO', 'In corso'),
    ('DEPOSITATA', 'Depositata'),
    ('INTEGRAZIONE', 'Integrazione'),
    ('APPROVATA', 'Approvata'),
    ('CONCLUSA', 'Conclusa'),
]


class Pratica(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    immobile = models.ForeignKey(Immobile, on_delete=models.CASCADE)

    tipo_pratica = models.CharField(
    max_length=255
    )

    stato = models.CharField(
        max_length=50,
        choices=STATI_PRATICA,
        default='IN_CORSO'
    )

    oggetto = models.CharField(max_length=255)

    comune = models.CharField(max_length=150)

    protocollo = models.CharField(
        max_length=100,
        blank=True
    )

    data_incarico = models.DateField(null=True, blank=True)

    data_deposito = models.DateField(null=True, blank=True)

    scadenza = models.DateField(null=True, blank=True)

    compenso = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )

    note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo_pratica} - {self.oggetto}"