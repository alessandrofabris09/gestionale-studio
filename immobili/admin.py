from django.contrib import admin
from .models import Immobile


@admin.register(Immobile)
class ImmobileAdmin(admin.ModelAdmin):

    list_display = (
        'comune',
        'indirizzo',
        'foglio',
        'mappale',
        'cliente',
    )

    search_fields = (
        'comune',
        'indirizzo',
        'foglio',
        'mappale',
    )

    list_filter = (
        'comune',
    )