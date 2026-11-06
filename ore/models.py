from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from pratiche.models import Pratica


class VoceOra(models.Model):

    TIPO_ATTIVITA = [
        ('SOPRALLUOGO', 'Sopralluogo'),
        ('RILIEVO', 'Rilievo'),
        ('PROGETTAZIONE', 'Progettazione'),
        ('DISEGNO', 'Disegno / elaborati grafici'),
        ('PRATICA', 'Gestione pratica'),
        ('INCONTRO', 'Incontro / riunione'),
        ('TELEFONATA', 'Telefonata / email'),
        ('ISTRUTTORIA', 'Istruttoria / verifica documentale'),
        ('CATASTO', 'Catasto'),
        ('DIREZIONE_LAVORI', 'Direzione lavori'),
        ('SICUREZZA', 'Sicurezza'),
        ('ALTRO', 'Altro'),
    ]

    pratica = models.ForeignKey(
        Pratica,
        on_delete=models.CASCADE,
        related_name='voci_ore'
    )

    utente = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='voci_ore'
    )

    data = models.DateField(
        default=timezone.now
    )

    tipo_attivita = models.CharField(
        max_length=30,
        choices=TIPO_ATTIVITA,
        default='ALTRO'
    )

    descrizione = models.TextField(
        blank=True
    )

    ore = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        default=Decimal('0.00')
    )

    tariffa_oraria = models.DecimalField(
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00')
    )

    fatturabile = models.BooleanField(
        default=True
    )

    inserita_in_parcella = models.BooleanField(
        default=False
    )

    note = models.TextField(
        blank=True
    )

    creata_il = models.DateTimeField(
        auto_now_add=True
    )

    aggiornata_il = models.DateTimeField(
        auto_now=True
    )

    class Meta:
        ordering = ['-data', '-id']
        verbose_name = 'Voce ore'
        verbose_name_plural = 'Voci ore'

    def __str__(self):
        return f'{self.pratica} - {self.data} - {self.ore} ore'

    @property
    def importo(self):
        ore = self.ore or Decimal('0.00')
        tariffa = self.tariffa_oraria or Decimal('0.00')
        return ore * tariffa