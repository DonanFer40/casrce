from django.shortcuts import redirect
from django.http import JsonResponse
from django.urls import reverse

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

    @staticmethod
    def _url_modulo_anterior(request):
        ultima_url = request.session.get("casrce_ultima_url_autorizada")
        if (
            isinstance(ultima_url, str)
            and ultima_url.startswith("/")
            and not ultima_url.startswith("//")
            and ultima_url != request.path_info
        ):
            return ultima_url
        return reverse("panel_usuario")

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        tiene_sesion_usuario = bool(
            request.session.get("id_cuenta")
        )
        response = self.get_response(request)

        if tiene_sesion_usuario or request.session.get("id_cuenta"):
            response["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, private"
            )
            response["Pragma"] = "no-cache"
            response["Expires"] = "0"

        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        match = getattr(request, "resolver_match", None)
        nombre_url = getattr(match, "url_name", None)
        id_cuenta = request.session.get("id_cuenta")

        if (
            nombre_url == "inicio_sesion"
            and request.method in ("GET", "HEAD")
            and id_cuenta
        ):
            if Cuenta.objects.filter(id_cuenta=id_cuenta).exists():
                return redirect(self._url_modulo_anterior(request))
            request.session.flush()

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
            return redirect(self._url_modulo_anterior(request))

        request.session["rol"] = sorted(roles)
        request.tab_auth_required = True
        if request.method in ("GET", "HEAD"):
            request.session["casrce_ultima_url_autorizada"] = request.path_info
        return None
