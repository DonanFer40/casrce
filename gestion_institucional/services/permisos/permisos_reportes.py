from functools import wraps

from django.http import HttpResponseForbidden

from inicio_sesion.models import (
    ControlEstudio,
    CoordinadorPNF,
    Cuenta,
    DirectorGeneral,
    Docente,
    Estudiante,
)


def obtener_roles_reporte(usuario):
    roles = set()
    if Estudiante.objects.filter(usuario=usuario).exists():
        roles.add("Estudiante")
    if Docente.objects.filter(usuario=usuario, activo=True).exists():
        roles.add("Docente")
    if CoordinadorPNF.objects.filter(usuario=usuario, activo=True).exists():
        roles.add("Coordinador PNF")
    if ControlEstudio.objects.filter(usuario=usuario, activo=True).exists():
        roles.add("Control de Estudio")
    if DirectorGeneral.objects.filter(usuario=usuario).exists():
        roles.add("Director General")
    return roles


def requiere_rol_reporte(*roles_permitidos):
    """
    Protege las vistas de reportes según el rol real
    registrado para la cuenta del usuario.
    """

    def decorador(vista):

        @wraps(vista)
        def envoltura(request, *args, **kwargs):

            id_cuenta = request.session.get("id_cuenta")

            # No existe una sesión válida
            if not id_cuenta:
                return HttpResponseForbidden(
                    "Acceso denegado."
                )

            # Buscar la cuenta directamente en la BD
            cuenta = (
                Cuenta.objects
                .select_related("id_usuario")
                .filter(id_cuenta=id_cuenta)
                .first()
            )

            # La cuenta no existe
            if not cuenta:
                return HttpResponseForbidden(
                    "Acceso denegado."
                )

            roles = obtener_roles_reporte(cuenta.id_usuario)

            # Verificar autorización
            if not roles.intersection(roles_permitidos):
                return HttpResponseForbidden(
                    "No tienes permisos para acceder a este reporte."
                )

            return vista(request, *args, **kwargs)

        return envoltura

    return decorador