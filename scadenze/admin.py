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
    )

    list_filter = (
        'priorita',
        'completata',
    )

    search_fields = (
        'titolo',
        'pratica__oggetto',
    )