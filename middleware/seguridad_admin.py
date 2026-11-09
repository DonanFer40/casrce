import logging

from django.conf import settings
from django.shortcuts import redirect
from django.http import HttpResponseForbidden

from inicio_sesion.services.seguridad_admin_service import (
    SESION_AUTORIZADO, SESION_USUARIO, obtener_verificacion_activa,
)

logger = logging.getLogger(__name__)


class SeguridadAdminMiddleware:
    """
    Protege /admin/ con la verificación de puerta + correo + TOTP ya existente.
    No sustituye el login de Django: exige además que el usuario autenticado sea
    exactamente el superusuario que completó la verificación.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        if not (path == "/admin" or path.startswith("/admin/")):
            return self.get_response(request)

        es_login = path.rstrip("/") == "/admin/login"
        try:
            from inicio_sesion.models import ConfiguracionSeguridadAdmin
            from inicio_sesion.services.seguridad_admin_service import obtener_superusuario_autorizado
            admin_configurado = obtener_superusuario_autorizado()
            totp_activado = ConfiguracionSeguridadAdmin.objects.filter(
                usuario=admin_configurado, totp_activo=True
            ).exists()
        except Exception:
            logger.exception("No se pudo comprobar el estado inicial de TOTP.")
            return HttpResponseForbidden(
                "No se puede validar la configuración administrativa."
            )

        if not totp_activado:
            if es_login:
                return self.get_response(request)
            if (
                request.user.is_authenticated
                and request.user.pk == admin_configurado.pk
                and request.user.is_active
                and request.user.is_staff
                and request.user.is_superuser
            ):
                return redirect("/seguridad-admin/configurar-totp/")
            return redirect("/admin/login/")

        # La página de login solo se muestra si ya se superó la puerta externa.
        autorizado = request.session.get(SESION_AUTORIZADO) is True
        usuario_id = request.session.get(SESION_USUARIO)

        try:
            verificacion = obtener_verificacion_activa(request)
        except Exception:
            logger.exception("No se pudo validar la sesión administrativa.")
            verificacion = None

        verificacion_valida = bool(
            autorizado
            and usuario_id
            and verificacion
            and verificacion.usuario_id == usuario_id
            and verificacion.etapa == "COMPLETADO"
            and verificacion.correo_verificado
            and verificacion.totp_verificado
            and verificacion.activo
        )

        if not verificacion_valida:
            request.session.pop(SESION_AUTORIZADO, None)
            request.session.pop(SESION_USUARIO, None)
            return redirect(getattr(settings, "CASRCE_ADMIN_LOGIN_URL", "/inicio_sesion/"))

        # En /admin/login/ Django aún no ha autenticado al usuario. Tras el login,
        # todas las páginas y operaciones exigen la misma identidad verificada.
        if not es_login:
            if not request.user.is_authenticated:
                return redirect("/admin/login/?next=/admin/")
            if (
                not request.user.is_active
                or not request.user.is_staff
                or not request.user.is_superuser
                or request.user.pk != usuario_id
            ):
                return HttpResponseForbidden(
                    "La cuenta autenticada no coincide con la verificación administrativa."
                )

        response = self.get_response(request)
        response["Cache-Control"] = "no-store, no-cache, must-revalidate, private"
        response["Pragma"] = "no-cache"
        return response
