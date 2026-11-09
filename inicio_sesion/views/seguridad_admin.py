
import logging
import base64
import qrcode

from io import BytesIO
from django.contrib.auth import logout
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.views.decorators.csrf import csrf_protect
from django.core.exceptions import ImproperlyConfigured
from django.shortcuts import render, redirect
from django.http import HttpResponseForbidden
from django.views.decorators.http import require_GET

from inicio_sesion.services.seguridad_admin_service import (
    iniciar_verificacion_admin,
    verificar_codigo_correo,
    verificar_codigo_totp,
    reenviar_codigo_correo,
    invalidar_verificacion_admin,
    obtener_verificacion_activa,
)

from inicio_sesion.services.seguridad_admin_service import (
    # Conserva aquí los imports que ya tienes.
    preparar_totp,
    confirmar_configuracion_totp,
    obtener_superusuario_autorizado,
)

logger = logging.getLogger(__name__)


def acceso_admin(request):
    verificacion = obtener_verificacion_activa(request)
    if not verificacion or verificacion.etapa not in {"CORREO", "TOTP"}:
        return redirect("inicio_sesion")
    return render(
        request,
        "Security/acceso_admin.html",
        {"etapa": verificacion.etapa},
    )


# ==========================================================
# RESPUESTAS JSON
# ==========================================================

def respuesta(mensaje, exito=False, estado=200, **datos):

    return JsonResponse(
        {
            "success": exito,
            "message": mensaje,
            **datos,
        },
        status=estado
    )


def obtener_estado_error(mensaje):

    mensaje = str(mensaje).lower()

    if "bloqueado" in mensaje or "bloqueada" in mensaje:
        return 423

    if "esperar" in mensaje:
        return 429

    if (
        "sesión" in mensaje
        or "verificación activa" in mensaje
        or "verificación ya no está disponible" in mensaje
    ):
        return 401

    return 400


# ==========================================================
# 1. INICIAR ACCESO ADMINISTRATIVO
# ==========================================================

@csrf_protect
@require_POST
def iniciar_acceso_admin(request):

    usuario = request.POST.get(
        "usuario",
        ""
    ).strip()

    contrasenia = request.POST.get(
        "contrasenia",
        ""
    )

    if not usuario or not contrasenia:

        return respuesta(
            "Debes introducir el usuario y la contraseña.",
            False,
            400
        )

    try:

        exito, mensaje = iniciar_verificacion_admin(
            request,
            usuario,
            contrasenia
        )

    except ImproperlyConfigured:

        logger.exception(
            "La configuración de seguridad administrativa está incompleta."
        )

        return respuesta(
            "La seguridad administrativa no está configurada correctamente.",
            False,
            503
        )

    except Exception:

        logger.exception(
            "Error iniciando la verificación administrativa."
        )

        return respuesta(
            "No fue posible iniciar el proceso de seguridad.",
            False,
            503
        )

    if not exito:

        estado = (
            403
            if "Primero debes configurar" in mensaje
            else 401
        )

        return respuesta(
            mensaje,
            False,
            estado
        )

    return respuesta(
        mensaje,
        True,
        etapa="CORREO",
        expiracion_minutos=5
    )


# ==========================================================
# 2. VERIFICAR CÓDIGO DE CORREO
# ==========================================================

@csrf_protect
@require_POST
def verificar_codigo_correo_admin(request):

    codigo = request.POST.get(
        "codigo",
        ""
    ).strip()

    if not codigo:

        return respuesta(
            "Debes introducir el código recibido por correo.",
            False,
            400
        )

    try:

        exito, mensaje = verificar_codigo_correo(
            request,
            codigo
        )

    except Exception:

        logger.exception(
            "Error durante la verificación del código de correo."
        )

        return respuesta(
            "Ocurrió un error al verificar el código.",
            False,
            500
        )

    if not exito:

        return respuesta(
            mensaje,
            False,
            obtener_estado_error(mensaje)
        )

    return respuesta(
        mensaje,
        True,
        etapa="TOTP"
    )


# ==========================================================
# 3. VERIFICAR CÓDIGO TOTP
# ==========================================================

