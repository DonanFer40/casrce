from django.shortcuts import redirect
from django.http import JsonResponse, HttpResponseForbidden

from inicio_sesion.models import (
    Cuenta, DirectorGeneral, ControlEstudio, CoordinadorPNF, Docente, Estudiante
)
from permisos.mapa_permisos import (
    DEFAULT_MODULE_ROLES, URL_PERMISSIONS, PUBLIC_URL_NAMES,
    PUBLIC_OR_TOKEN_URL_NAMES,
)


def roles_reales_de_usuario(usuario):
    """Consulta los roles vigentes en BD; nunca confía en request.session['rol'].""" 
    roles = set()
    if DirectorGeneral.objects.filter(usuario=usuario).exists():
        roles.add("Director General")
    if ControlEstudio.objects.filter(usuario=usuario, activo=True).exists():
        roles.add("Control de Estudio")
    if CoordinadorPNF.objects.filter(usuario=usuario, activo=True).exists():
        roles.add("Coordinador PNF")
    if Docente.objects.filter(usuario=usuario, activo=True).exists():
        roles.add("Docente")
    if Estudiante.objects.filter(usuario=usuario).exists():
        roles.add("Estudiante")
    return roles


class SeguridadRolesMiddleware:
    """Impide acceder a endpoints internos sin sesión y rol autorizado."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        return self.get_response(request)

    def process_view(self, request, view_func, view_args, view_kwargs):
        match = getattr(request, "resolver_match", None)
        nombre_url = getattr(match, "url_name", None)

        if nombre_url in PUBLIC_URL_NAMES or nombre_url in PUBLIC_OR_TOKEN_URL_NAMES:
            return None

        modulo_python = getattr(view_func, "__module__", "")
        modulo = next(
            (nombre for nombre in DEFAULT_MODULE_ROLES
             if modulo_python.startswith(nombre + ".")),
            None,
        )
        if not modulo:
            return None

        id_cuenta = request.session.get("id_cuenta")
        if not id_cuenta:
            if request.headers.get("Accept", "").startswith("application/json") or request.content_type == "application/json":
                return JsonResponse({"success": False, "message": "Debes iniciar sesión."}, status=401)
            return redirect("inicio_sesion")

        try:
            cuenta = Cuenta.objects.select_related("id_usuario").get(id_cuenta=id_cuenta)
        except Cuenta.DoesNotExist:
            request.session.flush()
            return redirect("inicio_sesion")

        roles = roles_reales_de_usuario(cuenta.id_usuario)
        permitidos = URL_PERMISSIONS.get(nombre_url, DEFAULT_MODULE_ROLES[modulo])
        if not roles.intersection(permitidos):
            if request.headers.get("Accept", "").startswith("application/json"):
                return JsonResponse({"success": False, "message": "No tienes permisos para acceder a este recurso."}, status=403)
            return HttpResponseForbidden("No tienes permisos para acceder a este recurso.")

        request.session["rol"] = sorted(roles)
        return None
