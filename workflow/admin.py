from django.contrib import admin

from .models import (
    TipoWorkflow,
    FaseWorkflow,
    ChecklistWorkflow,
    WorkflowPratica,
    FasePratica,
    ChecklistPratica,
)


class FaseWorkflowInline(admin.TabularInline):
    model = FaseWorkflow
    extra = 1


class ChecklistWorkflowInline(admin.TabularInline):
    model = ChecklistWorkflow
    extra = 1


@admin.register(TipoWorkflow)
class TipoWorkflowAdmin(admin.ModelAdmin):

    list_display = (
        'nome',
        'categoria',
        'attivo',
        'ordine',
    )

    list_filter = (
        'categoria',
        'attivo',
    )

    search_fields = (
        'nome',
        'descrizione',
    )

    inlines = [
        FaseWorkflowInline,
        ChecklistWorkflowInline,
    ]


@admin.register(WorkflowPratica)
class WorkflowPraticaAdmin(admin.ModelAdmin):

    list_display = (
        'pratica',
        'workflow',
        'data_attivazione',
        'completato',
    )

    list_filter = (
        'workflow',
        'completato',
    )


@admin.register(FasePratica)
class FasePraticaAdmin(admin.ModelAdmin):

    list_display = (
        'titolo',
        'workflow_pratica',
        'completata',
        'data_scadenza',
    )


@admin.register(ChecklistPratica)
class ChecklistPraticaAdmin(admin.ModelAdmin):

    list_display = (
        'voce',
        'workflow_pratica',
        'completato',
        'obbligatorio',
    )