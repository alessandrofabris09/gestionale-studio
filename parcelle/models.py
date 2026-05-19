from django.db import models
from pratiche.models import Pratica


STATO_PAGAMENTO = [
    ('DA_PAGARE', 'Da pagare'),
    ('PARZIALE', 'Parziale'),
    ('PAGATO', 'Pagato'),
]


TIPO_DOCUMENTO = [
    ('PREVENTIVO', 'Preventivo'),
    ('PARCELLA', 'Parcella'),
    ('FATTURA', 'Fattura'),
]


class Parcella(models.Model):

    pratica = models.ForeignKey(
        Pratica,
        on_delete=models.CASCADE,
        related_name='parcelle'
    )

    tipo_documento = models.CharField(
        max_length=20,
        choices=TIPO_DOCUMENTO,
        default='PARCELLA'
    )

    numero_documento = models.CharField(
        max_length=50,
        blank=True
    )

    descrizione = models.CharField(
        max_length=255
    )

    importo = models.DecimalField(
        max_digits=10,
        decimal_places=2
    )

    importo_pagato = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0
    )

    iva = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        default=22
    )

    data_emissione = models.DateField(
        null=True,
        blank=True
    )

    data_scadenza = models.DateField(
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

    @property
    def saldo_residuo(self):

        importo = self.importo or 0
        pagato = self.importo_pagato or 0

        return importo - pagato    

    note = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

def save(self, *args, **kwargs):

    if not self.numero_documento or self.numero_documento.strip() == '':

        from datetime import datetime

        anno = datetime.now().year

        ultimo = Parcella.objects.filter(
            tipo_documento=self.tipo_documento
        ).count() + 1

        prefisso = ''

        if self.tipo_documento == 'PREVENTIVO':
            prefisso = 'PRE'

        elif self.tipo_documento == 'PARCELLA':
            prefisso = 'PAR'

        elif self.tipo_documento == 'FATTURA':
            prefisso = 'FAT'

        self.numero_documento = (
            f'{prefisso}-{anno}-{ultimo}'
        )

    super().save(*args, **kwargs)
    
    def totale_con_iva(self):
        return self.importo + (
            self.importo * self.iva / 100
        )

    def __str__(self):
        return f"{self.descrizione} - {self.pratica}"