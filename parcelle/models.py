from decimal import Decimal

from django.db import models
from django.utils import timezone

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

    note = models.TextField(
        blank=True
    )

    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = [
            '-data_emissione',
            '-created_at',
            '-id',
        ]

    def save(self, *args, **kwargs):
        """
        Compila automaticamente:
        - numero documento, se mancante
        - data emissione, se mancante
        - stato pagamento in base agli importi
        """

        if not self.data_emissione:
            self.data_emissione = timezone.now().date()

        if not self.numero_documento or self.numero_documento.strip() == '':

            anno = timezone.now().year

            prefisso = self.get_prefisso_documento()

            ultimo_numero = Parcella.objects.filter(
                tipo_documento=self.tipo_documento,
                data_emissione__year=anno
            ).count() + 1

            self.numero_documento = (
                f'{prefisso}-{anno}-{ultimo_numero:04d}'
            )

        self.aggiorna_stato_pagamento()

        super().save(*args, **kwargs)

    def get_prefisso_documento(self):
        """
        Restituisce il prefisso corretto in base al tipo documento.
        """

        if self.tipo_documento == 'PREVENTIVO':
            return 'PRE'

        if self.tipo_documento == 'PARCELLA':
            return 'PAR'

        if self.tipo_documento == 'FATTURA':
            return 'FAT'

        return 'DOC'

    @property
    def imponibile(self):
        """
        Importo senza IVA.
        """

        return self.importo or Decimal('0.00')

    @property
    def importo_iva(self):
        """
        Importo IVA calcolato sull'imponibile.
        """

        imponibile = self.imponibile
        iva = self.iva or Decimal('0.00')

        return imponibile * iva / Decimal('100.00')

    @property
    def totale_con_iva(self):
        """
        Totale documento IVA compresa.
        """

        return self.imponibile + self.importo_iva

    @property
    def saldo_residuo(self):
        """
        Importo ancora da incassare.
        """

        pagato = self.importo_pagato or Decimal('0.00')

        return self.totale_con_iva - pagato

    def aggiorna_stato_pagamento(self):
        """
        Aggiorna automaticamente lo stato del pagamento.
        """

        pagato = self.importo_pagato or Decimal('0.00')
        totale = self.totale_con_iva

        if pagato <= Decimal('0.00'):
            self.stato = 'DA_PAGARE'

        elif pagato < totale:
            self.stato = 'PARZIALE'

        else:
            self.stato = 'PAGATO'

            if not self.data_pagamento:
                self.data_pagamento = timezone.now().date()

    def __str__(self):
        numero = (
            self.numero_documento
            if self.numero_documento
            else 'Documento non numerato'
        )

        return f'{numero} - {self.descrizione}'