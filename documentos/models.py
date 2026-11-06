
import uuid

from django.db import models
from django.utils import timezone

from inicio_sesion.models import (
    Usuario,
    Estudiante,
    Materia,
    PeriodoAcademico,
    TrayectoAcademico,
)

from notas_academicas.models import (
    Calificaciones,
    PromedioFinal,
    PlanificacionAcademica,
)

class DocumentoInstitucional(models.Model):

    ESTADOS = [
        ("VIGENTE", "Vigente"),
        ("ANULADO", "Anulado"),
    ]

    identificador = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
    )

    codigo_documento = models.CharField(
        max_length=50,
        unique=True,
        editable=False,
        db_index=True,
    )

    tipo_documento = models.CharField(max_length=100)

    titulo = models.CharField(max_length=200)

    fecha_emision = models.DateTimeField(
        default=timezone.now,
        db_index=True,
    )

    estado = models.CharField(
        max_length=15,
        choices=ESTADOS,
        default="VIGENTE",
        db_index=True,
    )

    # Datos mínimos de identificación del documento.
    # No se deben exponer directamente en la página pública.
    datos_documento = models.JSONField(
        default=dict,
        blank=True,
    )

    archivo_pdf = models.FileField(
        upload_to="documentos_institucionales/",
        null=True,
        blank=True,
    )

    emitido_por = models.ForeignKey(
        Usuario,
        on_delete=models.PROTECT,
        related_name="documentos_emitidos",
        null=True,
        blank=True,
    )

    fecha_anulacion = models.DateTimeField(
        null=True,
        blank=True,
    )

    motivo_anulacion = models.TextField(
        blank=True,
    )

    class Meta:
        ordering = ["-fecha_emision"]
        verbose_name = "Documento institucional"
        verbose_name_plural = "Documentos institucionales"

    def save(self, *args, **kwargs):

        if not self.codigo_documento:
            identificador_corto = self.identificador.hex[:10].upper()

            self.codigo_documento = (
                f"CASRCE-{timezone.localdate().year}-"
                f"{identificador_corto}"
            )

        super().save(*args, **kwargs)

    def anular(self, motivo=""):

        self.estado = "ANULADO"
        self.fecha_anulacion = timezone.now()
        self.motivo_anulacion = motivo

        self.save(
            update_fields=[
                "estado",
                "fecha_anulacion",
                "motivo_anulacion",
            ]
        )

    def __str__(self):
        return f"{self.codigo_documento} - {self.titulo}"
