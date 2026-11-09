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

    workflow_origine = models.ForeignKey(
        'workflow.WorkflowPratica',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='scadenze_generate',
        editable=False,
    )
    fase_origine = models.OneToOneField(
        'workflow.FasePratica', on_delete=models.SET_NULL,
        null=True, blank=True, editable=False, related_name='scadenza_generata',
    )
    archiviata = models.BooleanField(default=False, editable=False)
    da_pratica = models.BooleanField(default=False, editable=False)

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

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['pratica'], condition=models.Q(da_pratica=True),
                name='scadenza_automatica_unica_per_pratica',
            ),
        ]

    def __str__(self):
        return self.titolo
