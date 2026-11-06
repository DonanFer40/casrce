from django.contrib import admin
from .models import RegistroAccion


@admin.register(RegistroAccion)
class RegistroAccionAdmin(admin.ModelAdmin):
    list_display = (
        "fecha_hora", "nombre_usuario", "rol", "accion",
        "modulo", "resultado", "direccion_ip",
    )
    list_filter = ("categoria", "resultado", "nivel", "rol", "fecha_hora")
    search_fields = ("nombre_usuario", "cedula_usuario", "accion", "modulo", "descripcion")
    ordering = ("-fecha_hora",)
    readonly_fields = [field.name for field in RegistroAccion._meta.fields]

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