@csrf_protect
@require_POST
def verificar_totp_admin(request):

    codigo = request.POST.get(
        "codigo",
        ""
    ).strip()

    if not codigo:

        return respuesta(
            "Debes introducir el código de tu aplicación autenticadora.",
            False,
            400
        )

    try:

        exito, mensaje = verificar_codigo_totp(
            request,
            codigo
        )

    except Exception:

        logger.exception(
            "Error durante la verificación TOTP administrativa."
        )

        return respuesta(
            "Ocurrió un error interno durante la verificación.",
            False,
            500
        )

    if not exito:

        return respuesta(
            mensaje,
            False,
            obtener_estado_error(mensaje)
        )

    return respuesta(
        mensaje,
        True,
        siguiente="/admin/login/?next=/admin/"
    )


# ==========================================================
# 4. REENVIAR CÓDIGO DE CORREO
# ==========================================================

@csrf_protect
@require_POST
def reenviar_codigo_admin(request):

    try:

        exito, mensaje = reenviar_codigo_correo(
            request
        )

    except Exception:

        logger.exception(
            "Error durante el reenvío del código administrativo."
        )

        return respuesta(
            "No fue posible enviar el código. Inténtalo nuevamente.",
            False,
            503
        )

    if not exito:

        return respuesta(
            mensaje,
            False,
            obtener_estado_error(mensaje)
        )

    return respuesta(
        mensaje,
        True
    )


# ==========================================================
# 5. CANCELAR ACCESO ADMINISTRATIVO
# ==========================================================

@csrf_protect
@require_POST
def cancelar_acceso_admin(request):

    try:

        invalidar_verificacion_admin(
            request
        )

    except Exception:

        logger.exception(
            "Error invalidando la verificación administrativa."
        )

        return respuesta(
            "No fue posible cancelar correctamente la verificación.",
            False,
            500
        )

    return respuesta(
        "El proceso de autenticación ha sido cancelado.",
        True
    )

# =========================================================
# CONFIGURACIÓN INICIAL DE GOOGLE AUTHENTICATOR
# =========================================================

def es_superusuario_autorizado(request):

    if not request.user.is_authenticated:
        return False

    if not (
        request.user.is_active
        and request.user.is_staff
        and request.user.is_superuser
    ):
        return False

    try:
        usuario_autorizado = obtener_superusuario_autorizado()

    except Exception:
        logger.exception(
            "No fue posible identificar el superusuario autorizado."
        )
        return False

    return request.user.pk == usuario_autorizado.pk


def generar_qr_totp(uri):

    codigo_qr = qrcode.make(uri)

    buffer = BytesIO()

    codigo_qr.save(buffer, format="PNG")

    imagen_base64 = base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")

    return imagen_base64


@require_GET
def configurar_totp_admin(request):

    if not es_superusuario_autorizado(request):

        return HttpResponseForbidden(
            "No tienes autorización para configurar la seguridad administrativa."
        )

    try:

        uri = preparar_totp()

        qr_base64 = generar_qr_totp(uri)

        return render(
            request,
            "Security/configurar_totp_admin.html",
            {
                "qr_base64": qr_base64,
            }
        )

    except ValueError as error:

        return render(
            request,
            "Security/configurar_totp_admin.html",
            {
                "error": str(error),
                "totp_configurado": True,
            },
            status=409
        )

    except Exception:

        logger.exception(
            "Error preparando la configuración TOTP administrativa."
        )

        return render(
            request,
            "Security/configurar_totp_admin.html",
            {
                "error": (
                    "No fue posible preparar la configuración "
                    "de Google Authenticator."
                )
            },
            status=503
        )


@csrf_protect
@require_POST
def confirmar_totp_admin(request):

    if not es_superusuario_autorizado(request):

        return respuesta(
            "No tienes autorización para realizar esta operación.",
            False,
            403
        )

    codigo = request.POST.get("codigo", "").strip()

    if not codigo:

        return respuesta(
            "Debes introducir el código de Google Authenticator.",
            False,
            400
        )

    try:

        confirmado = confirmar_configuracion_totp(codigo)

        if not confirmado:

            return respuesta(
                "El código es incorrecto o la configuración "
                "ya no está disponible.",
                False,
                400
            )

        logout(request)
        return respuesta(
            "Google Authenticator se ha configurado correctamente.",
            True,
            etapa="COMPLETADO"
        )

    except Exception:

        logger.exception(
            "Error confirmando la configuración TOTP administrativa."
        )

        return respuesta(
            "Ocurrió un error al confirmar la configuración.",
            False,
            503
        )