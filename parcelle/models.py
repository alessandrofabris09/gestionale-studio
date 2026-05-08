from django.db import models
from pratiche.models import Pratica


STATO_PAGAMENTO = [
    ('DA_PAGARE', 'Da pagare'),
    ('PARZIALE', 'Parziale'),
    ('PAGATO', 'Pagato'),
]


class Parcella(models.Model):
    pratica = models.ForeignKey(
        Pratica,
        on_delete=models.CASCADE,
        related_name='parcelle'
    )

    descrizione = models.CharField(max_length=255)

    importo = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    importo_pagato = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    data_emissione = models.DateField(
        null=True,
        blank=True
    )

    data_pagamento = models.DateField(
        null=True,
        blank=True
    )

    stato = models.CharField(
        max_length=20,
        choices=STATO_PAGAMENTO,
        default='DA_PAGARE'
    )

    note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def saldo_residuo(self):
        return self.importo - self.importo_pagato

    def __str__(self):
        return f"{self.descrizione} - {self.pratica}"