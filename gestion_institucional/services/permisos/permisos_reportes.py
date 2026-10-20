from functools import wraps

from django.http import HttpResponseForbidden

from inicio_sesion.models import Cuenta


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

            # Obtener el rol principal desde la BD
            rol_principal = cuenta.obtener_rol_principal()

            # Verificar autorización
            if rol_principal not in roles_permitidos:
                return HttpResponseForbidden(
                    "No tienes permisos para acceder a este reporte."
                )

            return vista(request, *args, **kwargs)

        return envoltura

    return decorador