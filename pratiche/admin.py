from django.contrib import admin
from .models import Pratica


@admin.register(Pratica)
class PraticaAdmin(admin.ModelAdmin):

    list_display = (
        'id',
        'tipo_pratica',
        'oggetto',
        'cliente',
        'comune',
        'stato',
        'scadenza',
    )

    list_filter = (
        'tipo_pratica',
        'stato',
        'comune',
    )

    search_fields = (
        'oggetto',
        'cliente__nome',
        'protocollo',
        'comune',
    )

    ordering = ('-id',)