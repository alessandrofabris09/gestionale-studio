from django.contrib import admin
from .models import Cliente


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):

    list_display = (
        'nome',
        'telefono',
        'email',
        'partita_iva',
    )

    search_fields = (
        'nome',
        'email',
        'partita_iva',
        'codice_fiscale',
    )