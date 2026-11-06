
from django.contrib import admin

from .models import DocumentoInstitucional


@admin.register(DocumentoInstitucional)
class DocumentoInstitucionalAdmin(admin.ModelAdmin):

    list_display = (
        "codigo_documento",
        "tipo_documento",
        "titulo",
        "fecha_emision",
        "estado",
    )

    list_filter = (
        "estado",
        "tipo_documento",
        "fecha_emision",
    )

    search_fields = (
        "codigo_documento",
        "titulo",
        "tipo_documento",
    )

    readonly_fields = (
        "identificador",
        "codigo_documento",
        "fecha_emision",
        "fecha_anulacion",
    )

    ordering = ("-fecha_emision",)
