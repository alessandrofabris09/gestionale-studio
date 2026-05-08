from django.contrib import admin
from .models import Documento


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = (
        'titolo',
        'pratica',
        'tipo_documento',
        'caricato_il',
    )

    list_filter = (
        'tipo_documento',
    )

    search_fields = (
        'titolo',
        'pratica__oggetto',
    )