from django.conf import settings
from django.db import models
from django.utils import timezone


class RegistroAccion(models.Model):
    CATEGORIAS = [
        ("AUTENTICACION", "Autenticación"),
        ("USUARIOS", "Gestión de usuarios"),
        ("ACADEMICO", "Gestión académica"),
        ("INSTITUCIONAL", "Gestión institucional"),
        ("DOCUMENTOS", "Documentos y reportes"),
        ("SEGURIDAD", "Seguridad"),
        ("SISTEMA", "Sistema"),
        ("OTRO", "Otro"),
    ]
    RESULTADOS = [
        ("EXITOSO", "Exitoso"),
        ("FALLIDO", "Fallido"),
        ("RECHAZADO", "Rechazado"),
        ("PENDIENTE", "Pendiente"),
    ]
    NIVELES = [
        ("INFO", "Informativo"),
        ("ADVERTENCIA", "Advertencia"),
        ("CRITICO", "Crítico"),
    ]

    id_registro = models.BigAutoField(primary_key=True)
    usuario = models.ForeignKey(
        "inicio_sesion.Usuario",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="acciones_bitacora",
    )
    nombre_usuario = models.CharField(max_length=201, blank=True)
    cedula_usuario = models.CharField(max_length=15, blank=True)
    rol = models.CharField(max_length=60, blank=True)
    categoria = models.CharField(max_length=20, choices=CATEGORIAS, default="OTRO", db_index=True)
    modulo = models.CharField(max_length=100, db_index=True)
    accion = models.CharField(max_length=120, db_index=True)
    descripcion = models.TextField()
    resultado = models.CharField(max_length=12, choices=RESULTADOS, default="EXITOSO", db_index=True)
    nivel = models.CharField(max_length=12, choices=NIVELES, default="INFO")
    tipo_objeto = models.CharField(max_length=100, blank=True)
    identificador_objeto = models.CharField(max_length=100, blank=True)
    direccion_ip = models.GenericIPAddressField(null=True, blank=True)
    ruta = models.CharField(max_length=500, blank=True)
    metodo_http = models.CharField(max_length=10, blank=True)
    detalles = models.JSONField(default=dict, blank=True)
    fecha_hora = models.DateTimeField(default=timezone.now, editable=False, db_index=True)

    class Meta:
        ordering = ["-fecha_hora", "-id_registro"]
        verbose_name = "Registro de bitácora"
        verbose_name_plural = "Registros de bitácora"
        indexes = [
            models.Index(fields=["categoria", "fecha_hora"], name="bitacora_cat_fecha_idx"),
            models.Index(fields=["resultado", "fecha_hora"], name="bitacora_res_fecha_idx"),
            models.Index(fields=["rol", "fecha_hora"], name="bitacora_rol_fecha_idx"),
        ]

    def __str__(self):
        return f"{self.accion} - {self.nombre_usuario or 'Sistema'} - {self.fecha_hora:%d/%m/%Y %H:%M}"

    def save(self, *args, **kwargs):
        if self.pk and type(self).objects.filter(pk=self.pk).exists():
            raise ValueError("Los registros de bitácora son inmutables.")
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise ValueError("Los registros de bitácora no pueden eliminarse.")
