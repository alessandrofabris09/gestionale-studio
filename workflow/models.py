from django.db import models

from pratiche.models import Pratica


CATEGORIE_WORKFLOW = [
    ('EDILIZIA', 'Edilizia'),
    ('CATASTO', 'Catasto'),
    ('ENERGIA', 'Energia'),
    ('PRATICHE_IMMOBILIARI_NOTARILI', 'Pratiche immobiliari e notarili'),
    ('STRUTTURE', 'Strutture'),
    ('AMBIENTE', 'Ambiente'),
    ('SICUREZZA_CANTIERI', 'Sicurezza cantieri'),
    ('CONTABILITA', 'Contabilità'),
    ('ALTRO', 'Altro'),
]


class TipoWorkflow(models.Model):

    categoria = models.CharField(
        max_length=50,
        choices=CATEGORIE_WORKFLOW
    )

    nome = models.CharField(max_length=255)

    descrizione = models.TextField(blank=True)

    attivo = models.BooleanField(default=True)

    ordine = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.get_categoria_display()} - {self.nome}'


class FaseWorkflow(models.Model):

    workflow = models.ForeignKey(
        TipoWorkflow,
        on_delete=models.CASCADE,
        related_name='fasi'
    )

    titolo = models.CharField(max_length=255)

    descrizione = models.TextField(blank=True)

    ordine = models.PositiveIntegerField(default=0)

    giorni_scadenza = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text='Giorni dopo la creazione pratica'
    )

    def __str__(self):
        return f'{self.workflow.nome} - {self.titolo}'


class ChecklistWorkflow(models.Model):

    workflow = models.ForeignKey(
        TipoWorkflow,
        on_delete=models.CASCADE,
        related_name='checklist'
    )

    voce = models.CharField(max_length=255)

    descrizione = models.TextField(blank=True)

    obbligatorio = models.BooleanField(default=True)

    ordine = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f'{self.workflow.nome} - {self.voce}'


class WorkflowPratica(models.Model):

    pratica = models.OneToOneField(
        Pratica,
        on_delete=models.CASCADE,
        related_name='workflow_pratica'
    )

    workflow = models.ForeignKey(
        TipoWorkflow,
        on_delete=models.SET_NULL,
        null=True,
        blank=True
    )

    data_attivazione = models.DateField(auto_now_add=True)

    completato = models.BooleanField(default=False)

    note = models.TextField(blank=True)

    def __str__(self):
        return f'{self.pratica} - {self.workflow}'


class FasePratica(models.Model):

    workflow_pratica = models.ForeignKey(
        WorkflowPratica,
        on_delete=models.CASCADE,
        related_name='fasi_pratica'
    )

    titolo = models.CharField(max_length=255)

    descrizione = models.TextField(blank=True)

    ordine = models.PositiveIntegerField(default=0)

    completata = models.BooleanField(default=False)

    data_scadenza = models.DateField(
        null=True,
        blank=True
    )

    def __str__(self):
        return self.titolo


class ChecklistPratica(models.Model):

    workflow_pratica = models.ForeignKey(
        WorkflowPratica,
        on_delete=models.CASCADE,
        related_name='checklist_pratica'
    )

    voce = models.CharField(max_length=255)

    descrizione = models.TextField(blank=True)

    obbligatorio = models.BooleanField(default=True)

    completato = models.BooleanField(default=False)

    ordine = models.PositiveIntegerField(default=0)

    def __str__(self):
        return self.voce