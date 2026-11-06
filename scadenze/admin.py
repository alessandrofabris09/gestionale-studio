from django.contrib import admin
from .models import Scadenza


@admin.register(Scadenza)
class ScadenzaAdmin(admin.ModelAdmin):

    list_display = (
        'titolo',
        'pratica',
        'data_scadenza',
        'priorita',
        'completata',
        'archiviata',
    )

    list_filter = (
        'priorita',
        'completata',
        'archiviata',
    )

    readonly_fields = ('workflow_origine', 'archiviata')

    search_fields = (
        'titolo',
        'pratica__oggetto',
    )