from functools import wraps

from django.http import JsonResponse, HttpResponseForbidden
from django.shortcuts import redirect

from inicio_sesion.models import Cuenta
from middleware.seguridad_roles import roles_reales_de_usuario


def requiere_roles(*roles_permitidos):
    """Protege una vista usando roles consultados en base de datos.

    Ejemplo:
        @requiere_roles("Director General", "Control de Estudio")
        def mi_vista(request): ...
    """
    permitidos = set(roles_permitidos)

    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            id_cuenta = request.session.get("id_cuenta")
            if not id_cuenta:
                if request.headers.get("Accept", "").startswith("application/json"):
                    return JsonResponse({"success": False, "message": "Debes iniciar sesión."}, status=401)
                return redirect("inicio_sesion")
            try:
                cuenta = Cuenta.objects.select_related("id_usuario").get(id_cuenta=id_cuenta)
            except Cuenta.DoesNotExist:
                request.session.flush()
                return redirect("inicio_sesion")
            roles = roles_reales_de_usuario(cuenta.id_usuario)
            if not roles.intersection(permitidos):
                return HttpResponseForbidden("No tienes permisos para realizar esta operación.")
            return vista(request, *args, **kwargs)
        return envoltura
    return decorador


def requiere_autenticacion(vista):
    """Exige una Cuenta válida en la sesión de CASRCE."""
    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        id_cuenta = request.session.get("id_cuenta")
        if not id_cuenta:
            return redirect("inicio_sesion")
        if not Cuenta.objects.filter(id_cuenta=id_cuenta).exists():
            request.session.flush()
            return redirect("inicio_sesion")
        return vista(request, *args, **kwargs)
    return envoltura
