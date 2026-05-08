from django.contrib import admin
from .models import Attivita


@admin.register(Attivita)
class AttivitaAdmin(admin.ModelAdmin):
    list_display = (
        'data',
        'utente',
        'tipo',
        'descrizione',
    )

    list_filter = (
        'tipo',
        'data',
    )

    search_fields = (
        'descrizione',
        'utente__username',
    )

    ordering = ('-data',)