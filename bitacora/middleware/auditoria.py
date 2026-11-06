import logging

from django.urls import resolve, Resolver404

from bitacora.services.registrar_accion import registrar_accion

logger = logging.getLogger(__name__)


class AuditoriaOperacionesMiddleware:
    """
    Registra solicitudes POST autenticadas después de que la vista responde.
    No registra visitas GET ni captura los valores enviados en formularios.
    """

    RUTAS_EXCLUIDAS = {
        "inicio_sesion",
        "cerrar_sesion",
        "bitacora_acciones",
        "detalle_accion",
    }

    MODULOS = {
        "notas_academicas": ("ACADEMICO", "Notas académicas"),
        "gestion_institucional": ("INSTITUCIONAL", "Gestión institucional"),
        "documentos": ("DOCUMENTOS", "Documentos"),
        "inicio_sesion": ("USUARIOS", "Gestión de usuarios"),
    }

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        if request.method != "POST" or not request.session.get("id_cuenta"):
            return response

        try:
            match = getattr(request, "resolver_match", None)
            if match is None:
                try:
                    match = resolve(request.path_info)
                except Resolver404:
                    return response

            nombre_ruta = match.url_name or match.view_name or "operacion"
            if nombre_ruta in self.RUTAS_EXCLUIDAS or nombre_ruta.startswith("admin:"):
                return response

            # Las operaciones de autenticación ya se registran explícitamente.
            if nombre_ruta in {"iniciar_sesion", "autenticar_usuario", "cerrar_sesion"}:
                return response

            namespace = match.namespace or ""
            modulo_key = namespace or request.path_info.strip("/").split("/")[0]
            modulo_vista = getattr(match.func, "__module__", "")
            for app_key in self.MODULOS:
                if modulo_vista.startswith(app_key + "."):
                    modulo_key = app_key
                    break
            categoria, modulo = self.MODULOS.get(
                modulo_key,
                ("OTRO", modulo_key.replace("_", " ").title() or "Sistema"),
            )

            if response.status_code >= 500:
                resultado, nivel = "FALLIDO", "CRITICO"
            elif response.status_code >= 400:
                resultado, nivel = "RECHAZADO", "ADVERTENCIA"
            elif 300 <= response.status_code < 400:
                resultado, nivel = "EXITOSO", "INFO"
            else:
                # Una respuesta 200 puede contener un formulario con errores.
                resultado, nivel = "PENDIENTE", "INFO"

            accion = nombre_ruta.replace("_", " ").replace("-", " ").strip().capitalize()
            descripcion = (
                f"Se recibió una solicitud de modificación mediante la operación "
                f"'{accion}'. Código de respuesta: {response.status_code}."
            )

            registrar_accion(
                request,
                categoria=categoria,
                modulo=modulo,
                accion=accion[:120],
                descripcion=descripcion,
                resultado=resultado,
                nivel=nivel,
                detalles={
                    "ruta_resuelta": match.view_name or nombre_ruta,
                    "codigo_respuesta": response.status_code,
                },
            )
        except Exception:
            logger.exception("No se pudo registrar una operación en la bitácora.")

        return response
